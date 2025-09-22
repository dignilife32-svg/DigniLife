# src/auth/service.py
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

class OptionalUser:
    # သင့် project အတွက် field တွေ ထပ်ထည့်နိုင်ပါတယ်
    def __init__(self, sub: Optional[str] = None):
        self.sub = sub

def verify_token(token: str) -> dict:
    # TODO: သင့် JWT/Custom token verify logic
    return {"sub": "demo-user"}

def create_access_token(sub: str) -> str:
    # TODO: create token logic
    return "demo-token"

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[OptionalUser]:
    if creds is None:
        return None
    try:
        payload = verify_token(creds.credentials)
        return OptionalUser(sub=payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
