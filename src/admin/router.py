# src/admin/router.py
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.admin.models import AdminTaskUpsert, AdminTaskOut, LedgerRow

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    want = os.getenv("ADMIN_KEY", "letmein")
    if not x_admin_key or x_admin_key != want:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin key required")


@router.get("/health")
async def health(_: None = Depends(_require_admin)):
    return {"ok": True}


# ------- TASKS -------

@router.get("/daily/tasks", response_model=List[AdminTaskOut])
async def list_tasks(
    _: None = Depends(_require_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    q = text("""
        SELECT code, category, display_value_usd, expected_time_sec,
               user_prompt, description, is_active
        FROM daily_tasks
        ORDER BY code ASC
        LIMIT :limit OFFSET :offset
    """)
    rows = (await db.execute(q, {"limit": limit, "offset": offset})).mappings().all()
    return [AdminTaskOut(**dict(r)) for r in rows]


@router.post("/daily/task", response_model=AdminTaskOut)
async def upsert_task(
    payload: AdminTaskUpsert,
    _: None = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
):
    # upsert (SQLite-friendly)
    q = text("""
        INSERT INTO daily_tasks (code, category, display_value_usd, expected_time_sec,
                                 user_prompt, description, is_active)
        VALUES (:code, :category, :val, :secs, :prompt, :desc, :active)
        ON CONFLICT(code) DO UPDATE SET
            category=excluded.category,
            display_value_usd=excluded.display_value_usd,
            expected_time_sec=excluded.expected_time_sec,
            user_prompt=excluded.user_prompt,
            description=excluded.description,
            is_active=excluded.is_active
    """)
    await db.execute(q, {
        "code": payload.code, "category": payload.category,
        "val": payload.display_value_usd, "secs": payload.expected_time_sec,
        "prompt": payload.user_prompt, "desc": payload.description,
        "active": 1 if payload.is_active else 0,
    })
    # return row
    sel = text("""
        SELECT code, category, display_value_usd, expected_time_sec,
               user_prompt, description, is_active
        FROM daily_tasks WHERE code = :code
    """)
    row = (await db.execute(sel, {"code": payload.code})).mappings().one()
    return AdminTaskOut(**dict(row))


@router.patch("/daily/task/{code}/active", response_model=dict)
async def set_task_active(
    code: str,
    is_active: bool = Query(...),
    _: None = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
):
    q = text("UPDATE daily_tasks SET is_active = :a WHERE code = :c")
    res = await db.execute(q, {"a": 1 if is_active else 0, "c": code})
    return {"updated": res.rowcount or 0}


# ------- LEDGER -------

@router.get("/wallet/ledger", response_model=List[LedgerRow])
async def wallet_ledger(
    user_id: str = Query(..., min_length=1),
    _: None = Depends(_require_admin),
    db: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = text("""
        SELECT id, user_id, amount_usd, COALESCE(ref,'') as ref,
               COALESCE(note,'') as note, created_at
        FROM wallet_ledger
        WHERE user_id = :u
        ORDER BY id DESC
        LIMIT :l OFFSET :o
    """)
    rows = (await db.execute(q, {"u": user_id, "l": limit, "o": offset})).mappings().all()
    return [LedgerRow(**dict(r)) for r in rows]
