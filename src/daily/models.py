# src/daily/models.py
from typing import Dict, Any, Optional
from pydantic import BaseModel

class UserCapabilities(BaseModel):
    prefers_voice: Optional[bool] = None

class StartResponse(BaseModel):
    ok: bool
    bundle_id: str
    targets: Dict[str, Any]
    minutes: int
    user_id: str

class SubmitRequest(BaseModel):
    bundle_id: str
    results: Dict[str, Any]   # test မှာ {"ok": True} လောက်ပဲ ပို့မယ်

class SubmitResponse(BaseModel):
    ok: bool
    bundle_id: str
    paid_usd: float
    new_balance: float
