#src/utils/ai_guard_helpers.py
from __future__ import annotations
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from functools import wraps

def requires_confidence(min_conf: float = 0.6, fallback_path: str | None = "/fallback") -> Callable:
    """
    Use on FastAPI handlers to enforce a minimum confidence.
    If below threshold -> raises HTTP 202 with fallback info (or redirects logic if you prefer).
    """
    def decorator(fn: Callable[[Request], Awaitable]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # find Request in args/kwargs
            req: Request | None = None
            for a in args:
                if hasattr(a, "json") and hasattr(a, "headers"):
                    req = a; break
            if req is None:
                req = kwargs.get("request")

            signals = getattr(req.state, "ai_signals", {}) if req else {}
            conf = float(signals.get("confidence", 1.0))

            if conf < min_conf:
                # 202 Accepted + guidance (fallback cue)
                from fastapi.responses import JSONResponse
                payload = {
                    "ok": False,
                    "message": "Routed to fallback/admin review",
                    "fallback": fallback_path,
                    "signals": signals,
                }
                return JSONResponse(payload, status_code=202)
            return await fn(*args, **kwargs)
        return wrapper
    return decorator
