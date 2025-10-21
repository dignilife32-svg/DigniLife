# src/sync/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_session
from .models import PushIn, PushOut
from .service import sync_earn_events

router = APIRouter(prefix="/sync", tags=["sync"])


def _require_user(x_user_id: Optional[str] = Header(default=None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="x-user-id header is required")
    return x_user_id


@router.post("/push", response_model=PushOut)
async def push_events(
    payload: PushIn,
    user_id: str = Depends(_require_user),
    db: AsyncSession = Depends(get_session),
):
    stats = await sync_earn_events(db, user_id=user_id, events=[e.dict() for e in payload.earn])
    return PushOut(**stats)
