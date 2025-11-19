# src/auth/deps.py
from __future__ import annotations
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from src.db.session import get_session
from src.db.models import AuthSession, User

def get_current_user(x_auth_token: str = Header(...), db: Session = Depends(get_session)):
    sess = db.query(AuthSession).filter(AuthSession.id == x_auth_token).one_or_none()
    if not sess or sess.revoked_at is not None or (sess.expires_at and sess.expires_at < datetime.utcnow()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_or_expired_token")
    user = db.query(User).filter(User.id == sess.user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="user_not_found")
    return user
