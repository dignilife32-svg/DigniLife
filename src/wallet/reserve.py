# src/wallet/reserve.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def hold_funds(
    db: AsyncSession, *, user_id: str, amount_usd: float, note: Optional[str] = None, ref: Optional[str] = None
) -> int:
    """
    Minimal 'reserve' by writing a negative line into ledger (soft hold).
    Real reservation table can be added later; this is deploy-safe & reversible.
    """
    q = text(
        """
        INSERT INTO wallet_ledger (user_id, amount_usd, note, ref)
        VALUES (:user_id, :amount_usd, :note, :ref)
        """
    )
    await db.execute(q, {"user_id": user_id, "amount_usd": round(-abs(amount_usd), 2), "note": note, "ref": ref})
    await db.commit()
    rid = await db.scalar(text("SELECT last_insert_rowid()"))
    return int(rid or 0)


async def release_funds(
    db: AsyncSession, *, user_id: str, amount_usd: float, note: Optional[str] = None, ref: Optional[str] = None
) -> int:
    """
    Release a previous hold by adding the same positive amount.
    """
    q = text(
        """
        INSERT INTO wallet_ledger (user_id, amount_usd, note, ref)
        VALUES (:user_id, :amount_usd, :note, :ref)
        """
    )
    await db.execute(q, {"user_id": user_id, "amount_usd": round(abs(amount_usd), 2), "note": note, "ref": ref})
    await db.commit()
    rid = await db.scalar(text("SELECT last_insert_rowid()"))
    return int(rid or 0)
