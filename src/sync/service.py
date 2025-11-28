# src/sync/service.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.wallet.service import add_earning
from src.realtime.push import publish_user_update


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


async def sync_earn_events(
    db: AsyncSession,
    *,
    user_id: str,
    events: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Offline → Online earn sync.

    - client က usd_cents unit နဲ့ ပို့တယ်
    - server က amount_usd (float/Decimal) နဲ့ save တယ်
    - (user_id, ref) နဲ့ idempotent check လုပ်တယ်
    """
    accepted = 0
    skipped = 0

    for ev in events:
        usd_cents_raw = ev.get("usd_cents", 0)
        try:
            usd_cents = int(usd_cents_raw)
        except (TypeError, ValueError):
            skipped += 1
            continue

        note: Optional[str] = ev.get("note") or None
        ref: Optional[str] = ev.get("ref") or None

        if usd_cents <= 0:
            skipped += 1
            continue

        # (user_id, ref) idempotency
        if await _ref_exists(db, user_id=user_id, ref=ref):
            skipped += 1
            continue

        amount_usd = usd_cents / 100.0

        # ledger + wallet balance update (atomic, inside its own transaction)
        ledger_id = await add_earning(
            session=db,
            user_id=user_id,
            amount_usd=amount_usd,
            note=note or "SYNC_EARN",
            request_id=ref or "",
        )
        accepted += 1

        # 🔔 Real-time push to WebSocket listeners (if Redis is available)
        await publish_user_update(
            user_id,
            {
                "type": "earn_synced",
                "amount_usd": amount_usd,
                "ref": ref,
                "ledger_id": ledger_id,
                "note": note or "",
            },
        )

    return {"accepted": accepted, "skipped": skipped}
