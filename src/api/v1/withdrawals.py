"""
Withdrawal Management Endpoints
"""
from datetime import datetime
from uuid import uuid4
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.db.models import (
    Withdrawal, WithdrawalFee, Transaction, FXRate, User,
    TransactionTypeEnum, TransactionStatusEnum
)
from src.schemas.wallet import (
    WithdrawalRequest, WithdrawalResponse, WithdrawalFeePreview
)
from src.core.deps import get_current_active_user
from src.api.v1.auth import FaceLivenessDetector, FaceLivenessLog
from src.core.earning_engine import WithdrawalFeeCalculator


router = APIRouter()


@router.post("/preview-fee", response_model=WithdrawalFeePreview)
async def preview_withdrawal_fee(
    amount_usd: float,
    currency_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview withdrawal fee before requesting
    """
    if amount_usd <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    if amount_usd > float(current_user.available_balance_usd):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Calculate fee
    fee_calc = WithdrawalFeeCalculator.calculate_fee(
        gross_amount=Decimal(str(amount_usd)),
        user_tier=current_user.subscription_tier,
    )
    
    # Get exchange rate
    exchange_rate = 1.0
    if currency_code != "USD":
        fx_result = await db.execute(
            select(FXRate)
            .where(
                FXRate.from_currency == "USD",
                FXRate.to_currency == currency_code.upper()
            )
            .order_by(FXRate.created_at.desc())
            .limit(1)
        )
        fx_rate = fx_result.scalar_one_or_none()
        if fx_rate:
            exchange_rate = float(fx_rate.rate)
    
    amount_local = float(fee_calc["net_amount"]) * exchange_rate
    
    return WithdrawalFeePreview(
        gross_amount=float(fee_calc["gross_amount"]),
        fee_amount=float(fee_calc["fee_amount"]),
        fee_percentage=float(fee_calc["fee_percentage"]),
        net_amount=float(fee_calc["net_amount"]),
        tier=fee_calc["tier"],
        amount_local=amount_local,
        currency_code=currency_code.upper(),
        exchange_rate=exchange_rate,
    )


@router.post("/request", response_model=WithdrawalResponse)
async def request_withdrawal(
    withdrawal_request: WithdrawalRequest,
    face_verification: str,  # NEW: Face image for verification
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Request withdrawal - FACE VERIFICATION REQUIRED!
    """
    # STEP 1: Verify face FIRST before allowing withdrawal
    liveness_result = await FaceLivenessDetector.verify_liveness(
        image_data=face_verification,
        user_id=current_user.id,
    )
    
    if not FaceLivenessDetector.validate_liveness_result(liveness_result):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Face verification required for withdrawal. Please verify your face."
        )
    
    # Log face verification for withdrawal
    face_log = FaceLivenessLog(
        id=uuid4(),
        user_id=current_user.id,
        is_live=True,
        confidence_score=liveness_result.get("confidence", 95),
        detection_details={
            **liveness_result.get("details", {}),
            "purpose": "withdrawal_verification",
            "amount_usd": withdrawal_request.amount_usd,
        },
        created_at=datetime.utcnow(),
    )
    db.add(face_log)

    """
    Request a withdrawal (with auto-cut fee)
    """
    # Validate amount
    if withdrawal_request.amount_usd <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    if withdrawal_request.amount_usd > float(current_user.available_balance_usd):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Calculate fee (AUTO-CUT based on tier)
    fee_calc = WithdrawalFeeCalculator.calculate_fee(
        gross_amount=Decimal(str(withdrawal_request.amount_usd)),
        user_tier=current_user.subscription_tier,
    )
    
    # Get exchange rate
    exchange_rate = 1.0
    if withdrawal_request.currency_code != "USD":
        fx_result = await db.execute(
            select(FXRate)
            .where(
                FXRate.from_currency == "USD",
                FXRate.to_currency == withdrawal_request.currency_code.upper()
            )
            .order_by(FXRate.created_at.desc())
            .limit(1)
        )
        fx_rate = fx_result.scalar_one_or_none()
        if fx_rate:
            exchange_rate = float(fx_rate.rate)
    
    amount_local = float(fee_calc["net_amount"]) * exchange_rate
    
    # Create withdrawal
    withdrawal = Withdrawal(
        id=uuid4(),
        user_id=current_user.id,
        gross_amount_usd=float(fee_calc["gross_amount"]),
        fee_amount_usd=float(fee_calc["fee_amount"]),
        net_amount_usd=float(fee_calc["net_amount"]),
        amount_local=amount_local,
        currency_code=withdrawal_request.currency_code.upper(),
        exchange_rate=exchange_rate,
        payout_method=withdrawal_request.payout_method,
        payout_details=withdrawal_request.payout_details,
        status=TransactionStatusEnum.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(withdrawal)
    
    # Create withdrawal fee record
    fee_record = WithdrawalFee(
        id=uuid4(),
        withdrawal_id=withdrawal.id,
        user_id=current_user.id,
        subscription_tier=current_user.subscription_tier,
        fee_percentage=float(fee_calc["fee_percentage"]),
        fee_amount_usd=float(fee_calc["fee_amount"]),
        created_at=datetime.utcnow(),
    )
    db.add(fee_record)
    
    # Create transaction record
    transaction = Transaction(
        id=uuid4(),
        user_id=current_user.id,
        amount_usd=withdrawal_request.amount_usd,
        transaction_type=TransactionTypeEnum.WITHDRAWAL,
        status=TransactionStatusEnum.PENDING,
        reference_id=str(withdrawal.id),
        trans_metadata={
            "withdrawal_id": str(withdrawal.id),
            "payout_method": withdrawal_request.payout_method.value,
            "currency_code": withdrawal_request.currency_code.upper(),
            "fee_amount": float(fee_calc["fee_amount"]),
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(transaction)
    
    # Deduct from user balance
    current_user.available_balance_usd -= withdrawal_request.amount_usd
    current_user.lifetime_withdrawals_usd += float(fee_calc["net_amount"])
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(withdrawal)
    
    return withdrawal


@router.get("/", response_model=List[WithdrawalResponse])
async def get_withdrawal_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get withdrawal history
    """
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.user_id == current_user.id)
        .order_by(Withdrawal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    withdrawals = result.scalars().all()
    return withdrawals


@router.get("/{withdrawal_id}", response_model=WithdrawalResponse)
async def get_withdrawal_status(
    withdrawal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get withdrawal status
    """
    result = await db.execute(
        select(Withdrawal)
        .where(
            Withdrawal.id == withdrawal_id,
            Withdrawal.user_id == current_user.id
        )
    )
    
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    return withdrawal


@router.get("/methods/available")
async def get_available_payout_methods(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available payout methods
    """
    from src.db.models import PayoutMethodEnum
    
    methods = [
        {
            "method": PayoutMethodEnum.WAVE_MONEY,
            "name": "Wave Money",
            "countries": ["MM"],
            "icon": "💸",
            "min_amount_usd": 5,
            "processing_time": "1-2 hours"
        },
        {
            "method": PayoutMethodEnum.KBZ_PAY,
            "name": "KBZ Pay",
            "countries": ["MM"],
            "icon": "🏦",
            "min_amount_usd": 5,
            "processing_time": "1-2 hours"
        },
        {
            "method": PayoutMethodEnum.CB_PAY,
            "name": "CB Pay",
            "countries": ["MM"],
            "icon": "💳",
            "min_amount_usd": 5,
            "processing_time": "1-2 hours"
        },
        {
            "method": PayoutMethodEnum.AYA_PAY,
            "name": "AYA Pay",
            "countries": ["MM"],
            "icon": "🏧",
            "min_amount_usd": 5,
            "processing_time": "1-2 hours"
        },
        {
            "method": PayoutMethodEnum.ONEPAY,
            "name": "OnePay",
            "countries": ["MM"],
            "icon": "💰",
            "min_amount_usd": 5,
            "processing_time": "1-2 hours"
        },
        {
            "method": PayoutMethodEnum.PAYPAL,
            "name": "PayPal",
            "countries": ["Global"],
            "icon": "🌐",
            "min_amount_usd": 10,
            "processing_time": "1-3 days"
        },
        {
            "method": PayoutMethodEnum.WESTERN_UNION,
            "name": "Western Union",
            "countries": ["Global"],
            "icon": "🌍",
            "min_amount_usd": 20,
            "processing_time": "1-2 days"
        },
        {
            "method": PayoutMethodEnum.MONEYGRAM,
            "name": "MoneyGram",
            "countries": ["Global"],
            "icon": "💵",
            "min_amount_usd": 20,
            "processing_time": "1-2 days"
        },
        {
            "method": PayoutMethodEnum.BANK_TRANSFER,
            "name": "Bank Transfer",
            "countries": ["Global"],
            "icon": "🏦",
            "min_amount_usd": 50,
            "processing_time": "3-5 days"
        },
    ]
    
    return {
        "methods": methods,
        "user_tier": current_user.subscription_tier,
        "fee_rate": {
            "free": "15%",
            "pro": "10%",
            "premium": "5%"
        }[current_user.subscription_tier.value]
    }