# src/routers/ai_explain.py
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Request
from src.middleware.explainer import build_explanation

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/explain")
async def explain(request: Request, payload: Dict[str, Any]):
    # middleware ထဲက signals
    signals = getattr(request.state, "ai_signals", {}) or {}
    # ဥပမာ reply (จริงๆ prod မှာ ကိုယ့် model/business reply ထည့်)
    reply = "Acknowledged."
    return {
        "ok": True,
        "data": payload,
        "signals": signals,
        "explain": build_explanation(request=request, reply=reply, signals=signals),
    }
