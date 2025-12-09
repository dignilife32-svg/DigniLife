"""
User Management Endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.db.session import get_db
from src.db.models import User, Submission, SubmissionStatusEnum
from src.schemas.user import UserResponse, UserUpdate, UserStats
from src.core.deps import get_current_user, get_current_active_user


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile
    """
    # Update fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.preferred_currency is not None:
        current_user.preferred_currency = user_update.preferred_currency.upper()
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics
    """
    # Count completed tasks
    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            Submission.user_id == current_user.id,
            Submission.status == SubmissionStatusEnum.APPROVED
        )
    )
    tasks_completed = result.scalar() or 0
    
    return UserStats(
        total_earnings_usd=float(current_user.total_earnings_usd),
        available_balance_usd=float(current_user.available_balance_usd),
        pending_balance_usd=float(current_user.pending_balance_usd),
        lifetime_withdrawals_usd=float(current_user.lifetime_withdrawals_usd),
        tasks_completed=tasks_completed,
        current_streak_days=current_user.current_streak_days,
        longest_streak_days=current_user.longest_streak_days,
    )


@router.post("/me/upgrade-subscription")
async def upgrade_subscription(
    tier: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upgrade user subscription tier
    """
    from src.db.models import SubscriptionTier
    
    # Validate tier
    valid_tiers = {
        "pro": SubscriptionTier.PRO,
        "premium": SubscriptionTier.PREMIUM
    }
    
    if tier.lower() not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier"
        )
    
    new_tier = valid_tiers[tier.lower()]
    
    # Check if already at this tier or higher
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 1,
        SubscriptionTier.PREMIUM: 2
    }
    
    if tier_order[current_user.subscription_tier] >= tier_order[new_tier]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already at this tier or higher"
        )
    
    # Update subscription
    current_user.subscription_tier = new_tier
    current_user.subscription_started_at = datetime.utcnow()
    # Set expiry to 30 days from now (example)
    from datetime import timedelta
    current_user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "message": f"Successfully upgraded to {tier.upper()} tier",
        "subscription_tier": current_user.subscription_tier,
        "expires_at": current_user.subscription_expires_at
    }