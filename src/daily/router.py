from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.daily.service import DailyService  # ✅ သင့် project ထဲမှာရှိတဲ့ class ကို import

router = APIRouter(prefix="/earn/daily", tags=["daily-earn"])

SVC = DailyService()

# -------------------- Dependency --------------------
def current_user_id(
    x_user_id: Optional[str] = Header(default=None, convert_underscores=False)
) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required"
        )
    return str(x_user_id)

# -------------------- Schemas --------------------
class NextTaskResponse(BaseModel):
    bundle_id: str
    item: Dict[str, Any]
    expires_at: datetime

class SubmitBody(BaseModel):
    bundle_id: str = Field(..., description="ID of the bundle")
    item: Dict[str, Any] = Field(..., description="User submitted task")
    took_ms: Optional[int] = Field(default=None, ge=0)

class SubmitResponse(BaseModel):
    ok: bool
    points_awarded: float
    next: Optional[NextTaskResponse] = None

class SummaryResponse(BaseModel):
    date: str
    total_tasks: int
    total_reward_usd: float
    daily_average_usd: float

# -------------------- Routes --------------------
@router.get("/next", response_model=NextTaskResponse)
def get_next_task(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
):
    """
    Get the next task for the user.
    """
    bundle = SVC.start_bundle(user_id=user_id, minutes=5)

    if not bundle.items:
        raise HTTPException(status_code=404, detail="No task available.")

    return NextTaskResponse(
        bundle_id=bundle.id,
        item=bundle.items[0],
        expires_at=bundle.expire_at
    )


@router.post("/submit", response_model=SubmitResponse)
def submit_task(
    body: SubmitBody,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
):
    """
    Submit a completed task.
    """
    try:
        awarded = SVC.submit(user_id=user_id, bundle_id=body.bundle_id, item=body.item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    next_bundle = SVC.start_bundle(user_id=user_id, minutes=5)
    next_task = None
    if next_bundle.items:
        next_task = NextTaskResponse(
            bundle_id=next_bundle.id,
            item=next_bundle.items[0],
            expires_at=next_bundle.expire_at
        )

    return SubmitResponse(
        ok=True,
        points_awarded=float(awarded),
        next=next_task
    )


@router.get("/summary", response_model=SummaryResponse)
def get_daily_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
):
    """
    Get daily earning summary.
    """
    s = SVC.summary(user_id=user_id)

    return SummaryResponse(
        date=s.get("ym", datetime.utcnow().strftime("%Y-%m")),
        total_tasks=int(s.get("total_tasks", 0)),
        total_reward_usd=float(s.get("total_reward_usd", 0.0)),
        daily_average_usd=float(s.get("daily_average_usd", 0.0))
    )
