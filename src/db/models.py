# src/db/models.py
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, Date, Numeric,
    UniqueConstraint, Index
)
from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # optional backref
    user: Mapped["User"] = relationship("User", backref="auth_sessions", lazy="raise")

    def __repr__(self) -> str:
        return f"<AuthSession user_id={self.user_id} token={self.token}>"
    
# ------------------------------------------------------------------------------
# USERS
# ------------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = ({ "extend_existing": True },)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # optional relationship (view-only; loose link used by ledger)
    wallet_ledger: Mapped[List["WalletLedger"]] = relationship(  # type: ignore
        back_populates="user", viewonly=True, lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

# ------------------------------------------------------------------------------
# DAILY TASKS  (auto-injector uses this)
# ------------------------------------------------------------------------------
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

    # Which day is this task valid for
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # short code / slug (unique per day via constraint above)
    code: Mapped[str] = mapped_column(String(64), nullable=False)

    # category (geo | voice | visual | feedback | engine | micro ...)
    category: Mapped[str] = mapped_column(String(32), nullable=False)

    # optional UI-only display USD (banners etc.)
    display_value_usd: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))

    # expected durations / confidence (planner hints)
    expected_time_sec: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")
    expected_confidence: Mapped[int] = mapped_column(Integer, nullable=False, server_default="66")

    # payout fields (AI uses this). keep in cents for precision.
    usd_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # user-facing prompt / optional actions json
    user_prompt: Mapped[str] = mapped_column(Text, default="")
    user_actions_json: Mapped[Optional[str]] = mapped_column(Text, default="")

    # feature flags
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")

    def __repr__(self) -> str:
        return f"<DailyTask {self.date} {self.code} ({self.category})>"

# ------------------------------------------------------------------------------
# FACE PROFILE (alias kept for old imports)
# ------------------------------------------------------------------------------
class FaceProfile(Base):
    __tablename__ = "face_profiles"
    __table_args__ = ({ "extend_existing": True },)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    meta: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FaceProfile user={self.user_id!r} id={self.id}>"

# ------------------------------------------------------------------------------
# EARN DAILY SESSION (simple audit)
# ------------------------------------------------------------------------------
class EarnDailySession(Base):
    __tablename__ = "earn_daily_sessions"
    __table_args__ = ({ "extend_existing": True },)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), default="ok")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EarnDailySession user={self.user_id!r} amount_usd={self.amount_usd}>"

# ------------------------------------------------------------------------------
# WITHDRAW REQUESTS (admin hybrid flow)
# ------------------------------------------------------------------------------
class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"
    __table_args__ = ({ "extend_existing": True },)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|approved|rejected
    ref: Mapped[Optional[str]] = mapped_column(String(64), index=True, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<WithdrawRequest user={self.user_id!r} amount_usd={self.amount_usd} status={self.status}>"

class LedgerType(str, Enum):
    EARN = "earn"
    BONUS ="bonus"
    ADJUST = "adjust"
    WITHDRAW = "withdraw"
    SYSTEMS = "systems"
    RESERVE = "reserve"

# ------------------------------------------------------------------------------
# WALLET LEDGER (single source of truth)
# ------------------------------------------------------------------------------
class WalletLedger(Base):
    __tablename__ = "wallet_ledger"
    __table_args__ = (
        Index("ix_wallet_ledger_user_id", "user_id"),
        Index("ix_wallet_ledger_ref", "ref"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # owner (keep str for admin_pool_user compatibility)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # + for credit / - for debit (decimal)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # "earn" | "bonus" | "withdraw" | "adjust" ...
    type: Mapped[str] = mapped_column(String(32), default="earn")

    note: Mapped[Optional[str]] = mapped_column(Text)

    # idempotency / traceability
    ref: Mapped[Optional[str]] = mapped_column(String(64))

    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # optional view-only relation back to users (loose join)
    user: Mapped[Optional[User]] = relationship(
        primaryjoin="foreign(WalletLedger.user_id) == cast(User.id, String)",
        viewonly=True,
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<WalletLedger user={self.user_id!r} amount_usd={self.amount_usd} type={self.type!r} ref={self.ref!r}>"

# ------------------------------------------------------------------------------
# Backward-compatibility aliases (old import names)
# ------------------------------------------------------------------------------
Faceprofile = FaceProfile
EarnDailySessionModel = EarnDailySession
WithdrawRequestModel = WithdrawRequest

__all__ = [
    "User",
    "DailyTask",
    "FaceProfile", "Faceprofile",
    "EarnDailySession", "EarnDailySessionModel",
    "WithdrawRequest", "WithdrawRequestModel",
    "WalletLedger",
]

# src/db/base.py (သို့) src/db/models.py တစ်ဖိုင်ထဲဆို
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
