# src/safety/facegate.py
from __future__ import annotations
from typing import Optional, Tuple
from datetime import datetime, timezone
import os, hmac, hashlib, time
from collections import defaultdict, deque

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src.ai.face import get_provider

router = APIRouter(tags=["safety"])

# ---------------- Config ----------------
MATCH_TH = float(os.getenv("FACE_MATCH_TH", "0.90"))
LIVE_TH  = float(os.getenv("FACE_LIVENESS_TH", "0.85"))
NONCE_TTL_SEC = int(os.getenv("FACE_NONCE_TTL", "60"))
RATE_PER_MIN = int(os.getenv("FACE_RATE_PER_MIN", "5"))
DAY_CAP_PER_DEVICE = int(os.getenv("FACE_DAY_CAP_PER_DEVICE", "20"))
HMAC_SECRET = os.getenv("FACE_HMAC_SECRET", "change-me-in-prod").encode()

# ---------------- In-memory guards (replace with Redis in prod) ----------------
_seen_nonces: dict[str, float] = {}                           # for /verify replay
_used_tokens: dict[str, float] = {}                           # NEW: single-use tokens
_rate_user: dict[str, deque] = defaultdict(deque)
_rate_device: dict[str, deque] = defaultdict(deque)
_day_count_device: dict[str, Tuple[int,int]] = defaultdict(lambda: (0, 0))  # (yyyymmdd, count)

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _today_key() -> int:
    dt = datetime.now(timezone.utc)
    return dt.year * 10000 + dt.month * 100 + dt.day

def _sign(data: str) -> str:
    return hmac.new(HMAC_SECRET, data.encode(), hashlib.sha256).hexdigest()

# ---------- Nonce & Token helpers ----------
def check_nonce_fresh(nonce: str) -> None:
    now = time.time()
    try:
        _, ts_str = nonce.split(".", 1)
        ts = int(ts_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail="BAD_NONCE") from e
    if now - ts > NONCE_TTL_SEC:
        raise HTTPException(status_code=400, detail="NONCE_EXPIRED")
    if nonce in _seen_nonces:
        raise HTTPException(status_code=409, detail="REPLAY_DETECTED")
    _seen_nonces[nonce] = now

def build_token(nonce: str, user_id: str, device_id: str, op: str) -> str:
    payload = f"{nonce}|{user_id}|{device_id}|{op}"
    sig = _sign(payload)
    return f"{payload}~{sig}"

def verify_token(token: str, *, expect_user: str, expect_device: str, expect_op: str) -> None:
    """Raise HTTPException if invalid. Single-use within TTL."""
    now = time.time()
    try:
        payload, sig = token.split("~", 1)
        nonce, user_id, device_id, op = payload.split("|", 3)
    except Exception as e:
        raise HTTPException(status_code=401, detail="BAD_TOKEN") from e

    # signature check (constant-time)
    if not hmac.compare_digest(_sign(payload), sig):
        raise HTTPException(status_code=401, detail="BAD_TOKEN_SIG")

    # bind checks
    if user_id != expect_user or device_id != expect_device or op != expect_op:
        raise HTTPException(status_code=401, detail="TOKEN_CONTEXT_MISMATCH")

    # TTL check from nonce ts
    try:
        _, ts_str = nonce.split(".", 1)
        ts = int(ts_str)
    except Exception:
        raise HTTPException(status_code=401, detail="BAD_NONCE")
    if now - ts > NONCE_TTL_SEC:
        raise HTTPException(status_code=401, detail="TOKEN_EXPIRED")

    # single-use
    if token in _used_tokens:
        raise HTTPException(status_code=409, detail="TOKEN_REPLAY")
    _used_tokens[token] = now

