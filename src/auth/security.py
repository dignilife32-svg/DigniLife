# src/auth/security.py
import os, hmac, json, time, base64, hashlib
from typing import Literal, Optional, Dict
from fastapi import Header, HTTPException, status, Depends
from fastapi import Request
# ── Config ─────────────────────────────────────────────────────────────────────
SECRET = (os.getenv("APP_SECRET") or "dignilife-dev-secret").encode()
ADMIN_KEY = os.getenv("ADMIN_KEY") or "let-me-in"       # change in .env for prod
TOKEN_TTL = int(os.getenv("TOKEN_TTL_SECONDS") or 86400)  # 24h

Role = Literal["user", "admin"]

# ── Tiny token (b64(payload).b64(sig)) ─────────────────────────────────────────
def _sign(data: bytes) -> str:
    sig = hmac.new(SECRET, data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")

def _b64(d: bytes) -> str:
    return base64.urlsafe_b64encode(d).decode().rstrip("=")

def _b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def make_token(user_id: str, role: Role) -> str:
    payload = {"sub": user_id, "role": role, "iat": int(time.time())}
    data = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = _sign(data.encode())
    return f"{data}.{sig}"

def verify_token(token: str) -> Dict:
    try:
        data_b64, sig = token.split(".", 1)
        if _sign(data_b64.encode()) != sig:
            raise ValueError("bad signature")
        payload = json.loads(_b64d(data_b64))
        if int(time.time()) - int(payload.get("iat", 0)) > TOKEN_TTL:
            raise ValueError("token expired")
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# ── Dependencies ───────────────────────────────────────────────────────────────
def require_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    payload = verify_token(authorization.split(" ", 1)[1])
    return payload  # {sub, role, iat}

def require_admin(payload=Depends(require_user)):
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload

COOKIE_NAME = "dl_token"

def token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)

def require_user_cookie(request: Request):
    token = token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing cookie token")
    return verify_token(token)
