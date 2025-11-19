# src/safety/proofguard.py
from __future__ import annotations
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from src.safety.facegate import verify_face_token_or_401  # from your existing file

class FaceProof(BaseModel):
    user_id: str
    device_id: str
    op: str = "withdraw"

async def require_face_proof(
    user_id: str,
    device_id: str,
    x_face_token: str | None = Header(None, alias="X-Face-Token"),
) -> FaceProof:
    if not x_face_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FACE_TOKEN_MISSING")
    # Will raise if invalid/expired/replayed/mismatch:
    verify_face_token_or_401(x_face_token, user_id=user_id, device_id=device_id, op="withdraw")
    return FaceProof(user_id=user_id, device_id=device_id, op="withdraw")