# ---------------- Rate limiting helpers ----------------
def enforce_rate_limit(user_id: str, device_id: str) -> None:
    now = time.time()
    window = 60.0

    dq_u = _rate_user[user_id]
    while dq_u and now - dq_u[0] > window:
        dq_u.popleft()
    if len(dq_u) >= RATE_PER_MIN:
        raise HTTPException(status_code=429, detail="RATE_LIMIT_USER")
    dq_u.append(now)

    dq_d = _rate_device[device_id]
    while dq_d and now - dq_d[0] > window:
        dq_d.popleft()
    if len(dq_d) >= RATE_PER_MIN:
        raise HTTPException(status_code=429, detail="RATE_LIMIT_DEVICE")
    dq_d.append(now)

    day_key, cnt = _day_count_device[device_id]
    tk = _today_key()
    if day_key != tk:
        _day_count_device[device_id] = (tk, 0)
        day_key, cnt = tk, 0
    if cnt >= DAY_CAP_PER_DEVICE:
        raise HTTPException(status_code=429, detail="DAY_CAP_DEVICE")
    _day_count_device[device_id] = (day_key, cnt + 1)

def ensure_device_binding(user_id: str, device_id: str) -> bool:
    # TODO: integrate real DB binding (1 user = 1 device)
    return True

# ---------------- Schemas ----------------
class VerifyFaceIn(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=128)
    image_b64: str
    device_id: str = Field(..., min_length=3, max_length=128)
    op: str = Field("withdraw", description="login|withdraw|highrisk")
    nonce: str = Field(..., description="client generated: {uuid}.{epoch_sec}")

    @field_validator("image_b64")
    @classmethod
    def _looks_like_b64(cls, v: str) -> str:
        if len(v) < 100:
            raise ValueError("IMAGE_TOO_SMALL")
        if " " in v or "\n" in v:
            raise ValueError("BAD_BASE64_FORMAT")
        return v

class VerifyFaceOut(BaseModel):
    ok: bool
    score_match: float
    score_liveness: float
    reason: Optional[str] = None
    ts_iso: str
    token: Optional[str] = None   # NEW: single-use token for downstream

# ---------------- Core Service ----------------
_provider = get_provider()

def _fail(reason: str, m: float = 0.0, l: float = 0.0) -> VerifyFaceOut:
    return VerifyFaceOut(ok=False, score_match=m, score_liveness=l, reason=reason, ts_iso=utcnow_iso(), token=None)

@router.post("/safety/face/verify", response_model=VerifyFaceOut)
async def post_verify_face(p: VerifyFaceIn, req: Request) -> VerifyFaceOut:
    # 1) Guards
    enforce_rate_limit(p.user_id, p.device_id)
    check_nonce_fresh(p.nonce)
    if not ensure_device_binding(p.user_id, p.device_id):
        return _fail("DEVICE_MISMATCH")

    # 2) Embedding (dev: use probe as gallery)
    try:
        probe_vec = _provider.embed_from_b64(p.image_b64)
        gallery_vec = probe_vec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        raise HTTPException(status_code=500, detail="EMBED_ERROR")

    # 3) Match
    try:
        ok_m, score_m = _provider.match(gallery_vec, probe_vec)
    except Exception:
        raise HTTPException(status_code=500, detail="MATCH_ERROR")

    # 4) Liveness
    try:
        score_l = _provider.liveness_score(p.image_b64)
    except Exception:
        raise HTTPException(status_code=500, detail="LIVENESS_ERROR")

    if not ok_m or score_m < MATCH_TH:
        return _fail("MATCH_LOW", score_m, score_l)
    if score_l < LIVE_TH:
        return _fail("LIVENESS_LOW", score_m, score_l)

    # 5) Success → issue single-use token (bound to user/device/op)
    token = build_token(p.nonce, p.user_id, p.device_id, p.op)
    return VerifyFaceOut(
        ok=True,
        score_match=float(score_m),
        score_liveness=float(score_l),
        reason=None,
        ts_iso=utcnow_iso(),
        token=token,
    )

# --------- EXPORTED for other modules (NEW) ----------
def verify_face_token_or_401(token: str, *, user_id: str, device_id: str, op: str) -> None:
    """Reusable verifier for other routers/services."""
    verify_token(token, expect_user=user_id, expect_device=device_id, expect_op=op)
