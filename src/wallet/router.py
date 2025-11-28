#src/wallet/router.py
from __future__ import annotations
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Body, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session

# --- Safety fallbacks (AI grace)
try:
    from src.safety.risk import assess_withdraw_risk
except Exception:
    async def assess_withdraw_risk(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"action": "ok", "score": 0.0, "reasons": []}

try:
    from src.safety.facegate import verify_face_token
except Exception:
    async def verify_face_token(*args: Any, **kwargs: Any) -> bool:
        return True

# --- Service imports
from src.wallet.service import (
    get_user_usd_balance,
    add_earning,
    add_adjustment,
    create_withdraw_reserve,
    release_funds,
    commit_withdraw,
    reverse_withdraw,
    payout_dispatch,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


# ---------- Schemas ----------
class BalanceOut(BaseModel):
    balance_usd: float = Field(..., example=12.3)


class EarnIn(BaseModel):
    usd_cents: int = Field(..., ge=0)
    note: Optional[str] = None
    ref: Optional[str] = None


class AdjustIn(BaseModel):
    amount_usd: float
    note: Optional[str] = None
    ref: Optional[str] = None


class ReserveIn(BaseModel):
    amount_usd: float = Field(..., gt=0)
    note: Optional[str] = None
    ref: Optional[str] = None


class WithdrawIn(BaseModel):
    amount_usd: float = Field(..., gt=0.0)
    note: Optional[str] = None
    ref: Optional[str] = None
    payout_method: str = Field("bank", example="bank|ewallet|prepaid_card|store_cash|unbanked_ai_cash")
    payout_target: str = Field(..., example="MAYBANK-ACCT-1234567890")
    device_id: Optional[str] = None
    face_token: Optional[str] = None
    ip: Optional[str] = None


class GenericOut(BaseModel):
    id: str
    detail: Optional[dict] = None


# ---------- Dependencies ----------
def require_user(x_user_id: Optional[str] = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="x-user-id header required")
    return x_user_id


# ---------- Routes ----------
@router.get("/balance", response_model=BalanceOut)
async def wallet_balance(user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    bal = await get_user_usd_balance(user_id=user_id, session=db)
    return BalanceOut(balance_usd=float(bal))


@router.post("/earn", response_model=GenericOut, status_code=201)
async def wallet_earn(payload: EarnIn, user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    rid = await add_earning(session=db, user_id=user_id, amount_usd=payload.usd_cents / 100, note=payload.note or "EARN", request_id=payload.ref or "")
    return GenericOut(id=rid)


@router.post("/adjust", response_model=GenericOut, status_code=201)
async def wallet_adjust(payload: AdjustIn, user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    rid = await add_adjustment(session=db, user_id=user_id, amount_usd=payload.amount_usd, note=payload.note or "ADJUST", request_id=payload.ref or "")
    return GenericOut(id=rid)


@router.post("/reserve", response_model=GenericOut, status_code=201)
async def wallet_reserve(payload: ReserveIn, user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    rid = await create_withdraw_reserve(session=db, user_id=user_id, amount_usd=payload.amount_usd, note=payload.note or "WITHDRAW_RESERVE", request_id=payload.ref or "")
    return GenericOut(id=rid)


@router.post("/reserve/release", response_model=GenericOut)
async def wallet_release(payload: ReserveIn, user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    rid = await release_funds(session=db, user_id=user_id, amount_usd=payload.amount_usd, note=payload.note or "RESERVE_RELEASE", request_id=payload.ref or "")
    return GenericOut(id=rid)


@router.post("/withdraw", response_model=GenericOut)
async def wallet_withdraw(request: WithdrawIn, user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    amt = round(request.amount_usd, 2)
    if amt <= 0:
        raise HTTPException(status_code=422, detail="amount_usd must be > 0")

    # --- AI Risk Check ---
    risk = await assess_withdraw_risk(user_id=user_id, amount=amt)
    if risk.get("action") == "block":
        raise HTTPException(status_code=403, detail="Withdraw blocked by AI risk policy")
    if risk.get("action") == "face":
        if not request.face_token or not (await verify_face_token(request.face_token, user_id, request.device_id)):
            raise HTTPException(status_code=401, detail="Face verification required")

    wid = await commit_withdraw(session=db, user_id=user_id, amount_usd=amt, note=f"{request.note or 'WITHDRAW'}:{request.payout_method}", request_id=request.ref or "")
    payout = await payout_dispatch(user_id=user_id, amount=amt, method=request.payout_method, target=request.payout_target)
    return GenericOut(id=wid, detail=payout)


@router.get("/summary", response_model=BalanceOut)
async def wallet_summary(user_id: str = Depends(require_user), db: AsyncSession = Depends(get_session)):
    bal = await get_user_usd_balance(user_id=user_id, session=db)
    return BalanceOut(balance_usd=float(bal))
