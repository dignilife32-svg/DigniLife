# src/auth/schemas.py
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List

class RegisterRequest(BaseModel):
    email: EmailStr
    face_image_b64: str = Field(..., description="Base64 face image")
    device_fp: str

class LoginRequest(BaseModel):
    email: EmailStr
    face_image_b64: str
    device_fp: str

class KycSubmitRequest(BaseModel):
    # Optional ID (any type) — images or metadata
    id_images_b64: Optional[List[str]] = None
    id_meta: Optional[Dict[str, Any]] = None

class TokenResponse(BaseModel):
    token: str
    user_id: str
    identity_tier: str
