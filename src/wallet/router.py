# src/wallet/router.py
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Request, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from src.safety.risk import assess_withdraw_risk
from src.safety.proofguard import require_face_proof, FaceProof
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from .logic import get_balance, add_earning, add_adjustment
from .reserve import hold_funds, release_funds


router = APIRouter(prefix="/wallet", tags=["wallet"])


# ---- Schemas ----------------------------------------------------------------

class BalanceOut(BaseModel):
    balance_usd: float = Field(..., example=12.30)


class EarnIn(BaseModel):
    usd_cents: int = Field(..., ge=1, example=250)   # 2.50 USD
    note: Optional[str] = Field(None, example="daily task reward")
    ref: Optional[str] = Field(None, example="task:c1")


class AdjustIn(BaseModel):
    amount_usd: float = Field(..., example=-1.25)    # can be +/-
    note: Optional[str] = None
    ref: Optional[str] = None


class ReserveIn(BaseModel):
    amount_usd: float = Field(..., gt=0.0, example=5.0)
    note: Optional[str] = None
    ref: Optional[str] = None


class ReserveOut(BaseModel):
    reserved_id: int


class GenericRowOut(BaseModel):
    id: int

class WithdrawIn(BaseModel):
    user_id: str = Field(..., min_length=3)
    device_id: str = Field(..., min_length=3)
    amount: float = Field(..., gt=0)

# ---- Dependencies -----------------------------------------------------------

def _require_user(x_user_id: Optional[str] = Header(default=None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="x-user-id header is required")
    return x_user_id


# ---- Routes ----------------------------------------------------------------

@router.get("/balance", response_model=BalanceOut)
async def wallet_balance(
    user_id: str = Depends(_require_user), db: AsyncSession = Depends(get_session)
):
    bal = await get_balance(db, user_id=user_id)
    return BalanceOut(balance_usd=bal)


@router.post("/earn", response_model=GenericRowOut, status_code=status.HTTP_201_CREATED)
async def wallet_earn(
    payload: EarnIn, user_id: str = Depends(_require_user), db: AsyncSession = Depends(get_session)
):
    rid = await add_earning(
        db,
        user_id=user_id,
        usd_cents=payload.usd_cents,
        note=payload.note,
        ref=payload.ref,
    )
    return GenericRowOut(id=rid)


@router.post("/adjust", response_model=GenericRowOut)
async def wallet_adjust(
    payload: AdjustIn, user_id: str = Depends(_require_user), db: AsyncSession = Depends(get_session)
):
    rid = await add_adjustment(
        db,
        user_id=user_id,
        amount_usd=payload.amount_usd,
        note=payload.note,
        ref=payload.ref,
    )
    return GenericRowOut(id=rid)


@router.post("/reserve", response_model=ReserveOut)
async def wallet_reserve(
    payload: ReserveIn, user_id: str = Depends(_require_user), db: AsyncSession = Depends(get_session)
):
    rid = await hold_funds(db, user_id=user_id, amount_usd=payload.amount_usd, note=payload.note, ref=payload.ref)
    return ReserveOut(reserved_id=rid)


@router.post("/reserve/release", response_model=GenericRowOut)
async def wallet_reserve_release(
    payload: ReserveIn, user_id: str = Depends(_require_user), db: AsyncSession = Depends(get_session)
):
    rid = await release_funds(db, user_id=user_id, amount_usd=payload.amount_usd, note=payload.note, ref=payload.ref)
    return GenericRowOut(id=rid)

@router.post("/withdraw")
async def withdraw_funds(p: WithdrawIn, request: Request, x_face_token: Optional[str] = Header(None, alias="X-Face-Token")):
    # 1) Assess risk
    ip = request.client.host if request.client else "0.0.0.0"
    ip_hash = str(hash(ip))  # swap to real hash if needed
    risk = assess_withdraw_risk(user_id=p.user_id, device_id=p.device_id, amount=p.amount, ip_hash=ip_hash)

    # 2) Gate by risk
    if risk.action == "block":
        raise HTTPException(status_code=403, detail={"msg": "WITHDRAW_BLOCKED", "risk": risk.reasons, "score": risk.score})

    if risk.require_face:
        if not x_face_token:
            raise HTTPException(status_code=401, detail={"msg": "FACE_TOKEN_REQUIRED", "risk": risk.reasons})
        # consume/verify token (raises on fail)
        from src.safety.facegate import verify_face_token_or_401
        verify_face_token_or_401(x_face_token, user_id=p.user_id, device_id=p.device_id, op="withdraw")


    # Proceed to your existing wallet logic
    try:
        tx = await withdraw_funds(user_id=p.user_id, amount=p.amount)  # adapt to your signature
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="WITHDRAW_ERROR") from e
    tx = None # fallback 
    
    return {
        "ok": True,
        "tx_id": getattr(tx, "id", None),
        "amount": p.amount,
        "ts": getattr(tx, "created_at", None).isoformat() if getattr(tx, "created_at", None) else None,
        
        "risk": {"action": risk.action, "score": risk.score, "reasons": risk.reasons},
        "face_checked": bool(x_face_token) if risk.require_face else False,
    }
