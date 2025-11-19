# src/admin/models.py
from __future__ import annotations
from typing import Optional, Dict, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

TaskCategory = Literal["content", "ops", "growth", "research", "other"]

class AdminTaskUpsert(BaseModel):
    """Input schema for create/update (upsert)."""
    model_config = ConfigDict(extra="ignore")
    code: str = Field(min_length=1, max_length=64)
    title: Optional[str] = None
    category: Optional[TaskCategory] = None
    display_value_usd: Optional[float] = None
    expected_time_sec: Optional[int] = None
    description: Optional[str] = None
    user_prompt: Optional[str] = None
    payload: Optional[Dict] = None
    is_active: bool = True
    streak_days: int = Field(default=0, ge=0)

class AdminTaskOut(BaseModel):
    """Read model used by responses in router."""
    code: str = Field(min_length=1, max_length=64)
    title: Optional[str] = None
    category: Optional[TaskCategory] = None
    display_value_usd: Optional[float] = None
    expected_time_sec: Optional[int] = None
    description: Optional[str] = None
    user_prompt: Optional[str] = None
    payload: Optional[Dict] = None
    is_active: bool = True
    streak_days: int = 0

class LedgerRow(BaseModel):
    """Response row for /wallet/ledger."""
    id: int
    user_id: str
    amount_usd: Decimal | float
    ref: str
    note: str
    created_at: datetime

__all__ = ["TaskCategory", "AdminTaskUpsert", "AdminTaskOut", "LedgerRow"]
