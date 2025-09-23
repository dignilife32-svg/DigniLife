# src/classic/router.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.classic import service as svc

router = APIRouter(prefix="/earn/classic", tags=["classic"])


def current_user_id(x_user_id: Optional[str] = Header(default=None)) -> str:
    """Require x-user-id header."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-user-id header is required",
        )
    return x_user_id


@router.get("/levels")
def list_levels(db: Session = Depends(get_db)):
    levels = svc.list_levels(db)
    return {"levels": levels}


@router.post("/start")
def start(
    level: str,
    minutes: int = 30,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    result = svc.start_level(db, user_id=user_id, level=level, minutes=minutes)
    return result
