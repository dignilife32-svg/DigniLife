from fastapi import APIRouter, Header
from .controller import start_bundle, submit_bundle

router = APIRouter(prefix="/earn/daily", tags=["daily"])

@router.post("/bundle/start")
def start(minutes: int = 60, x_user_id: str | None = Header(None, alias="x-user-id")):
    user = x_user_id or "anon"
    bundle_id, targets, plan, minutes = start_bundle(user, minutes)
    # expose targets so client can display $/hour goals (200/300/500)
    return {"ok": True, "bundle_id": bundle_id, "targets": targets, "plan": plan, "minutes": minutes}

@router.post("/bundle/submit")
def submit(payload: dict, x_user_id: str | None = Header(None, alias="x-user-id")):
    user = x_user_id or "anon"
    bundle_id = payload.get("bundle_id")
    results = payload.get("results", {})
    paid_usd, balance = submit_bundle(user, bundle_id, results)
    return {"ok": True, "paid_usd": float(paid_usd), "balance": float(balance)}
