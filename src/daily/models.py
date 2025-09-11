# src/daily/models.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

TaskType = Literal["daily", "classic"]

class TaskSubmission(BaseModel):
    user_id: str = Field(..., min_length=1)
    task_type: TaskType = "daily"
    proof: Optional[str] = None
    accuracy: Optional[float] = 1.0
    submitted_at: Optional[datetime] = None
