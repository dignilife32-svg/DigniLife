from datetime import datetime
from sqlalchemy.orm import  Mapped, mapped_column
from src.db.session import Base
from sqlalchemy import String, Float, DateTime, Enum, Integer, Index, UniqueConstraint
import enum



class LedgerType(str, enum.Enum):
    EARN_RESERVE   = "EARN_RESERVE"
    EARN_COMMIT    = "EARN_COMMIT"
    EARN_REVERSE   = "EARN_REVERSE"
    WITHDRAW_RESERVE = "WITHDRAW_RESERVE"
    WITHDRAW_COMMIT  = "WITHDRAW_COMMIT"
    SYSTEM_CUT     = "SYSTEM_CUT"
    BONUS          = "BONUS"
    ADJUST         = "ADJUST"
    
    WITHDRAW_REQ = "WITHDRAW_REQ"
    WITHDRAW_CUT = "WITHDRAW_CUT"
    WITHDRAW_FINAL = "WITHDRAW_FINAL"
    AI_TASK_EARN = "AI_TASK_EARN"
    AI_TASK_SPEND = "AI_TASK_SPEND"

class WalletLedger(Base):
    __tablename__ = "wallet_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    type: Mapped[LedgerType] = mapped_column(Enum(LedgerType))
    amount_usd: Mapped[float] = mapped_column(Float)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    ref_task_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="ux_wallet_ledger_idem"),
        Index("ix_wallet_user_created", "user_id", "created_at"),
    )
