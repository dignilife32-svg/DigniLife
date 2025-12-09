"""
Wallet Management Endpoints
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.db.models import Wallet, Transaction, User, Currency, FXRate
from src.schemas.wallet import BalanceResponse, TransactionResponse
from src.core.deps import get_current_active_user


router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's wallet balance with currency conversion
    """
    # Get latest FX rate for user's preferred currency
    exchange_rate = 1.0
    if current_user.preferred_currency != "USD":
        fx_result = await db.execute(
            select(FXRate)
            .where(
                FXRate.from_currency == "USD",
                FXRate.to_currency == current_user.preferred_currency
            )
            .order_by(FXRate.created_at.desc())
            .limit(1)
        )
        fx_rate = fx_result.scalar_one_or_none()
        if fx_rate:
            exchange_rate = float(fx_rate.rate)
    
    # Calculate converted amounts
    available_local = float(current_user.available_balance_usd) * exchange_rate
    
    return BalanceResponse(
        available_balance_usd=float(current_user.available_balance_usd),
        pending_balance_usd=float(current_user.pending_balance_usd),
        total_earnings_usd=float(current_user.total_earnings_usd),
        lifetime_withdrawals_usd=float(current_user.lifetime_withdrawals_usd),
        preferred_currency=current_user.preferred_currency,
        available_balance_local=available_local,
        currency_code=current_user.preferred_currency,
        exchange_rate=exchange_rate,
    )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get transaction history
    """
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    transactions = result.scalars().all()
    return transactions


@router.get("/convert")
async def convert_currency(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = Query(..., min_length=3, max_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Convert currency amount
    """
    if from_currency == to_currency:
        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": amount,
            "exchange_rate": 1.0
        }
    
    # Get FX rate
    result = await db.execute(
        select(FXRate)
        .where(
            FXRate.from_currency == from_currency.upper(),
            FXRate.to_currency == to_currency.upper()
        )
        .order_by(FXRate.created_at.desc())
        .limit(1)
    )
    
    fx_rate = result.scalar_one_or_none()
    
    if not fx_rate:
        # Try reverse rate
        reverse_result = await db.execute(
            select(FXRate)
            .where(
                FXRate.from_currency == to_currency.upper(),
                FXRate.to_currency == from_currency.upper()
            )
            .order_by(FXRate.created_at.desc())
            .limit(1)
        )
        reverse_rate = reverse_result.scalar_one_or_none()
        
        if reverse_rate:
            exchange_rate = 1.0 / float(reverse_rate.rate)
        else:
            exchange_rate = 1.0  # Fallback
    else:
        exchange_rate = float(fx_rate.rate)
    
    converted_amount = amount * exchange_rate
    
    return {
        "amount": amount,
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "converted_amount": converted_amount,
        "exchange_rate": exchange_rate
    }