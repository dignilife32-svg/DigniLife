# src/wallet/schemas.py
from __future__ import annotations

from typing import Optional, Annotated
from pydantic import BaseModel, Field

# ---- Common typed aliases ----------------------------------------------------
# Pylance-friendly: use Annotated[int, Field(...)] instead of conint(...)
UsdCents = Annotated[int, Field(ge=1, le=100_00, description="Amount in USD cents (1..10000)")]

# ---- API Schemas -------------------------------------------------------------

class WalletSummarySchema(BaseModel):
    balance_usd: float = Field(..., example=12.34)


class EarnIn(BaseModel):
    usd_cents: UsdCents = Field(..., example=250)  # $2.50
    ref: Optional[str] = Field(default=None, max_length=64)
    note: Optional[str] = Field(default=None, max_length=256)


class EarnOut(BaseModel):
    balance_usd: float


class WithdrawIn(BaseModel):
    usd_cents: UsdCents
    ref: Optional[str] = None
    note: Optional[str] = None


class WithdrawOut(BaseModel):
    balance_usd: float


class HoldFundsIn(BaseModel):
    usd_cents: UsdCents
    hold_ref: str = Field(..., max_length=64)
    note: Optional[str] = None


class ReleaseHoldIn(BaseModel):
    hold_ref: str = Field(..., max_length=64)


class LimitsSchema(BaseModel):
    max_single_tx_usd: float = 100.0
