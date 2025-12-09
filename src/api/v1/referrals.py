"""
Referral System - Invite friends and earn bonuses
"""
from datetime import datetime
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import secrets

from src.db.session import get_db
from src.db.models import Referral, User, Transaction, TransactionTypeEnum, TransactionStatusEnum
from src.core.deps import get_current_active_user


router = APIRouter()


class ReferralStats(BaseModel):
    total_referrals: int
    successful_referrals: int
    total_earned_usd: float
    referral_code: str


@router.get("/my-code")
async def get_referral_code(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's referral code
    """
    # Check if user already has a referral code
    result = await db.execute(
        select(Referral).where(
            Referral.referrer_id == current_user.id,
            Referral.referred_user_id == None  # This is the code record
        )
    )
    referral_code_record = result.scalar_one_or_none()
    
    if not referral_code_record:
        # Generate new referral code
        referral_code = f"DL{secrets.token_hex(4).upper()}"
        
        referral_code_record = Referral(
            id=uuid4(),
            referrer_id=current_user.id,
            referral_code=referral_code,
            created_at=datetime.utcnow(),
        )
        db.add(referral_code_record)
        await db.commit()
    
    return {
        "referral_code": referral_code_record.referral_code,
        "referral_link": f"https://dignilife.app/register?ref={referral_code_record.referral_code}",
        "bonus_per_referral": "$5 when friend completes 10 tasks"
    }


@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get referral statistics
    """
    # Get referral code
    code_result = await db.execute(
        select(Referral).where(
            Referral.referrer_id == current_user.id,
            Referral.referred_user_id == None
        )
    )
    code_record = code_result.scalar_one_or_none()
    referral_code = code_record.referral_code if code_record else "N/A"
    
    # Count total referrals
    total_result = await db.execute(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == current_user.id,
            Referral.referred_user_id != None
        )
    )
    total_referrals = total_result.scalar() or 0
    
    # Count successful referrals (bonus earned)
    successful_result = await db.execute(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == current_user.id,
            Referral.bonus_earned == True
        )
    )
    successful_referrals = successful_result.scalar() or 0
    
    # Calculate total earned
    earned_result = await db.execute(
        select(func.sum(Referral.bonus_amount_usd)).where(
            Referral.referrer_id == current_user.id,
            Referral.bonus_earned == True
        )
    )
    total_earned = earned_result.scalar() or 0
    
    return ReferralStats(
        total_referrals=total_referrals,
        successful_referrals=successful_referrals,
        total_earned_usd=float(total_earned),
        referral_code=referral_code,
    )


@router.get("/my-referrals")
async def get_my_referrals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of referred users
    """
    result = await db.execute(
        select(Referral, User)
        .join(User, Referral.referred_user_id == User.id)
        .where(
            Referral.referrer_id == current_user.id,
            Referral.referred_user_id != None
        )
        .order_by(Referral.created_at.desc())
    )
    
    referrals = []
    for referral, user in result:
        referrals.append({
            "user_name": user.full_name,
            "joined_at": referral.created_at,
            "bonus_earned": referral.bonus_earned,
            "bonus_amount_usd": float(referral.bonus_amount_usd) if referral.bonus_earned else 0,
            "status": "Bonus Earned" if referral.bonus_earned else "In Progress"
        })
    
    return referrals


@router.post("/apply-code")
async def apply_referral_code(
    referral_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Apply a referral code (for new users)
    """
    # Check if user already used a referral code
    existing_result = await db.execute(
        select(Referral).where(Referral.referred_user_id == current_user.id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already used a referral code"
        )
    
    # Find referral code
    code_result = await db.execute(
        select(Referral).where(
            Referral.referral_code == referral_code.upper(),
            Referral.referred_user_id == None
        )
    )
    code_record = code_result.scalar_one_or_none()
    
    if not code_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid referral code"
        )
    
    # Can't use own referral code
    if code_record.referrer_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot use your own referral code"
        )
    
    # Create referral record
    referral = Referral(
        id=uuid4(),
        referrer_id=code_record.referrer_id,
        referred_user_id=current_user.id,
        referral_code=referral_code.upper(),
        bonus_earned=False,
        created_at=datetime.utcnow(),
    )
    
    db.add(referral)
    await db.commit()
    
    return {
        "message": "Referral code applied successfully!",
        "bonus_info": "Complete 10 tasks to earn $5 bonus for you and your referrer!"
    }