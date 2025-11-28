#src/middleware/ratelimit_radis.py
"""
ratelimit_redis.py

FastAPI/Starlette middleware that enforces:
 - per-user rate limit (sliding window)
 - per-route (path+ip) rate limit (sliding window)

Dependencies:
  pip install fastapi "uvicorn[standard]" redis[asyncio]

Usage:
  from fastapi import FastAPI
  from ratelimit_redis import RedisRateLimitMiddleware

  app = FastAPI()
  app.add_middleware(
      RedisRateLimitMiddleware,
      redis_url="redis://localhost:6379/0",
      prefix="dignilife:rate",
      user_limit=60,
      route_limit=120,
      window_seconds=60,
      fail_open=True,
      header_user_id="X-User-Id",   # optional header for user id
  )
"""

import os
import logging
import asyncio
from typing import Callable, List, Tuple, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp
from src.middleware import  ratelimit

import redis.asyncio as aioredis  # redis-py async client

logger = logging.getLogger("ratelimit")
logger.setLevel(logging.INFO)


LUA_SCRIPT = r"""
-- KEYS[1] = user_key
-- KEYS[2] = route_key
-- ARGV[1] = user_limit
-- ARGV[2] = route_limit
-- ARGV[3] = window_seconds

local nowdata = redis.call('TIME')           -- returns {seconds, microseconds}
local now = tonumber(nowdata[1])             -- we use seconds resolution
local window = tonumber(ARGV[3])

local function slide(key, limit)
  local cutoff = now - window
  -- purge old entries
  redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
  local cnt = redis.call('ZCARD', key)
  if cnt >= tonumber(limit) then
    -- find oldest score
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')[2]
    if oldest == false or oldest == nil then
      return {0, window, cnt}
    end
    local retry = window - (now - tonumber(oldest))
    if retry < 0 then retry = 0 end
    return {0, retry, cnt}
  end
  -- add this event (use unique member)
  local member = tostring(now) .. ":" .. tostring(math.random(1000000))
  redis.call('ZADD', key, now, member)
  redis.call('EXPIRE', key, window + 2)
  return {1, 0, cnt + 1}
end

local ures = slide(KEYS[1], ARGV[1])
local rres = slide(KEYS[2], ARGV[2])

local uok, uretry, ucount = ures[1], ures[2], ures[3]
local rok, rretry, rcount = rres[1], rres[2], rres[3]

if uok == 1 and rok == 1 then
  return {1, 0, tonumber(ARGV[1]) - ucount, tonumber(ARGV[2]) - rcount}
end

local retry = uretry
if rretry > retry then retry = rretry end
return {0, retry, tonumber(ARGV[1]) - ucount, tonumber(ARGV[2]) - rcount}
"""


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        redis_url: str = None,
        prefix: str = "ratelimit",
        user_limit: int = 60,
        route_limit: int = 120,
        window_seconds: int = 60,
        fail_open: bool = True,
        header_user_id: str = "X-User-Id",
        redis_namespace_db: int = 0,
    ):
        super().__init__(app)
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.user_limit = int(os.getenv("USER_RATE_LIMIT", str(user_limit)))
        self.route_limit = int(os.getenv("ROUTE_RATE_LIMIT", str(route_limit)))
        self.window = int(os.getenv("RATE_WINDOW_SEC", str(window_seconds)))
        self.fail_open = bool(fail_open)
        self.header_user_id = header_user_id
        self.redis_namespace_db = redis_namespace_db

        self.redis: Optional[aioredis.Redis] = None
        self.lua_sha: Optional[str] = None

        # attach the script source for eval
        self._lua = LUA_SCRIPT

        logger.info("RateLimit middleware initialized: %s", {
            "redis_url": self.redis_url,
            "prefix": self.prefix,
            "user_limit": self.user_limit,
            "route_limit": self.route_limit,
            "window": self.window,
            "fail_open": self.fail_open,
        })

    async def _ensure_redis(self):
        if self.redis is None:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            # Try to load script (cached), but if not available we'll EVAL at call time.
            try:
                self.lua_sha = await self.redis.script_load(self._lua)
            except Exception as e:
                logger.warning("Could not preload Lua script: %s", e)
                self.lua_sha = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ensure client exists
        await self._ensure_redis()

        # derive keys
        ip = request.client.host if request.client is not None else "unknown"
        # prefer real user id from header (integrate with your auth in prod)
        user_id = request.headers.get(self.header_user_id) or "anon"

        # route bucket includes path + ip to reduce shared noise
        route_ident = f"{request.url.path}:{ip}"

        user_key = f"{self.prefix}:user:{user_id}"
        route_key = f"{self.prefix}:route:{route_ident}"

        keys = [user_key, route_key]
        args = [str(self.user_limit), str(self.route_limit), str(self.window)]

        # call lua atomically
        try:
            # Prefer EVALSHA if loaded; fallback to EVAL
            if self.lua_sha:
                # `evalsha` usage: script_sha, numkeys, *keys_and_args
                res = await self.redis.evalsha(self.lua_sha, len(keys), *(keys + args))
            else:
                res = await self.redis.eval(self._lua, len(keys), *(keys + args))
            # res expected: [ok(1/0), retry_seconds, remain_user, remain_route]
            # may come as strings due to decode_responses=True
            ok = int(res[0])
            retry_after = float(res[1])
            remain_user = int(res[2])
            remain_route = int(res[3])
        except Exception as e:
            logger.exception("Redis eval error: %s", e)
            if self.fail_open:
                # Allow request through but mark header
                resp = await call_next(request)
                resp.headers["X-RateLimit-Bypass"] = "redis_down"
                return resp
            else:
                return JSONResponse(
                    {"detail": "rate limiter unavailable"},
                    status_code=503
                )

        # If not ok => rate limited
        if ok == 0:
            # choose 429, include Retry-After in header & body
            
            retry_int = int(retry_after if retry_after and retry_after > 0 else 1)
            body = {
                "detail": "rate limit exceeded",
                "retry_after_seconds": retry_int,
            }
            
            headers = {"Retry-After": str(retry_int)}

            return JSONResponse(body, status_code=429, headers=headers)

        # allowed -> call next and attach headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-User"] = str(self.user_limit)
        response.headers["X-RateLimit-Remaining-User"] = str(remain_user)
        response.headers["X-RateLimit-Limit-Route"] = str(self.route_limit)
        response.headers["X-RateLimit-Remaining-Route"] = str(remain_route)
        return response

    async def shutdown(self):
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass
            self.redis = None

    ##########################################################################
    # Utility functions (optional): inspect / clear rate keys during dev
    ##########################################################################
    async def scan_rate_keys(self, match: str = None, count: int = 100) -> List[str]:
        await self._ensure_redis()
        pattern = f"{self.prefix}:*"
        if match:
            pattern = match
        cur = "0"
        keys = []
        try:
            while True:
                cur, found = await self.redis.scan(cur, pattern=pattern, count=count)
                keys.extend(found)
                if cur == "0":
                    break
        except Exception as e:
            logger.warning("scan error: %s", e)
        return keys

    async def flush_rate_keys(self, match: str = None):
        await self._ensure_redis()
        pattern = f"{self.prefix}:*"
        if match:
            pattern = match
        # Warning: this is destructive
        keys = await self.scan_rate_keys(pattern)
        if keys:
            try:
                await self.redis.delete(*keys)
            except Exception as e:
                logger.warning("delete keys error: %s", e)
        return len(keys)

