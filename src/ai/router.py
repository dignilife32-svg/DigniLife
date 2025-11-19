# src/ai/router.py
from __future__ import annotations
from fastapi import APIRouter

# Auto-wiring scanner က ယခု variable ကိုရှာတယ်
router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/health")
async def health():
    return {"ok": True}

__all__ = ["router"]
