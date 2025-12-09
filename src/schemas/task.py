"""
Task Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from src.db.models import TaskTypeEnum, TaskDifficultyEnum, SubmissionStatusEnum


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: TaskTypeEnum
    difficulty: TaskDifficultyEnum
    reward_usd: float = Field(..., gt=0)
    expected_time_seconds: int = Field(..., gt=0)
    instructions: Optional[str] = None
    max_submissions: int = Field(..., gt=0)


class TaskCreate(TaskBase):
    project_id: UUID
    example_data: Optional[Dict[str, Any]] = None
    metadata_required: Optional[Dict[str, Any]] = None
    validation_criteria: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    reward_usd: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    id: UUID
    project_id: UUID
    current_submissions: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    id: UUID
    title: str
    task_type: TaskTypeEnum
    difficulty: TaskDifficultyEnum
    reward_usd: float
    expected_time_seconds: int
    current_submissions: int
    max_submissions: int
    is_active: bool
    
    class Config:
        from_attributes = True


# Submission schemas
class SubmissionCreate(BaseModel):
    task_id: UUID
    data: Dict[str, Any]


class SubmissionResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    data: Dict[str, Any]
    status: SubmissionStatusEnum
    ai_validation_score: Optional[float] = None
    ai_auto_approved: bool
    submitted_at: datetime
    
    class Config:
        from_attributes = True