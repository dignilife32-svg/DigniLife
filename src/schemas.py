#src/schemas.py
from pydantic import BaseModel, Field
from typing import List

class WalletSummarySchema(BaseModel):
    balance_cents: int
    available_cents: int
    on_hold_cents: int
    locked_reserve_cents: int
    tier: int
    trust_score: float

class WalletLimitsSchema(BaseModel):
    can_withdraw: bool
    min_cents: int
    max_cents_now: int
    attempts_left: int
    cooldown_seconds: int
    explain: str
    reasons: List[str] = []
    tier: int
    trust_score: float

class WithdrawCreate(BaseModel):
    amount_cents: int = Field(..., ge=100)      # at least $1 unless config says $5; validated again in logic
    dst_kind: str                                # "bank" | "wallet" | "store"
    dst_account: str
    country: str
    device_fp: str
    face_image_b64: str


# <<< CODEGEN:DAILY START
from typing import Optional, List
from pydantic import BaseModel

class TaskDTO(BaseModel):
    id: str
    title: str
    usd: float
    payload: dict = {}
    limits: dict = {}
    assist: dict | None = None

class SubmitDTO(BaseModel):
    task_id: str
    answer: dict
    elapsed_ms: int = 0

class SubmitResult(BaseModel):
    ok: bool
    usd_credited: float = 0.0
    next_hint: Optional[str] = None
    new_balance_usd: float = 0.0
# <<< CODEGEN:DAILY END
