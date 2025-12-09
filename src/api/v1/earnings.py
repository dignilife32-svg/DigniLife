"""
Earning History & Stats Endpoints
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.db.session import get_db
from src.db.models import EarningHistory, DailyEarningStat, User
from src.core.deps import get_current_active_user
from pydantic import BaseModel


router = APIRouter()


class EarningRecord(BaseModel):
    id: str
    base_reward: float
    quality_bonus: float
    speed_bonus: float
    streak_bonus: float
    tier_multiplier: float
    total_earned: float
    earned_at: datetime
    
    class Config:
        from_attributes = True


class DailyStats(BaseModel):
    date: datetime
    tasks_completed: int
    total_earned_usd: float
    avg_quality_score: Optional[float] = None


@router.get("/history", response_model=List[EarningRecord])
async def get_earning_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's earning history
    """
    result = await db.execute(
        select(EarningHistory)
        .where(EarningHistory.user_id == current_user.id)
        .order_by(EarningHistory.earned_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    earnings = result.scalars().all()
    return [EarningRecord(id=str(e.id), **e.__dict__) for e in earnings]


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_earnings(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get daily earning statistics
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(DailyEarningStat)
        .where(
            DailyEarningStat.user_id == current_user.id,
            DailyEarningStat.date >= start_date
        )
        .order_by(DailyEarningStat.date.desc())
    )
    
    stats = result.scalars().all()
    return stats


@router.get("/streak")
async def get_streak_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's streak information
    """
    return {
        "current_streak_days": current_user.current_streak_days,
        "longest_streak_days": current_user.longest_streak_days,
        "last_task_completed": current_user.last_task_completed_date,
        "streak_bonus_percentage": min(current_user.current_streak_days, 30)
    }


@router.get("/summary")
async def get_earning_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get earning summary
    """
    # Today's earnings
    today = datetime.utcnow().date()
    today_result = await db.execute(
        select(func.sum(EarningHistory.total_earned))
        .where(
            EarningHistory.user_id == current_user.id,
            func.date(EarningHistory.earned_at) == today
        )
    )
    today_earnings = today_result.scalar() or 0
    
    # This week's earnings
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_result = await db.execute(
        select(func.sum(EarningHistory.total_earned))
        .where(
            EarningHistory.user_id == current_user.id,
            EarningHistory.earned_at >= week_ago
        )
    )
    week_earnings = week_result.scalar() or 0
    
    # This month's earnings
    month_ago = datetime.utcnow() - timedelta(days=30)
    month_result = await db.execute(
        select(func.sum(EarningHistory.total_earned))
        .where(
            EarningHistory.user_id == current_user.id,
            EarningHistory.earned_at >= month_ago
        )
    )
    month_earnings = month_result.scalar() or 0
    
    return {
        "today_usd": float(today_earnings),
        "this_week_usd": float(week_earnings),
        "this_month_usd": float(month_earnings),
        "total_lifetime_usd": float(current_user.total_earnings_usd),
        "available_balance_usd": float(current_user.available_balance_usd),
        "pending_balance_usd": float(current_user.pending_balance_usd),
    }