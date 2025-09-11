# src/auth/router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import os
from src.auth.security import make_token, ADMIN_KEY, Role

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: Role = "user"
    admin_key: Optional[str] = None

@router.post("/login")
def login(body: LoginRequest):
    if body.role == "admin":
        if (body.admin_key or "") != ADMIN_KEY:
            raise HTTPException(status_code=401, detail="Invalid admin key")
    token = make_token(body.user_id, body.role)
    return {"access_token": token, "token_type": "bearer", "role": body.role}
