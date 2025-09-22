# src/routers/feedback.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.utils.feedback_store import store

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackIn(BaseModel):
    message_id: str = Field(..., description="client-side id for the AI reply")
    vote: str = Field(..., pattern="^(up|down)$")
    text: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    meta: Optional[Dict[str, Any]] = None

@router.post("/save")
async def save_feedback(payload: FeedbackIn):
    try:
        store.append(payload.model_dump())
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
