# src/routers/wallet.py
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# project deps
from src.db.session import get_session  # <- make sure this returns AsyncSession
from src.wallet import service as wallet_service
from src.wallet.schemas import (
    WalletSummarySchema,
    EarnIn, EarnOut,
    WithdrawIn, WithdrawOut,
    HoldFundsIn, ReleaseHoldIn,
    LimitsSchema,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])

# ---- simple header-based auth (works with your middleware, too) -------------
async def current_user(
    x_user_id: Optional[str] = Header(default=None, alias="x-user-id")
) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-user-id header required",
        )
    return x_user_id


# ---- routes ------------------------------------------------------------------

@router.get("/limits", response_model=LimitsSchema)
async def get_limits() -> LimitsSchema:
    return LimitsSchema()


@router.get("/summary", response_model=WalletSummarySchema)
async def get_wallet_summary(
    db: AsyncSession = Depends(get_session),
    user_id: str = Depends(current_user),
) -> WalletSummarySchema:
    bal = await wallet_service.get_summary(db, user_id)
    return WalletSummarySchema(balance_usd=bal.balance_usd if hasattr(bal, "balance_usd") else float(bal))


@router.post("/earn", response_model=EarnOut)
async def pos_earn(
    payload: EarnIn,                                  # <- non-defaults FIRST
    db: AsyncSession = Depends(get_session),          # <- defaults (Depends) AFTER
    user_id: str = Depends(current_user),
) -> EarnOut:
    out = await wallet_service.pos_earn(db, user_id, payload)
    return EarnOut(balance_usd=out.balance_usd)


@router.post("/withdraw", response_model=WithdrawOut)
async def pos_withdraw(
    payload: WithdrawIn,
    db: AsyncSession = Depends(get_session),
    user_id: str = Depends(current_user),
) -> WithdrawOut:
    out = await wallet_service.pos_withdraw(db, user_id, payload)
    return WithdrawOut(balance_usd=out.balance_usd)


@router.post("/reserve", status_code=200)
async def hold_funds(
    payload: HoldFundsIn,
    db: AsyncSession = Depends(get_session),
    user_id: str = Depends(current_user),
) -> dict:
    await wallet_service.hold_funds(db, user_id, payload)
    return {"ok": True}


@router.post("/reserve/release", status_code=200)
async def release_funds(
    payload: ReleaseHoldIn,
    db: AsyncSession = Depends(get_session),
    user_id: str = Depends(current_user),
) -> dict:
    await wallet_service.release_hold(db, user_id, payload)
    return {"ok": True}
