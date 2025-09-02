# src/daily/models.py
from pydantic import BaseModel, Field
from typing import List, Optional


class StartBundleReq(BaseModel):
    minutes: int = Field(ge=1, le=240)


class StartBundleResp(BaseModel):
    bundle_id: str
    expires_in_sec: int


class SubmitItem(BaseModel):
    qid: str
    answer: str
    correct: Optional[bool] = None
    tokens: int = 0


class SubmitReq(BaseModel):
    bundle_id: str
    items: List[SubmitItem]


class SubmitResp(BaseModel):
    accepted: int
    reward_usd: float


class SummaryResp(BaseModel):
    user_id: str
    month: str
    total_tasks: int
    total_reward_usd: float
    daily_average_usd: float
