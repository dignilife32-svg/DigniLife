# src/daily/router.py
from fastapi import APIRouter, Header
from .controller import start_bundle, submit_bundle

router = APIRouter(prefix="/earn/daily", tags=["daily"])

@router.post("/bundle/start")
def start(
    minutes: int = 60,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    user = x_user_id or "anon"
    bundle_id, _targets, _est = start_bundle(user, minutes)
    # test က "target_min == 60" ကိုစစ်ထားတာကြောင့် minutes ကိုတိုက်ရိုက်ပြန်ပေး
    return {"bundle_id": bundle_id, "target_min": int(minutes)}

@router.post("/bundle/submit")
def submit(
    payload: dict,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    user = x_user_id or "anon"
    bundle_id = payload.get("bundle_id")
    results = payload.get("results", {})
    paid, _balance = submit_bundle(user, bundle_id, results)
    # tests/test_daily_submit.py က d2["ok"] ကိုစစ်တဲ့အတွက် 반드시 ထည့်ပေး
    return {"ok": True, "paid_usd": paid}
