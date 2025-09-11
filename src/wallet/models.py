from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# <-- ADD (bring back) -->
class UserCapabilities(BaseModel):
    # simple accessibility feature flags (MVP)
    prefers_voice: bool = False
    prefers_large_text: bool = False
    prefers_high_contrast: bool = False
    limited_motor: bool = False

# existing wallet summary (keep this)
class WalletSummary(BaseModel):
    user_id: str
    available_balance: float
    pending_withdrawal: float
    last_contribution: Optional[datetime] = None

class WithdrawRequestBody(BaseModel):
    amount: float = Field(..., gt=0)
    method: str = Field("wallet", min_length=2)   # "bank" | "wallet" | "mobile"
    details: Optional[str] = None                 # free text / JSON string

class WithdrawAdminAction(BaseModel):
    withdraw_id: int = Field(..., ge=1)
    tx_ref: Optional[str] = None                  # for approve
