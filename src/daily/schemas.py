# src/daily/schemas.py
from __future__ import annotations

from typing import Annotated, List
from pydantic import BaseModel, Field

# ---- Schemas ---------------------------------------------------------------

class TaskOut(BaseModel):
    code: str
    category: str
    display_value_usd: float
    expected_time_sec: int
    user_prompt: str
    description: str
    is_active: bool

class SubmitIn(BaseModel):
    task_code: str = Field(..., min_length=1, max_length=64)
    # Pydantic v2 style: no more `conint(...)` as a type
    usd_cents: Annotated[int, Field(ge=1, le=1_000_000)]
    note: str = Field(..., max_length=250)  # e.g., for voice, QR, etc.
