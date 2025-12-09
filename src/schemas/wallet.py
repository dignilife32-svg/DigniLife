"""
Wallet & Transaction Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from src.db.models import (
    TransactionTypeEnum, 
    TransactionStatusEnum,
    PayoutMethodEnum,
    SubscriptionTier
)


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance_usd: float
    pending_usd: float
    
    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    available_balance_usd: float
    pending_balance_usd: float
    total_earnings_usd: float
    lifetime_withdrawals_usd: float
    preferred_currency: str
    
    # Converted amounts
    available_balance_local: Optional[float] = None
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount_usd: float
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum
    reference_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Withdrawal schemas
class WithdrawalRequest(BaseModel):
    amount_usd: float = Field(..., gt=0)
    currency_code: str = Field(..., min_length=3, max_length=3)
    payout_method: PayoutMethodEnum
    payout_details: Dict[str, Any]
    face_verification_base64: str

class WithdrawalFeePreview(BaseModel):
    gross_amount: float
    fee_amount: float
    fee_percentage: float
    net_amount: float
    tier: str
    amount_local: float
    currency_code: str
    exchange_rate: float


class WithdrawalResponse(BaseModel):
    id: UUID
    user_id: UUID
    gross_amount_usd: float
    fee_amount_usd: float
    net_amount_usd: float
    amount_local: float
    currency_code: str
    payout_method: PayoutMethodEnum
    status: TransactionStatusEnum
    created_at: datetime
    
    class Config:
        from_attributes = True