# src/middleware/auth.py
from __future__ import annotations

from typing import Callable, Awaitable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.db.session import get_session_ctx

OPEN_PATHS = [
    r"^/health$",
    r"^/openapi\.json$",
    r"^/docs($|/)",
    r"^/redoc$",
    r"^/static($|/)",
]

def is_open(path: str) -> bool:
    import re
    return any(re.match(p, path) for p in OPEN_PATHS)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if is_open(request.url.path):
            return await call_next(request)

        user_id = request.headers.get("x-user-id")
        if not user_id:
            return JSONResponse({"detail": "x-user-id missing"}, status_code=401)

        async with get_session_ctx() as db:
            assert isinstance(db, AsyncSession)
            row = await db.execute(
                text("SELECT 1 FROM users WHERE id=:u LIMIT 1"),
                {"u": user_id},
            )
            if not row.scalar():
                return JSONResponse({"detail": "user_id not found"}, status_code=401)

        # ✅ REQUIRED FIX
        request.state.user_id = user_id

        return await call_next(request)

