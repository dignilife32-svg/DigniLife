# src/classic/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class DailyEarnRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    date: Optional[date] = None

class DailyEarnResponse(BaseModel):
    status: Literal["OK", "WARN", "BAD"]
    points: int
    reason: Optional[str] = None
