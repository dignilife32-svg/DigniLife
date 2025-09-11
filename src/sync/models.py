# src/sync/models.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Any
from datetime import datetime

OpType = Literal["task.submit", "bonus.grant", "user.report", "sos.manual"]

class SyncOp(BaseModel):
    op_id: str = Field(..., min_length=8)     # client-generated UUID
    user_id: str
    op_type: OpType
    payload: dict

class SyncPushRequest(BaseModel):
    ops: List[SyncOp]

class SyncPushResult(BaseModel):
    op_id: str
    status: Literal["applied", "duplicate", "failed"]
    result: Optional[Any] = None
    error: Optional[str] = None

class SyncPullResponse(BaseModel):
    since: Optional[str] = None
    tasks: list = []
    bonuses: list = []
    reports: list = []
    sos: list = []
