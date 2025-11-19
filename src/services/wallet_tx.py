# src/services/wallet_tx.py
from __future__ import annotations

import json
from uuid import uuid4
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

def _ensure_wallet_row(db: Session, user_id: str) -> None:
    """
    Make sure `wallets` table has a row for this user.
    Schema (suggested):
      wallets(user_id TEXT PRIMARY KEY, balance_usd REAL NOT NULL DEFAULT 0, updated_at TEXT)
    """
    db.execute(
        text(
            """
            INSERT INTO wallets (user_id, balance_usd, updated_at)
            VALUES (:uid, 0.0, datetime('now'))
            ON CONFLICT(user_id) DO NOTHING
            """
        ),
        {"uid": user_id},
    )


def post_earn_credit(
    db: Session,
    user_id: str,
    amount_usd: float,
    ref_type: str,
    ref_id: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a credit transaction and update wallet balance atomically.
    Requires schema:
      wallet_tx(id TEXT PRIMARY KEY, user_id TEXT, amount_usd REAL, tx_type TEXT,
                ref_type TEXT, ref_id TEXT, meta_json TEXT, created_at TEXT)
      wallets(user_id TEXT PRIMARY KEY, balance_usd REAL, updated_at TEXT)
    """
    tx_id = str(uuid4())
    meta_json = json.dumps(meta or {}, ensure_ascii=False)

    _ensure_wallet_row(db, user_id)

    # insert transaction
    db.execute(
        text(
            """
            INSERT INTO wallet_tx
                (id, user_id, amount_usd, tx_type, ref_type, ref_id, meta_json, created_at)
            VALUES
                (:id, :uid, :amt, 'credit', :rtype, :rid, :meta, datetime('now'))
            """
        ),
        {
            "id": tx_id,
            "uid": user_id,
            "amt": float(amount_usd or 0.0),
            "rtype": ref_type,
            "rid": ref_id,
            "meta": meta_json,
        },
    )

    # upsert-add to wallets
    db.execute(
        text(
            """
            INSERT INTO wallets (user_id, balance_usd, updated_at)
            VALUES (:uid, :amt, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE
                SET balance_usd = balance_usd + excluded.balance_usd,
                    updated_at = excluded.updated_at
            """
        ),
        {"uid": user_id, "amt": float(amount_usd or 0.0)},
    )

    db.commit()
    return tx_id


def get_wallet_summary(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Basic wallet snapshot for a user.
    """
    _ensure_wallet_row(db, user_id)

    bal = db.execute(
        text("SELECT balance_usd FROM wallets WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    bal = float(bal or 0.0)

    last_tx = (
        db.execute(
            text(
                """
                SELECT created_at, amount_usd, tx_type, ref_type, ref_id
                FROM wallet_tx
                WHERE user_id = :uid
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"uid": user_id},
        )
        .mappings()
        .fetchone()
    )

    today = db.execute(
        text(
            """
            SELECT COALESCE(SUM(amount_usd), 0.0)
            FROM wallet_tx
            WHERE user_id = :uid
              AND tx_type = 'credit'
              AND date(created_at) = date('now')
            """
        ),
        {"uid": user_id},
    ).scalar()
    today = float(today or 0.0)

    return {
        "user_id": user_id,
        "balance_usd": bal,
        "today_credited_usd": today,
        "last_tx": dict(last_tx) if last_tx else None,
    }

ADMIN_UID = "admin"  # or load from config

async def credit_admin(session: AsyncSession, amount: float, ref: str, note: str = "") -> None:
    # Ledger insert
    await session.execute(
        text("""INSERT INTO wallet_ledger(user_id, amount_usd, ref, note)
                VALUES (:uid, :amt, :ref, :note)"""),
        {"uid": ADMIN_UID, "amt": amount, "ref": ref, "note": note},
    )
    # Balance update (idempotent UPSERT style)
    await session.execute(
        text("""UPDATE wallet_balances SET balance_usd = balance_usd + :amt
                WHERE user_id = :uid"""),
        {"uid": ADMIN_UID, "amt": amount},
    )
    await session.commit()
    
