# src/db/models.py
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    Numeric,
    UniqueConstraint,
    Index,
    ForeignKey,
    func, Column,
    Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    points = Column(Integer, nullable=False, default=0)
    reason = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    inviter_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    invitee_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    status = Column(String(16), nullable=False, default="pending")  # pending/completed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class WalletTxn(Base):
    __tablename__ = "wallet_txn"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # + / - amount in USD or cents (choose based on your system)
    amount_usd = Column(Float, nullable=False)

    kind = Column(
        String(32),
        nullable=False,
    )  # "earn", "adjust", "withdraw_reserve", "withdraw_commit", "bonus"

    ref = Column(String(64), nullable=True)  # withdrawal_id, task_id, admin note etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
# --------------------------------------------------------------------------
# USERS + AUTH
# --------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    # UUID style string id (auth/service.py နဲ့ကိုက်အောင်)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    device_fp: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    identity_tier: Mapped[str] = mapped_column(String(32), default="FACE_ONLY")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sessions: Mapped[List["AuthSession"]] = relationship(
        "AuthSession", back_populates="user", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = {"extend_existing": True}

    # token ကို id အနေနဲ့သုံးတယ် (auth/service.py မှာ)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id"), index=True, nullable=False
    )
    device_fp: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="sessions", lazy="raise")

    def __repr__(self) -> str:
        return f"<AuthSession user_id={self.user_id!r} id={self.id!r}>"


class FaceProfile(Base):
    __tablename__ = "face_profiles"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id"), index=True, nullable=False
    )

    # embedding ကို text/json style အနေနဲ့ သိမ်း
    face_vec: Mapped[Optional[str]] = mapped_column(Text)
    liveness: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", lazy="raise")

    def __repr__(self) -> str:
        return f"<FaceProfile user={self.user_id!r} id={self.id!r}>"


class KycVerification(Base):
    __tablename__ = "kyc_verifications"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id"), index=True, nullable=False
    )

    tier: Mapped[str] = mapped_column(String(32), default="FACE_ONLY")
    ai_risk_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    state: Mapped[str] = mapped_column(String(32), default="PENDING")
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    evidence_json: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship("User", lazy="raise")

    def __repr__(self) -> str:
        return f"<KycVerification user_id={self.user_id!r} tier={self.tier!r} state={self.state!r}>"


# --------------------------------------------------------------------------
# DAILY TASKS (auto-injector / planner)
# --------------------------------------------------------------------------


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    __table_args__ = (
        UniqueConstraint("date", "code", name="uq_daily_tasks_date_code"),
        Index("ix_daily_tasks_date", "date"),
        Index("ix_daily_tasks_code", "code"),
        Index("ix_daily_tasks_category", "category"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)

    display_value_usd: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))

    expected_time_sec: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="60"
    )
    expected_confidence: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="66"
    )

    usd_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    user_prompt: Mapped[str] = mapped_column(Text, default="")
    user_actions_json: Mapped[Optional[str]] = mapped_column(Text, default="")

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    def __repr__(self) -> str:
        return f"<DailyTask {self.date} {self.code} ({self.category})>"


# --------------------------------------------------------------------------
# EARN DAILY SESSION
# --------------------------------------------------------------------------


class EarnDailySession(Base):
    __tablename__ = "earn_daily_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), default="ok")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EarnDailySession user={self.user_id!r} amount_usd={self.amount_usd}>"


# --------------------------------------------------------------------------
# WITHDRAW REQUESTS
# --------------------------------------------------------------------------


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending|approved|rejected
    ref: Mapped[Optional[str]] = mapped_column(String(64), index=True, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<WithdrawRequest user={self.user_id!r} "
            f"amount_usd={self.amount_usd} status={self.status}>"
        )


class LedgerType(str, Enum):
    EARN = "earn"
    BONUS = "bonus"
    ADJUST = "adjust"
    WITHDRAW = "withdraw"
    SYSTEM = "system"
    RESERVE = "reserve"


# --------------------------------------------------------------------------
# WALLET LEDGER
# --------------------------------------------------------------------------


class WalletLedger(Base):
    __tablename__ = "wallet_ledger"
    __table_args__ = (
        Index("ix_wallet_ledger_user_id", "user_id"),
        Index("ix_wallet_ledger_ref", "ref"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(String(64), nullable=False)

    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    type: Mapped[str] = mapped_column(String(32), default="earn")

    note: Mapped[Optional[str]] = mapped_column(Text)

    ref: Mapped[Optional[str]] = mapped_column(String(64))

    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # optional view-only relation back to users
    user: Mapped[Optional[User]] = relationship(
        "User",
        primaryjoin="foreign(WalletLedger.user_id) == User.id",
        viewonly=True,
        lazy="raise",
    )

    def __repr__(self) -> str:
        return (
            f"<WalletLedger user={self.user_id!r} amount_usd={self.amount_usd} "
            f"type={self.type!r} ref={self.ref!r}>"
        )


# --------------------------------------------------------------------------
# Backward-compat aliases
# --------------------------------------------------------------------------

Faceprofile = FaceProfile
EarnDailySessionModel = EarnDailySession
WithdrawRequestModel = WithdrawRequest

__all__ = [
    "User",
    "AuthSession",
    "FaceProfile",
    "Faceprofile",
    "KycVerification",
    "DailyTask",
    "EarnDailySession",
    "EarnDailySessionModel",
    "WithdrawRequest",
    "WithdrawRequestModel",
    "LedgerType",
    "WalletLedger",
]

from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
