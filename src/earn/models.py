# src/earn/models.py
from pydantic import BaseModel, Field
from typing import Optional

class BonusGrant(BaseModel):
    user_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    reason: Optional[str] = "manual"

class BonusPolicy(BaseModel):
    accuracy_threshold: float = 0.90
    multiplier: float = 1.50
