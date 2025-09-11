
# src/admin/models.py
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.db.session import Base
from typing import Dict

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

# Summary schema format
UserEarnings = Dict[str, float]  # e.g. {"usd": 12.50, "minutes": 60, ...}
TaskStats = Dict[str, int]       # e.g. {"read_aloud": 4, "qr_proof": 2, ...}
