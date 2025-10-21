# src/admin/models.py
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

# ---- Admin task upsert / out -----------------------------------------------

class AdminTaskUpssert(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    category: str
    display_value_usd: float
    expected_time_sec: int
    description: str
    user_prompt: str
    is_active: bool = True

    # Optional: daily streak bonus system (if you really need it on this model)
    streak_days: int = Field(default=60, ge=0)

class AdminTaskOut(BaseModel):
    code: str
    category: str
    display_value_usd: float
    expected_time_sec: int
    user_prompt: str
    description: str
    is_active: bool
    streak_days: int = Field(default=60, ge=0)
