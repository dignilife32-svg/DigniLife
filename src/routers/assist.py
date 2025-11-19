# src/routers/assist.py
from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from src.ai.assist import assist_once, AUTO_CREDIT_TH, _try_credit_wallet

router = APIRouter(prefix="/assist", tags=["assist"])

class AssistIn(BaseModel):
    user_id: str = Field(..., min_length=3)
    device_id: str = Field(..., min_length=3)
    text: Optional[str] = None
    image_b64: Optional[str] = None
    audio_b64: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    locale: Optional[str] = None
    task_hint: Optional[str] = Field(None, description="scan_qr|geo_ping|voice_3words|image_label|text_tag")
    auto_credit: bool = Field(True, description="credit wallet automatically when confidence >= threshold")

    @field_validator("image_b64", "audio_b64")
    @classmethod
    def _b64_len(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 64:
            raise ValueError("BASE64_TOO_SHORT")
        return v

class AssistOut(BaseModel):
    ok: bool
    task: Optional[str] = None
    confidence: Optional[float] = None
    payout_usd: Optional[float] = None
    needs_review: Optional[bool] = None
    reason: Optional[str] = None
    ts_iso: str
    credit_ok: Optional[bool] = None
    tx_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

@router.post("/submit", response_model=AssistOut)
async def submit(p: AssistIn, req: Request, bg: BackgroundTasks) -> AssistOut:
    # 1) Run assist core (threadpool-safe)
    out = await run_in_threadpool(assist_once, p.model_dump())
    if not out.get("ok"):
        raise HTTPException(status_code=429 if "RATE_LIMIT" in out.get("reason", "") else 400, detail=out.get("reason"))

    # 2) Optional auto-credit
    credit_ok = False
    tx_id = None
    if p.auto_credit and float(out["confidence"]) >= AUTO_CREDIT_TH:
        # we call sync wrapper in a thread to avoid blocking
        def _credit():
            return _try_credit_wallet(p.user_id, float(out["payout_usd"]), f"assist:{out['task']}", out.get("meta") or {})
        credit_ok, tx_id = await run_in_threadpool(_credit)

    return AssistOut(
        ok=True,
        task=out["task"],
        confidence=out["confidence"],
        payout_usd=out["payout_usd"],
        needs_review=out["needs_review"],
        reason=out["reason"],
        ts_iso=out["ts_iso"],
        credit_ok=credit_ok,
        tx_id=tx_id,
        meta=out.get("meta") or {},
    )
