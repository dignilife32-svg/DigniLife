# src/wallet/logic.py
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import WalletLedger, LedgerType
# NOTE: commit_ledger_entry MUST NOT receive "meta". We pass only supported fields.
from src.utils.db_helpers import commit_ledger_entry

__all__ = ["get_balance", "add_earning", "add_adjustment"]


# -------------------------------------------------
# Queries
# -------------------------------------------------
async def get_balance(db: AsyncSession, user_id: str) -> Decimal:
    """
    Return current wallet balance for a user.

    Positive types (+): EARN_COMMIT, BONUS, ADJUST
    Negative types (-): WITHDRAW_*, SYSTEM_CUT
    """
    q = select(func.coalesce(func.sum(WalletLedger.amount_usd), 0)).where(
        WalletLedger.user_id == user_id
    )
    res = await db.execute(q)
    total = res.scalar_one() or 0
    # Decimal(str(x)) is the most stable & DB-agnostic coercion
    return Decimal(str(total))


# -------------------------------------------------
# Mutations
# -------------------------------------------------
async def add_earning(
    db: AsyncSession,
    user_id: str,
    amount_usd: Decimal | float,
    ref: Optional[str] = None,
) -> int:
    """
    Record a positive earning entry for the user.
    - `ref` is mapped to `ref_task_code` (truncated 64 chars).
    """
    amt = Decimal(amount_usd)
    if amt <= 0:
        raise ValueError("add_earning() expects a positive amount_usd")

    row_id = await commit_ledger_entry(
        db=db,
        user_id=user_id,
        type_=LedgerType.EARN_COMMIT,
        amount_usd=amt,
        ref_task_code=(ref or "")[:64],
    )
    return row_id


async def add_adjustment(
    db: AsyncSession,
    user_id: str,
    amount_usd: Decimal | float,
    reason: Optional[str] = None,
) -> int:
    """
    Manual balance adjustment (admin/system use).
    Positive increases balance; negative decreases.
    """
    amt = Decimal(amount_usd)
    if amt == 0:
        raise ValueError("add_adjustment() amount_usd must be non-zero")

    row_id = await commit_ledger_entry(
        db=db,
        user_id=user_id,
        type_=LedgerType.ADJUST,
        amount_usd=amt,
        ref_task_code=(reason or "")[:64],
    )
    return row_id

async def get_user_usd_balance(db: AsyncSession, user_id: str) -> Decimal:
    return await get_balance(db, user_id)
