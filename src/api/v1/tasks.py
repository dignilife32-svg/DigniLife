"""
Task Management Endpoints
"""
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from src.db.session import get_db
from src.db.models import (
    Task, Submission, TaskAssignment, EarningHistory,
    TaskTypeEnum, TaskDifficultyEnum, SubmissionStatusEnum
)
from src.schemas.task import (
    TaskListResponse, TaskResponse, 
    SubmissionCreate, SubmissionResponse
)
from src.core.deps import get_current_active_user
from src.db.models import User


router = APIRouter()


@router.get("/", response_model=List[TaskListResponse])
async def list_available_tasks(
    task_type: Optional[TaskTypeEnum] = None,
    difficulty: Optional[TaskDifficultyEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List available tasks for the user
    """
    # Build query
    query = select(Task).where(
        Task.is_active == True,
        Task.current_submissions < Task.max_submissions
    )
    
    # Apply filters
    if task_type:
        query = query.where(Task.task_type == task_type)
    if difficulty:
        query = query.where(Task.difficulty == difficulty)
    
    # Order by reward (highest first)
    query = query.order_by(Task.reward_usd.desc())
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_details(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get task details
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.post("/{task_id}/claim")
async def claim_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Claim a task (lock it for 30 minutes)
    """
    # Get task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not active"
        )
    
    if task.current_submissions >= task.max_submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is full"
        )
    
    # Check if user already has active assignment
    existing_assignment = await db.execute(
        select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == current_user.id,
            TaskAssignment.is_active == True,
            TaskAssignment.expires_at > datetime.utcnow()
        )
    )
    if existing_assignment.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active assignment for this task"
        )
    
    # Create assignment (lock for 30 minutes)
    assignment = TaskAssignment(
        id=uuid4(),
        task_id=task.id,
        user_id=current_user.id,
        assigned_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(assignment)
    
    await db.commit()
    await db.refresh(assignment)
    
    return {
        "message": "Task claimed successfully",
        "assignment_id": str(assignment.id),
        "expires_at": assignment.expires_at,
        "task": task
    }


@router.post("/{task_id}/submit", response_model=SubmissionResponse)
async def submit_task(
    task_id: str,
    submission_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit completed task
    """
    # Get task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has active assignment
    assignment_result = await db.execute(
        select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == current_user.id,
            TaskAssignment.is_active == True,
            TaskAssignment.expires_at > datetime.utcnow()
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active assignment found or assignment expired"
        )
    
    # Calculate completion time
    completion_time = int((datetime.utcnow() - assignment.assigned_at).total_seconds())
    
    # Create submission
    submission = Submission(
        id=uuid4(),
        task_id=task.id,
        user_id=current_user.id,
        data=submission_data,
        status=SubmissionStatusEnum.PENDING,
        completion_time_seconds=completion_time,
        submitted_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # AI Validation (simplified - score between 70-100)
    import random
    ai_score = random.uniform(70, 100)
    submission.ai_validation_score = ai_score
    
    # Auto-approve if score > 95
    if ai_score >= 95:
        submission.status = SubmissionStatusEnum.APPROVED
        submission.ai_auto_approved = True
        
        # Calculate earnings
        from decimal import Decimal
        from src.core.earning_engine import EarningEngine
        
        earnings = EarningEngine.calculate_earning(
            base_reward=Decimal(str(task.reward_usd)),
            ai_score=Decimal(str(ai_score)),
            completion_time_seconds=completion_time,
            expected_time_seconds=task.expected_time_seconds,
            user_tier=current_user.subscription_tier,
            current_streak=current_user.current_streak_days,
        )
        
        # Create earning record
        earning_record = EarningHistory(
            id=uuid4(),
            user_id=current_user.id,
            submission_id=submission.id,
            base_reward=float(earnings["base_reward"]),
            quality_bonus=float(earnings["quality_bonus"]),
            speed_bonus=float(earnings["speed_bonus"]),
            streak_bonus=float(earnings["streak_bonus"]),
            tier_multiplier=float(earnings["tier_multiplier"]),
            total_earned=float(earnings["total_earning"]),
            earned_at=datetime.utcnow(),
        )
        db.add(earning_record)
        
        # Update user balance
        current_user.available_balance_usd += float(earnings["total_earning"])
        current_user.total_earnings_usd += float(earnings["total_earning"])
        
        # Update task count
        task.current_submissions += 1
        
        # Update streak
        current_user.last_task_completed_date = datetime.utcnow().date()
        current_user.current_streak_days += 1
        if current_user.current_streak_days > current_user.longest_streak_days:
            current_user.longest_streak_days = current_user.current_streak_days
    
    else:
        submission.ai_validation_notes = "Requires human review"
        current_user.pending_balance_usd += float(task.reward_usd)
    
    # Mark assignment as completed
    assignment.is_active = False
    assignment.completed_at = datetime.utcnow()
    
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    return submission


@router.get("/my-tasks/active")
async def get_my_active_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's active task assignments
    """
    result = await db.execute(
        select(TaskAssignment, Task)
        .join(Task, TaskAssignment.task_id == Task.id)
        .where(
            TaskAssignment.user_id == current_user.id,
            TaskAssignment.is_active == True,
            TaskAssignment.expires_at > datetime.utcnow()
        )
    )
    
    assignments = []
    for assignment, task in result:
        assignments.append({
            "assignment_id": str(assignment.id),
            "task": task,
            "assigned_at": assignment.assigned_at,
            "expires_at": assignment.expires_at,
            "time_remaining_seconds": int((assignment.expires_at - datetime.utcnow()).total_seconds())
        })
    
    return assignments


@router.get("/my-tasks/submissions")
async def get_my_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's submission history
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    submissions = result.scalars().all()
    return submissions