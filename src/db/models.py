from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from src.db.session import Base 

class SomeModel(Base):
    __tablename__ = "some"

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    points = Column(Integer, nullable=False, default=0)
    reason = Column(String(120), nullable=False)  # e.g. "referral_signup"
    created_at = Column(DateTime, server_default=func.now())

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    inviter_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    invitee_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)  # filled after signup
    code = Column(String(16), unique=True, nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, completed, canceled
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('inviter_user_id', 'invitee_user_id', name='uq_referral_pair'),
    )
