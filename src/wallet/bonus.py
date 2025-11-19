# src/wallet/bonus.py
from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import blake2b

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.money import as_money
from src.db.models import WalletLedger, LedgerType
from src.config.settings import BONUS_PERCENT, BONUS_MIN_CENTS, BONUS_DAILY_CAP_USD

# ---------------- helpers ----------------

def _today_utc() -> datetime:
    return datetime.now(timezone.utc)

def _make_idem(user_id: str, base_amount_usd: Decimal, ref: Optional[str]) -> str:
    h = blake2b(digest_size=16)
    h.update(str(user_id).encode())
    h.update(str(as_money(base_amount_usd)).encode())
    h.update((ref or "").encode())
    h.update(_today_utc().date().isoformat().encode())
    return h.hexdigest()

# ---------------- queries ----------------

async def today_bonus_total(session: AsyncSession, user_id: str) -> Decimal:
    q = (
        select(func.coalesce(func.sum(WalletLedger.amount_usd), 0))
        .where(WalletLedger.user_id == user_id)
        .where(WalletLedger.type_ == LedgerType.BONUS)
        .where(func.date(WalletLedger.created_at) == _today_utc().date())
    )
    value = (await session.execute(q)).scalar_one()
    return as_money(value or 0)

# business compute (if you still need percentage path)
def calc_bonus(base_amount_usd: Decimal) -> Decimal:
    """
    If you are calling apply_bonus() with a *final* per-line amount,
    this function is not used. Kept for backwards-compat calls.
    """
    pct = Decimal(str(BONUS_PERCENT or 0))
    min_cents = Decimal(str(BONUS_MIN_CENTS or 0)) / Decimal("100")
    amt = as_money(base_amount_usd * pct)
    if amt < min_cents:
        amt = as_money(min_cents)
    return amt

# ---------------- idempotent writer ----------------

async def apply_bonus(
    session: AsyncSession,
    user_id: str,
    base_amount_usd: Decimal,
    ref: Optional[str] = None,           # idempotency key (recommended: engine-provided)
    meta: Optional[Dict[str, Any]] = None,
) -> Tuple[Decimal, Optional[str]]:
    """
    Returns: (amount_usd, ledger_id or None)
    - Idempotent per (user_id, idem_key) UNIQUE (create a unique index in DB).
    - If duplicate, returns (0, None).
    """
    amount = as_money(base_amount_usd)  # already final from engine (or use calc_bonus if needed)

    # respect global daily cap (extra guard — engine already enforces)
    if BONUS_DAILY_CAP_USD is not None:
        today_total = await today_bonus_total(session, user_id)
        remaining = as_money(Decimal(str(BONUS_DAILY_CAP_USD)) - today_total)
        if remaining <= Decimal("0.00"):
            return (Decimal("0.00"), None)
        if amount > remaining:
            amount = remaining

    idem_key = ref or _make_idem(user_id, amount, ref)
    row = WalletLedger(
        user_id=user_id,
        type_=LedgerType.BONUS,           # ensure your Enum/const matches
        amount_usd= amount,
        idempotency_key=idem_key,               # <-- UNIQUE INDEX REQUIRED
        ref_task_code=ref,
        created_at=_today_utc(),
    )

    try:
        session.add(row)
        await session.flush()  # leave commit to caller
        return (amount, getattr(row, "id", None))
    except IntegrityError:
        # duplicate (idempotent conflict) — already granted
        await session.rollback()  # rollback the failed insert only
        return (Decimal("0.00"), None)
