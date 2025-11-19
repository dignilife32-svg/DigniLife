# src/middleware/authsig.py
from __future__ import annotations

import os
import hmac
import json
import time
import hashlib
from typing import Callable, Iterable, Optional

from fastapi import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

# --- optional redis (async) ---------------------------------------------------
try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # redis not installed in some envs
    redis = None  # type: ignore

# --- optional prometheus counters --------------------------------------------
try:
    from prometheus_client import Counter  # type: ignore

    SIG_FAILURES = Counter(
        "authsig_failures_total",
        "HMAC signature failures",
        ["reason"],
    )
    REPLAY_BLOCKS = Counter(
        "authsig_replay_blocks_total",
        "Requests blocked due to replay detection",
    )
except Exception:
    # no-op fallbacks (so importers won't break)
    class _Noop:
        def labels(self, *_, **__):  # for SIG_FAILURES.labels(...).inc()
            return self

        def inc(self, *_a, **_kw):
            pass

    SIG_FAILURES = _Noop()
    REPLAY_BLOCKS = _Noop()

# --- helpers ------------------------------------------------------------------
def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_sha256_hex(secret: str, message: str) -> str:
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


class AuthSignatureMiddleware(BaseHTTPMiddleware):
    """
    HMAC SHA256 middleware (anti-tamper + anti-replay).

    Required headers (case-insensitive):
      x-dl-key, x-dl-nonce, x-dl-timestamp, x-dl-signature

    Canonical string:
      "{METHOD}\\n{PATH}\\n{timestamp}\\n{nonce}\\n{sha256(body)}"

    Server secret is loaded from env DL_SECRET (required).
    Optional allowlist of keys via DL_KEY (single) or DL_KEYS (CSV).
    Redis (async) is used for replay protection if DL_REDIS_URL is provided.
    """

    def __init__(
        self,
        app,
        *,
        redis_url: Optional[str] = None,
        replay_ttl_sec: int = 60,
        clock_skew_sec: int = 60,
        allowed_methods: Iterable[str] = ("POST", "PUT", "PATCH", "DELETE"),
        skip_paths: Iterable[str] = ("/health", "/metrics", "/docs", "/openapi.json"),
        key_prefix: str = "dignilife:replay:",
    ):
        super().__init__(app)

        # config
        self.replay_ttl = int(replay_ttl_sec)
        self.clock_skew = int(clock_skew_sec)
        self.allowed_methods = {m.upper() for m in allowed_methods}
        self.skip_paths = set(skip_paths)
        self.key_prefix = key_prefix

        # secrets & allowed key ids
        self.secret = os.getenv("DL_SECRET", "")
        if not self.secret:
            raise RuntimeError("DL_SECRET env var is required for AuthSignatureMiddleware")

        keys_single = os.getenv("DL_KEY", "").strip()
        keys_csv = os.getenv("DL_KEYS", "").strip()
        self.allowed_key_ids = set()
        if keys_single:
            self.allowed_key_ids.add(keys_single)
        if keys_csv:
            self.allowed_key_ids.update(k.strip() for k in keys_csv.split(",") if k.strip())

        # redis
        self._redis = None
        self.redis_url = redis_url or os.getenv("DL_REDIS_URL", "redis://localhost:6379/0")

    # -- redis lazy init -------------------------------------------------------
    async def _lazy_redis(self):
        if self._redis is None and redis is not None and self.redis_url:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    # -- utilities -------------------------------------------------------------
    @staticmethod
    def _read_headers(req: Request) -> dict:
        h = req.headers
        return {
            "key_id": h.get("x-dl-key"),
            "nonce": h.get("x-dl-nonce"),
            "ts": h.get("x-dl-timestamp"),
            "sig": h.get("x-dl-signature"),
        }

    @staticmethod
    def _is_public(method: str, path: str) -> bool:
        # default: protect non-GET by signature
        return method.upper() == "GET"

    async def _is_replay(self, key_id: str, nonce: str) -> bool:
        r = await self._lazy_redis()
        if not r:
            return False  # no redis => cannot check replay
        cache_key = f"{self.key_prefix}{key_id}:{nonce}"
        # True when created; False when existed
        created = await r.set(cache_key, "1", ex=self.replay_ttl, nx=True)
        if not created:
            # already exists -> replay
            REPLAY_BLOCKS.inc()
            return True
        return False

    # -- middleware core -------------------------------------------------------
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        method = request.method.upper()
        path = request.url.path

        # quick skip for public paths
        if path in self.skip_paths:
            return await call_next(request)

        # only enforce for write-intent by default
        if self._is_public(method, path) and method not in self.allowed_methods:
            return await call_next(request)

        # Basic presence checks
        headers = self._read_headers(request)
        key_id, nonce, ts_raw, sig = headers["key_id"], headers["nonce"], headers["ts"], headers["sig"]
        if not (key_id and nonce and ts_raw and sig):
            SIG_FAILURES.labels("missing_header").inc()
            return JSONResponse({"detail": "missing auth headers"}, status_code=401)

        # key allowlist (if configured)
        if self.allowed_key_ids and key_id not in self.allowed_key_ids:
            SIG_FAILURES.labels("unknown_key").inc()
            return JSONResponse({"detail": "unknown api key"}, status_code=401)

        # timestamp sanity
        try:
            ts = int(ts_raw)
        except (TypeError, ValueError):
            SIG_FAILURES.labels("bad_timestamp").inc()
            return JSONResponse({"detail": "invalid timestamp"}, status_code=401)

        now = int(time.time())
        if abs(now - ts) > self.clock_skew:
            SIG_FAILURES.labels("expired").inc()
            return JSONResponse({"detail": "timestamp outside allowed window"}, status_code=401)

        # body hash
        body_bytes = await request.body()
        body_hash = sha256_hex(body_bytes)

        # expected signature
        canonical = f"{method}\n{path}\n{ts}\n{nonce}\n{body_hash}"
        expected_sig = hmac_sha256_hex(self.secret, canonical).lower()

        if not hmac.compare_digest(str(sig).lower(), expected_sig):
            SIG_FAILURES.labels("invalid_signature").inc()
            return JSONResponse({"detail": "invalid signature"}, status_code=401)

        # replay protection
        if await self._is_replay(key_id, nonce):
            return JSONResponse({"detail": "replay detected"}, status_code=401)

        # forward request (rebuild body because we consumed it)
        async def receive_gen():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        # starlette Request allows overriding the receive callable
        request._receive = receive_gen  # type: ignore[attr-defined]
        return await call_next(request)

    # optional graceful shutdown
    async def shutdown(self):
        try:
            if self._redis:
                await self._redis.aclose()
        except Exception:
            pass
        self._redis = None
