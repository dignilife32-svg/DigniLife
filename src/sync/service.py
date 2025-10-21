# src/sync/service.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.wallet.logic import add_earning


async def _ref_exists(db: AsyncSession, *, user_id: str, ref: Optional[str]) -> bool:
    if not ref:
        return False
    q = text(
        """
        SELECT 1
        FROM wallet_ledger
        WHERE user_id = :user_id AND ref = :ref
        LIMIT 1
        """
    )
    row = await db.scalar(q, {"user_id": user_id, "ref": ref})
    return bool(row)


async def sync_earn_events(db: AsyncSession, *, user_id: str, events: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Minimal offline->online sync for earn events.
    - Skips duplicate refs for same user (idempotent-ish without schema change)
    - Writes via wallet.logic.add_earning
    """
    accepted = 0
    skipped = 0

    for ev in events:
        usd_cents = int(float(ev.get("usd_cents", 0)))
        note = ev.get("note") or None
        ref = ev.get("ref") or None

        if usd_cents <= 0:
            skipped += 1
            continue

        # idempotency by (user_id, ref)
        if await _ref_exists(db, user_id=user_id, ref=ref):
            skipped += 1
            continue

        await add_earning(db, user_id=user_id, usd_cents=usd_cents, note=note, ref=ref)
        accepted += 1

    return {"accepted": accepted, "skipped": skipped}
