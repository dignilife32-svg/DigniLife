# src/auth/security.py
from __future__ import annotations

import os
import hmac
import json
import time
from base64 import b64encode, b64decode
from hashlib import sha256
from typing import Literal, Optional

from fastapi import Header, HTTPException, Request, status, Depends
from sqlalchemy import text

from src.db.session import get_session

# === Config ==================================================================
SECRET: bytes = os.getenv("APP_SECRET", "dignilife-dev-secret").encode()
ADMIN_KEY: str = os.getenv("ADMIN_KEY", "let-me-in")
TOKEN_TTL: int = int(os.getenv("TOKEN_TTL_SECONDS", str(60 * 60)))  # 1h default
COOKIE_NAME = "dl_token"

Role = Literal["user", "admin"]


# === Tiny token (same API as before) =========================================
def b64(data: bytes) -> str:
    return b64encode(data).decode().rstrip("=")


def b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return b64decode(s + pad)

def sign(data: bytes) -> str:
    return b64(hmac.new(SECRET, data, sha256).digest())

def tiny_token(payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":")).encode()
    ts = int(time.time())
    msg = b"%d." % ts + body
    sig = sign(msg)
    return f"{b64(body)}.{ts}.{sig}"

# 🔧 Backward-compat alias for old imports
make_token = tiny_token

# (optional) export list
__all__ = [
    "make_token", "tiny_token", "verify_token",
    "require_user_authorization", "get_current_user",
    "Role", "COOKIE_NAME", "ADMIN_KEY", "TOKEN_TTL",
    "b64", "b64d",
]

def verify_token(token: str) -> dict:
    try:
        body_b64, ts_str, sig = token.split(".")
        body = b64d(body_b64)
        ts = int(ts_str)
        if time.time() - ts > TOKEN_TTL:
            raise ValueError("token expired")
        msg = b"%d." % ts + body
        if not hmac.compare_digest(sign(msg), sig):
            raise ValueError("bad signature")
        return json.loads(body.decode())
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e

# === Dependencies =============================================================
def require_user_authorization(authorization: Optional[str] = Header(default=None)) -> dict:
    """
    Accepts: Authorization: Bearer <token>
    Returns decoded payload (dict).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        scheme, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid authorization header")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid auth scheme")
    return verify_token(token)

def require_user_cookie(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="missing cookie token")
    return verify_token(token)

# === Simple x-user-id based identity check (for tests / AI-assisted routes) ==
async def get_current_user(
    x_user_id: Optional[str] = Header(default=None),
    db=Depends(get_session),
) -> dict:
    """
    If x-user-id header is provided we look it up in DB (tests use this).
    Otherwise the route should depend on `require_user_authorization` or
    `require_user_cookie` separately.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="missing x-user-id")

    row = await db.execute(text("SELECT id, email FROM users WHERE id = :uid LIMIT 1"), {"uid": x_user_id})
    user = row.first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return {"id": user.id, "email": user.email}

# src/auth/security.py

async def require_admin():
    """Temporary bypass until real admin guard implemented."""
    # later you can validate token/session here
    return True
