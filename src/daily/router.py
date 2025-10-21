# src/daily/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import Optional

from src.db.session import get_session, get_session
from src.db.models import DailyTask
from src.wallet.logic import add_earning
from .schemas import TaskOut, SubmitIn
from .service import list_tasks

router = APIRouter(prefix="/learn/daily", tags=["daily"])


def _require_user(x_user_id: Optional[str] = Header(default=None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="x-user-id header is required")
    return x_user_id


@router.get("/tasks", response_model=list[TaskOut])
async def get_tasks(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    rows = await list_tasks(db, limit=limit, offset=offset)
    return [TaskOut(**r) for r in rows]


@router.post("/submit")
async def submit_task(
    payload: SubmitIn,
    user_id: str = Depends(_require_user),
    db: AsyncSession = Depends(get_session),
):
    # write earning
    await add_earning(
        db,
        user_id=user_id,
        usd_cents=payload.usd_cents,
        note=f"{payload.note}:{payload.task_code}",
        ref=f"daily:{payload.task_code}",
    )
    return {"ok": True}


@router.get("/health/ok")
async def health_ok(db: AsyncSession = Depends(get_session)):
    await db.execute(text("SELECT 1"))
    return {"ok": True}

@router.get("/tasks/today")
async def get_today_tasks(session=Depends(get_session)):
    today = date.today()
    rows = (await session.execute(
        select(DailyTask).where(DailyTask.date==today)
    )).scalars().all()
    return [r.as_dict() for r in rows]
