"""
DigniLife Platform - Complete Database Models
All 32 Tables - Production Ready
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4
import enum

from sqlalchemy import Boolean, Column, DateTime, String, Text, Integer, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


# ============================================================================
# ENUMS
# ============================================================================

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    PARTNER = "partner"
    NGO = "ngo"


class TaskTypeEnum(str, enum.Enum):
    IMAGE_LABELING = "image_labeling"
    TEXT_ANNOTATION = "text_annotation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VIDEO_REVIEW = "video_review"
    DATA_VALIDATION = "data_validation"
    CONTENT_MODERATION = "content_moderation"
    SURVEY = "survey"
    OTHER = "other"


class TaskDifficultyEnum(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class SubmissionStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class TransactionTypeEnum(str, enum.Enum):
    EARNING = "earning"
    WITHDRAWAL = "withdrawal"
    BONUS = "bonus"
    PENALTY = "penalty"
    REFUND = "refund"


class TransactionStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PayoutMethodEnum(str, enum.Enum):
    WAVE_MONEY = "wave_money"
    KBZ_PAY = "kbz_pay"
    CB_PAY = "cb_pay"
    AYA_PAY = "aya_pay"
    ONEPAY = "onepay"
    PAYPAL = "paypal"
    WESTERN_UNION = "western_union"
    MONEYGRAM = "moneygram"
    BANK_TRANSFER = "bank_transfer"


class AIProposalStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class TicketPriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatusEnum(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ============================================================================
# USER MODELS (6 tables)
# ============================================================================

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    face_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # NEW!
    face_embedding: Mapped[Optional[str]] = mapped_column(Text)  # Store face data for matching
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    role: Mapped[str] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    total_earnings_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    available_balance_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    pending_balance_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    lifetime_withdrawals_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    preferred_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kyc_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_task_completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    user_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserDevice(Base):
    __tablename__ = "user_devices"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    device_fingerprint: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255))
    device_type: Mapped[Optional[str]] = mapped_column(String(50))
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    location_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    block_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user_devices.id", ondelete="SET NULL"))
    
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    logged_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class LivenessVerification(Base):
    __tablename__ = "liveness_verifications"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_result: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BiometricVerification(Base):
    __tablename__ = "biometric_verifications"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_devices.id", ondelete="CASCADE"), nullable=False)
    verification_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_description: Mapped[Optional[str]] = mapped_column(Text)
    activity_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ============================================================================
# TASK MODELS (6 tables)
# ============================================================================

class TaskType(Base):
    __tablename__ = "task_types"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(SQLEnum(TaskTypeEnum), nullable=False)
    difficulty: Mapped[str] = mapped_column(SQLEnum(TaskDifficultyEnum), nullable=False)
    
    reward_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    expected_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    example_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    metadata_required: Mapped[Optional[dict]] = mapped_column(JSONB)
    validation_criteria: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    max_submissions: Mapped[int] = mapped_column(Integer, nullable=False)
    current_submissions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Submission(Base):
    __tablename__ = "submissions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum(SubmissionStatusEnum), default=SubmissionStatusEnum.PENDING, nullable=False)
    
    ai_validation_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    ai_validation_notes: Mapped[Optional[str]] = mapped_column(Text)
    ai_auto_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    human_review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    completion_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EarningHistory(Base):
    __tablename__ = "earning_history"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    
    base_reward: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quality_bonus: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    speed_bonus: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    streak_bonus: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tier_multiplier: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0, nullable=False)
    total_earned: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class DailyEarningStat(Base):
    __tablename__ = "daily_earning_stats"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    avg_quality_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# FINANCIAL MODELS (7 tables)
# ============================================================================

class Currency(Base):
    __tablename__ = "currencies"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FXRate(Base):
    __tablename__ = "fx_rates"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    from_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Wallet(Base):
    __tablename__ = "wallets"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    balance_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    pending_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(SQLEnum(TransactionTypeEnum), nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum(TransactionStatusEnum), default=TransactionStatusEnum.PENDING, nullable=False)
    
    reference_id: Mapped[Optional[str]] = mapped_column(String(255))
    trans_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    gross_amount_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    fee_amount_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    net_amount_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    amount_local: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    
    payout_method: Mapped[str] = mapped_column(SQLEnum(PayoutMethodEnum), nullable=False)
    payout_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    status: Mapped[str] = mapped_column(SQLEnum(TransactionStatusEnum), default=TransactionStatusEnum.PENDING, nullable=False)
    
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WithdrawalFee(Base):
    __tablename__ = "withdrawal_fees"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    withdrawal_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("withdrawals.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    subscription_tier: Mapped[str] = mapped_column(SQLEnum(SubscriptionTier), nullable=False)
    fee_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    fee_amount_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PayoutMethod(Base):
    __tablename__ = "payout_methods"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    method_type: Mapped[str] = mapped_column(SQLEnum(PayoutMethodEnum), nullable=False)
    method_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================================
# PARTNER & NGO MODELS (5 tables)
# ============================================================================

class Partner(Base):
    __tablename__ = "partners"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    api_key: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NGO(Base):
    __tablename__ = "ngos"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    mission: Mapped[Optional[str]] = mapped_column(Text)
    focus_areas: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    partner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    budget_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    spent_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    project_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NGOProject(Base):
    __tablename__ = "ngo_projects"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ngo_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    social_impact_goals: Mapped[Optional[dict]] = mapped_column(JSONB)
    budget_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    spent_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    beneficiaries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impact_metrics: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Sponsor(Base):
    __tablename__ = "sponsors"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512))
    website_url: Mapped[Optional[str]] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================================
# AI SYSTEM MODELS (7 tables)
# ============================================================================

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    context_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conversation_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIMessage(Base):
    __tablename__ = "ai_messages"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AIContextStore(Base):
    __tablename__ = "ai_context_store"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    context_type: Mapped[str] = mapped_column(String(100), nullable=False)
    context_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AILearningEvent(Base):
    __tablename__ = "ai_learning_events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ai_response: Mapped[dict] = mapped_column(JSONB, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    human_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_feedback: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AIProposal(Base):
    __tablename__ = "ai_proposals"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    proposal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    impact_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    status: Mapped[str] = mapped_column(SQLEnum(AIProposalStatusEnum), default=AIProposalStatusEnum.PENDING, nullable=False)
    
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIDecisionLog(Base):
    __tablename__ = "ai_decision_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    decision_made: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text)
    
    confidence_level: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    
    was_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class SystemHealthMetric(Base):
    __tablename__ = "system_health_metrics"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    metric_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ============================================================================
# SUPPORT MODELS (3 tables)
# ============================================================================

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    priority: Mapped[str] = mapped_column(SQLEnum(TicketPriorityEnum), default=TicketPriorityEnum.MEDIUM, nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum(TicketStatusEnum), default=TicketStatusEnum.OPEN, nullable=False)
    
    assigned_to: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    ai_handled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    ticket_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    admin_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    action_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    target_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    was_ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

# Add after AIProposal class, before the end of file

class ChatMessage(Base):
    """
    Chat messages between user and AI assistant
    Stores conversation history
    """
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    message = Column(Text, nullable=False)
    message_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.id} - {self.role}>"
    
class Referral(Base):
    """Referral system - users invite friends"""
    __tablename__ = "referrals"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    referrer_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    referral_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    bonus_earned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bonus_amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    bonus_paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class ResearchSponsor(Base):
    """Research sponsors - OpenAI, Anthropic, Google, etc."""
    __tablename__ = "research_sponsors"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_type: Mapped[str] = mapped_column(String(100), nullable=False)  # ai_research, tech_company, university
    
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    website_url: Mapped[Optional[str]] = mapped_column(String(512))
    logo_url: Mapped[Optional[str]] = mapped_column(String(512))
    
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    api_secret_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    total_budget_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    spent_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    sponsor_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SponsoredTask(Base):
    """Tasks sponsored by research companies"""
    __tablename__ = "sponsored_tasks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sponsor_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_sponsors.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_description: Mapped[Optional[str]] = mapped_column(Text)
    
    budget_allocated_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    budget_spent_usd: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    target_submissions: Mapped[int] = mapped_column(Integer, nullable=False)
    current_submissions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    research_purpose: Mapped[Optional[str]] = mapped_column(Text)
    data_usage_terms: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DataLicensingAgreement(Base):
    """Track data licensing agreements with sponsors"""
    __tablename__ = "data_licensing_agreements"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sponsor_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_sponsors.id", ondelete="CASCADE"), nullable=False, index=True)
    
    agreement_type: Mapped[str] = mapped_column(String(100), nullable=False)  # exclusive, non_exclusive, one_time
    license_scope: Mapped[str] = mapped_column(Text, nullable=False)
    
    price_usd: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    data_categories: Mapped[dict] = mapped_column(JSONB, nullable=False)
    usage_restrictions: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    signed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class FaceLivenessLog(Base):
    """Log of face liveness verification attempts"""
    __tablename__ = "face_liveness_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    detection_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class SupportTicketMessage(Base):
    """Messages in support tickets"""
    __tablename__ = "support_ticket_messages"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
