from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Literal, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# DB session helper
from src.db.session import get_session

# Wallet models (enum + ledger)
from src.wallet.models import WalletLedger, LedgerType

# Face/KYC gate – this is what your facegate.py actually exports
from src.safety.facegate import verify_face_token_or_401

# ---- settings (env override later if you like) ----
WITHDRAWAL_FEE_PERCENT = Decimal("5.0")   # 5%
DAILY_BASELINE_CUT    = Decimal("3.33")   # $3.33/day (reserved for future logic)

router = APIRouter(prefix="/withdraw", tags=["withdraw"])


# -----------------------------
# Schemas
# -----------------------------
class WithdrawRequest(BaseModel):
    user_id: str = Field(..., examples=["user_123"])
    amount_usd: Decimal = Field(..., gt=Decimal("0.00"), examples=["6.00"])
    # optional device binding for face token
    device_id: Optional[str] = Field(None, examples=["dev_abc"])
    face_token: Optional[str] = Field(None, description="Short-lived face verify token")
    source_id: Optional[str] = Field(None, description="Trace id (client)")


class WithdrawPreview(BaseModel):
    ok: bool = True
    rid: str
    gross_usd: Decimal
    fee_usd: Decimal
    net_usd: Decimal
    capped: bool = False


class WithdrawConfirmRequest(BaseModel):
    rid: str
    method: Literal["bank", "prepaid", "online_bank", "ewallet", "topup"]
    destination: Optional[str] = Field(
        None, description="masked account / phone / wallet id shown in dashboard only"
    )
    device_id: Optional[str] = None
    face_token: Optional[str] = None


class WithdrawLine(BaseModel):
    rule: str
    ok: bool
    ledger_id: int


class WithdrawConfirmResponse(BaseModel):
    ok: bool = True
    lines: List[WithdrawLine]
    id: str  # iso timestamp or uuid
    capped: bool = False


# -----------------------------
# Helpers
# -----------------------------
def _q2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calc_fee(amount: Decimal) -> Decimal:
    fee = (amount * WITHDRAWAL_FEE_PERCENT / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return fee if fee > Decimal("0.00") else Decimal("0.00")


# simple in-memory preview cache (swap to Redis later)
_preview_cache: Dict[str, Dict[str, Any]] = {}


# -----------------------------
# Routes
# -----------------------------

@router.post("/start", response_model=WithdrawPreview)
async def start_withdraw(req: WithdrawRequest, db: AsyncSession = Depends(get_session)):
    # 1) face gate (optional token)
    if req.face_token:
        # facegate will raise 401 itself if invalid
        verify_face_token_or_401(req.face_token, req.user_id, req.device_id or "-", "withdraw:start")

    # 2) (optional) user existence check — enable only if you keep a users table
    # from src.db.models import User
    # user = (await db.execute(select(User).where(User.id == req.user_id))).scalar_one_or_none()
    # if not user:
    #     raise HTTPException(status_code=404, detail="user not found")

    gross = _q2(Decimal(req.amount_usd))
    fee = _calc_fee(gross)
    net = _q2(gross - fee)
    if net <= Decimal("0.00"):
        raise HTTPException(status_code=422, detail="amount too small after fee")

    import uuid
    rid = f"wd:{req.user_id}:{uuid.uuid4().hex[:12]}"

    _preview_cache[rid] = {
        "user_id": req.user_id,
        "device_id": req.device_id or "-",
        "gross": str(gross),
        "fee": str(fee),
        "net": str(net),
        "source_id": req.source_id,
    }

    return WithdrawPreview(ok=True, rid=rid, gross_usd=gross, fee_usd=fee, net_usd=net, capped=False)


@router.post("/confirm", response_model=WithdrawConfirmResponse)
async def confirm_withdraw(
    req: WithdrawConfirmRequest,
    db: AsyncSession = Depends(get_session),
    background: BackgroundTasks = None,
):
    prev = _preview_cache.get(req.rid)
    if not prev:
        raise HTTPException(status_code=404, detail="withdraw request not found or expired")

    user_id = prev["user_id"]
    device_id = req.device_id or prev.get("device_id") or "-"
    gross = Decimal(prev["gross"])
    fee = Decimal(prev["fee"])
    net = Decimal(prev["net"])

    if req.face_token:
        verify_face_token_or_401(req.face_token, user_id, device_id, "withdraw:confirm")

    # idempotency – already committed?
    already = (
        await db.execute(
            select(WalletLedger.id).where(
                WalletLedger.user_id == user_id,
                WalletLedger.type == LedgerType.WITHDRAW_FINAL,
                WalletLedger.ref_task_code == req.rid,
            )
        )
    ).scalar_one_or_none()
    if already:
        return WithdrawConfirmResponse(
            ok=True,
            lines=[
                WithdrawLine(rule="WITHDRAW_CUT", ok=True, ledger_id=already),
                WithdrawLine(rule="WITHDRAW_FINAL", ok=True, ledger_id=already),
            ],
            id=str(already),
            capped=False,
        )

    import datetime as _dt

    lines: List[WithdrawLine] = []

    # 1) CUT (fee)
    cut_row = WalletLedger(
        user_id=user_id,
        type=LedgerType.WITHDRAW_CUT,
        amount_usd=float(fee),
        idempotency_key=f"{req.rid}:cut",
        ref_task_code=req.rid,
        meta={
            "method": req.method,
            "destination": req.destination or "",
            "gross": str(gross),
            "fee": str(fee),
            "net": str(net),
            "source": "withdraw_api",
        },
        created_at=_dt.datetime.utcnow(),
    )
    db.add(cut_row)
    await db.flush()
    lines.append(WithdrawLine(rule="WITHDRAW_CUT", ok=True, ledger_id=cut_row.id))

    # 2) FINAL (net to user)
    final_row = WalletLedger(
        user_id=user_id,
        type=LedgerType.WITHDRAW_FINAL,
        amount_usd=float(net),
        idempotency_key=f"{req.rid}:final",
        ref_task_code=req.rid,
        meta={
            "method": req.method,
            "destination": req.destination or "",
            "gross": str(gross),
            "fee": str(fee),
            "net": str(net),
            "source": "withdraw_api",
        },
        created_at=_dt.datetime.utcnow(),
    )
    db.add(final_row)
    await db.flush()
    lines.append(WithdrawLine(rule="WITHDRAW_FINAL", ok=True, ledger_id=final_row.id))

    await db.commit()

    _preview_cache.pop(req.rid, None)

    return WithdrawConfirmResponse(
        ok=True,
        lines=lines,
        id=_dt.datetime.utcnow().isoformat() + "Z",
        capped=False,
    )
