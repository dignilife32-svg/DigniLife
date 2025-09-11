# src/safety/models.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime

ReportCategory = Literal["bug", "abuse", "task", "payment", "other"]

class UserReport(BaseModel):
    user_id: str = Field(..., min_length=1)
    category: ReportCategory = "other"
    message: str = Field(..., min_length=5, max_length=2000)
    task_id: Optional[str] = None
    severity: Optional[int] = Field(3, ge=1, le=5)  # 1=low,5=critical
    contact: Optional[str] = None  # email/phone (free text)

class Geo(BaseModel):
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None

class SOSRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    reason: Optional[str] = "manual"
    location: Optional[Geo] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

class SOSAck(BaseModel):
    sos_id: str
    status: Literal["queued", "rate_limited"] = "queued"
    received_at: datetime
