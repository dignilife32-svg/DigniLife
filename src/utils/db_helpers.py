# src/utils/db_helpers.py
from __future__ import annotations
from sqlite3 import Connection
from typing import Any, Iterable, Mapping, Sequence, Tuple
from src.wallet.models import WalletLedger
from src.wallet.models import LedgerType
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

# လုံးဝအလွယ်သုံးချင်လို့ types ကို လွတ်လပ်အောင် ထားရင် Pylance Errors မလာအောင် Any သုံး
def exec(db: Connection, sql: str, params: Iterable[Any] | Mapping[str, Any] = ()) -> None:
    # params တကယ် list/tuple မဟုတ်ရင် tuple ပြောင်း
    if not isinstance(params, (tuple, list, dict)):
        params = tuple([params])
    db.execute(sql, params if not isinstance(params, list) else tuple(params))
    db.commit()

def exec1(db: Connection, sql: str, params: Iterable[Any] | Mapping[str, Any] = ()) -> Tuple | None:
    if not isinstance(params, (tuple, list, dict)):
        params = tuple([params])
    cur = db.execute(sql, params if not isinstance(params, list) else tuple(params))
    return cur.fetchone()

def qi(n: int) -> str:
    """quick placeholders: qi(3) -> '?, ?, ?'"""
    return ", ".join(["?"] * n)

async def commit_ledger_entry(
    db: AsyncSession,
    user_id: str,
    type_: LedgerType,
    amount_usd,
    ref_task_code: str = "",
    meta: str | None = None,
) -> int:
    """
    Universal helper: insert 1 WalletLedger row safely.
    """
    entry = WalletLedger(
        user_id=user_id,
        type=type_,
        amount_usd=amount_usd,
        ref_task_code=ref_task_code[:64],
        meta=meta,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry.id
