# src/daily/router.py
from typing import Optional
from fastapi import APIRouter, Header, HTTPException

from src.wallet.client import get_wallet
from src.daily.controller import start_bundle, submit_bundle
from src.daily.models import UserCapabilities, SubmitRequest, SubmitResponse, StartResponse

router = APIRouter(prefix="/earn/daily", tags=["daily"])

@router.post("/bundle/start", response_model=StartResponse)
def start(
    minutes: int = 60,
    x_user_id: Optional[str] = Header(None, alias="x-user-id"),
    x_prefers_voice: Optional[str] = Header(None, alias="x-prefers-voice"),
):
    user = x_user_id or "anon"
    caps = UserCapabilities(prefers_voice=(x_prefers_voice.lower() == "true") if x_prefers_voice else None)

    bundle_id, targets, bundle_minutes = start_bundle(user, minutes, caps)

    return {
        "ok": True,
        "bundle_id": bundle_id,
        "targets": targets,
        "minutes": bundle_minutes,
        "user_id": user,
    }

@router.post("/bundle/submit", response_model=SubmitResponse)
def submit(
    payload: SubmitRequest,
    x_user_id: Optional[str] = Header(None, alias="x-user-id"),
):
    user = x_user_id or "anon"

    # controller က verify/mutate လုပ်စေမယ်
    try:
        paid_usd, new_balance = submit_bundle(user_id=user, bundle_id=payload.bundle_id, results=payload.results)
    except ValueError as e:
        # owner မကိုက်/ bundle မရှိ စတဲ့ case မှာ 400 ပစ်
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ok": True,
        "bundle_id": payload.bundle_id,
        "paid_usd": float(paid_usd),
        "new_balance": float(new_balance),
    }
