# src/bonus/router.py
from __future__ import annotations
from decimal import Decimal
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.bonus.service import grant_daily_submit_bonus

router = APIRouter(prefix="/bonus", tags=["bonus"])

# ---------- Schemas ----------
class TestBonusRequest(BaseModel):
    user_id: str = Field(..., examples=["user_123"])
    base_usd: Decimal = Field(..., examples=["1.00"])
    user_flags: Dict[str, Any] = Field(default_factory=dict, examples=[{"is_trust_ok": True, "is_kyc_ok": True}])
    source_id: Optional[str] = Field(default=None, examples=["assist-0001"])

class TestBonusResponse(BaseModel):
    ok: bool
    granted: str
    capped: bool
    lines: list[dict]
    ts: str

# ---------- Route ----------
@router.post("/test", response_model=TestBonusResponse)
async def test_bonus(
    payload: TestBonusRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick test endpoint to grant DAILY_SUBMIT_OK bonus.
    Uses the production service + wallet ledger (idempotent).
    """
    try:
        result = await grant_daily_submit_bonus(
            session,
            user_id=payload.user_id,
            base_usd=payload.base_usd,
            user_flags=payload.user_flags,
            source_id=payload.source_id,
        )
        # commit the ledger writes
        await session.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
