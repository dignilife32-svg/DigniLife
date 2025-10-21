# src/sync/models.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List


class EarnEvent(BaseModel):
    id: Optional[str] = Field(default=None, description="client-side event id (optional)")
    usd_cents: int = Field(..., ge=1, example=250)
    note: Optional[str] = Field(default=None, example="testing bonus")
    ref: Optional[str] = Field(default=None, example="task:c1")  # idempotency key (optional)


class PushIn(BaseModel):
    earn: List[EarnEvent] = Field(default_factory=list)


class PushOut(BaseModel):
    accepted: int
    skipped: int
