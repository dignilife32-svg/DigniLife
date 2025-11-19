import json
import hashlib
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter
import redis.asyncio as redis

# Metrics
IDEMPOTENT_HITS = Counter("idempotent_hits_total", "Number of idempotent requests")
IDEMPOTENT_REPLAYS = Counter("idempotent_replays_total", "Number of replayed idempotent requests")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure idempotent POST requests using Redis.
    If client sends same Idempotency-Key + same payload + same user, cached response is reused.
    """

    def __init__(self, app, redis_url: str = "redis://localhost:6379", ttl: int = 86400):
        super().__init__(app)
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Apply only to mutating methods
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        user = request.headers.get("x-user-id", "anonymous")

        if not key:
            # Proceed as normal if no idempotency key
            return await call_next(request)

        # Compute hash to uniquely identify this request
        body = await request.body()
        hash_val = hashlib.sha256(body).hexdigest()
        cache_key = f"idemp:{user}:{key}:{hash_val}"

        # Lazy-init Redis
        if not self.redis:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)

        # Try to find cached response
        cached = await self.redis.get(cache_key)
        if cached:
            IDEMPOTENT_REPLAYS.inc()
            cached_data = json.loads(cached)
            return JSONResponse(
                content=cached_data["body"],
                status_code=cached_data["status"],
                headers=cached_data.get("headers", {}),
            )

        # Lock key (prevent race)
        lock_key = f"{cache_key}:lock"
        got_lock = await self.redis.set(lock_key, "1", ex=30, nx=True)
        if not got_lock:
            # Another request already processing
            return JSONResponse(
                {"detail": "Duplicate request processing"},
                status_code=409
            )

        # Process normally
        response = await call_next(request)

        # Cache only success (2xx) responses
        if 200 <= response.status_code < 300:
            IDEMPOTENT_HITS.inc()
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            data = {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": json.loads(body_bytes.decode()) if body_bytes else {},
            }
            await self.redis.set(cache_key, json.dumps(data), ex=self.ttl)

            # release lock
            await self.redis.delete(lock_key)

            # re-create response since body_iterator was consumed
            return JSONResponse(content=data["body"], status_code=data["status"], headers=data["headers"])

        else:
            await self.redis.delete(lock_key)
            return response

    async def shutdown(self):
        if self.redis:
            await self.redis.aclose()
            self.redis = None
