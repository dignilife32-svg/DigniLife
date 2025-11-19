# src/auth/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session
from src.auth.schemas import RegisterRequest, LoginRequest, KycSubmitRequest, TokenResponse
from src.auth import service as auth_service

from src.auth.deps import get_current_user
from src.auth.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_session)):
    try:
        sess = auth_service.register_user(db, req.email, req.face_image_b64, req.device_fp)
        user = db.query(auth_service.User).filter(auth_service.User.id == sess.user_id).one()
        return TokenResponse(token=sess.id, user_id=sess.user_id, identity_tier=user.identity_tier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_session)):
    try:
        sess = auth_service.login(db, req.email, req.face_image_b64, req.device_fp)
        user = db.query(auth_service.User).filter(auth_service.User.id == sess.user_id).one()
        return TokenResponse(token=sess.id, user_id=sess.user_id, identity_tier=user.identity_tier)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
def logout(x_auth_token: str = Header(...), db: Session = Depends(get_session)):
    auth_service.logout(db, x_auth_token)
    return {"ok": True}

@router.post("/kyc/submit")
def kyc_submit(req: KycSubmitRequest, user=Depends(get_current_user), db: Session = Depends(get_session)):
    return auth_service.kyc_submit(db, user_id=user.id, id_images_b64=req.id_images_b64, id_meta=req.id_meta)

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email, "identity_tier": user.identity_tier}

