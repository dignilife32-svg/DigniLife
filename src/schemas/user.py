"""
User Pydantic Schemas - COMPLETE
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from src.db.models import SubscriptionTier, UserRole


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(BaseModel):
    """Register with Email + Face (Password OPTIONAL)"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=100)  # OPTIONAL!
    face_image_base64: str  # REQUIRED for registration


class UserUpdate(BaseModel):
    """Update user profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    preferred_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    preferred_language: Optional[str] = Field(None, min_length=2, max_length=5)
    timezone: Optional[str] = Field(None, max_length=50)


class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole
    subscription_tier: SubscriptionTier
    is_active: bool
    is_verified: bool
    kyc_verified: bool
    total_earnings_usd: float
    available_balance_usd: float
    pending_balance_usd: float
    preferred_currency: str
    current_streak_days: int
    longest_streak_days: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics"""
    total_earnings_usd: float
    available_balance_usd: float
    pending_balance_usd: float
    lifetime_withdrawals_usd: float
    tasks_completed: int
    current_streak_days: int
    longest_streak_days: int


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class UserLogin(BaseModel):
    """Login with Face FIRST"""
    face_image_base64: str  # PRIMARY login method
    email: Optional[EmailStr] = None  # Fallback if face fails
    password: Optional[str] = None  # Fallback if face fails


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload"""
    sub: Optional[str] = None
    exp: Optional[int] = None