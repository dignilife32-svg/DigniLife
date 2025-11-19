# src/utils/db_helpers.py
from __future__ import annotations
from sqlite3 import Connection
from typing import Any, Iterable, Mapping, Sequence, Tuple
from src.db.models import WalletLedger
from src.db.models import LedgerType
from sqlalchemy import text
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

async def q(db: AsyncSession, sql: str, **params):
    return await db.execute(text(sql), params)

async def get_tasks_stats(db: AsyncSession) -> dict:
    # TODO: real impl
    row = await q(db, "SELECT COUNT(*) AS n FROM daily_tasks")
    n = row.scalar_one()
    return {"daily_tasks": n}

async def fallback_log(db: AsyncSession, event: str, payload: dict | None = None):
    # TODO: real impl (simple audit trail)
    await q(db,
        "INSERT INTO audit_log(event, payload) VALUES (:e, :p)",
        e=event, p=str(payload or {}))
    
