# src/middleware/ratelimit.py
from __future__ import annotations
import os, time, asyncio
from typing import Callable, Awaitable, Deque, Dict, Tuple
from collections import defaultdict, deque

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

Key = Tuple[str, str]  # (id, route)

RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
RATE_LIMIT_BURST    = int(os.getenv("RATE_LIMIT_BURST", "60"))
WINDOW_SECS         = 60.0
MAX_KEYS            = int(os.getenv("RATE_LIMIT_MAX_KEYS", "10000"))  # safety cap
TRUST_PROXY         = os.getenv("TRUST_PROXY", "false").lower() == "true"

def get_client_id(req: Request) -> str:
    if TRUST_PROXY:
        xf = req.headers.get("x-forwarded-for")
        if xf:
            return xf.split(",")[0].strip()
        xr = req.headers.get("x-real-ip")
        if xr:
            return xr.strip()
    return req.headers.get("x-user-id") or (req.client.host if req.client else "unknown")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.bucket: Dict[Key, Deque[float]] = defaultdict(deque)
        self.locks: Dict[Key, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._gc_lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi", "/static")):
            return await call_next(request)

        uid = get_client_id(request)
        key: Key = (uid, path)
        now = time.time()
        window_start = now - WINDOW_SECS

        # soft cap to avoid RAM blowups
        if len(self.bucket) > MAX_KEYS and key not in self.bucket:
            return JSONResponse(
                {"ok": False, "error": {"code": "RATE_CAP_KEYS", "message": "Server busy"}},
                status_code=503
            )

        async with self.locks[key]:
            q = self.bucket[key]
            # purge old
            while q and q[0] < window_start:
                q.popleft()

            remaining = max(RATE_LIMIT_PER_MIN - len(q), 0)

            if remaining <= 0 and len(q) >= RATE_LIMIT_BURST:
                retry = max(0, int(round(q[0] + WINDOW_SECS - now)))
                return JSONResponse(
                    {"ok": False, "error": {
                        "code": "RATE_LIMIT",
                        "message": "Too many requests",
                        "retry_after_sec": retry,
                        "limit": RATE_LIMIT_PER_MIN,
                        "window_sec": int(WINDOW_SECS)
                    }},
                    status_code=429,
                    headers={
                        "Retry-After": str(retry),
                        "X-RateLimit-Limit": str(RATE_LIMIT_PER_MIN),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(q[0] + WINDOW_SECS))
                    }
                )

            q.append(now)
            headers = {
                "X-RateLimit-Limit": str(RATE_LIMIT_PER_MIN),
                "X-RateLimit-Remaining": str(max(remaining - 1, 0)),
                "X-RateLimit-Reset": str(int(q[0] + WINDOW_SECS)) if q else str(int(now + WINDOW_SECS)),
            }

        resp = await call_next(request)
        for k, v in headers.items():
            resp.headers[k] = v
        # opportunistic GC
        await self._maybe_gc(window_start)
        return resp

    async def _maybe_gc(self, window_start: float):
        # cheap periodic sweep
        if getattr(self, "_last_gc", 0) + 15 > time.time():
            return
        async with self._gc_lock:
            self._last_gc = time.time()
            dead = []
            for k, q in self.bucket.items():
                while q and q[0] < window_start:
                    q.popleft()
                if not q:
                    dead.append(k)
            for k in dead:
                self.bucket.pop(k, None)
                self.locks.pop(k, None)
