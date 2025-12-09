"""
Admin Dashboard Endpoints
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import (
    User, Task, Submission, Transaction, Withdrawal,
    SupportTicket, AIProposal, SubmissionStatusEnum,
    TicketStatusEnum, TransactionStatusEnum
)
from src.core.deps import require_admin


router = APIRouter()


class DashboardStats(BaseModel):
    total_users: int
    active_users_today: int
    total_tasks: int
    pending_submissions: int
    total_earnings_usd: float
    total_withdrawals_usd: float
    open_tickets: int
    pending_proposals: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Get overall platform statistics
    """
    # Total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    
    # Active users today
    today = datetime.utcnow().date()
    active_result = await db.execute(
        select(func.count(User.id)).where(
            func.date(User.last_activity_at) == today
        )
    )
    active_users = active_result.scalar() or 0
    
    # Total tasks
    tasks_result = await db.execute(select(func.count(Task.id)))
    total_tasks = tasks_result.scalar() or 0
    
    # Pending submissions
    pending_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatusEnum.PENDING
        )
    )
    pending_submissions = pending_result.scalar() or 0
    
    # Total earnings
    earnings_result = await db.execute(
        select(func.sum(User.total_earnings_usd))
    )
    total_earnings = earnings_result.scalar() or 0
    
    # Total withdrawals
    withdrawals_result = await db.execute(
        select(func.sum(Withdrawal.net_amount_usd)).where(
            Withdrawal.status == TransactionStatusEnum.COMPLETED
        )
    )
    total_withdrawals = withdrawals_result.scalar() or 0
    
    # Open tickets
    tickets_result = await db.execute(
        select(func.count(SupportTicket.id)).where(
            SupportTicket.status.in_([TicketStatusEnum.OPEN, TicketStatusEnum.IN_PROGRESS])
        )
    )
    open_tickets = tickets_result.scalar() or 0
    
    # Pending proposals
    proposals_result = await db.execute(
        select(func.count(AIProposal.id)).where(
            AIProposal.status == "pending"
        )
    )
    pending_proposals = proposals_result.scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        active_users_today=active_users,
        total_tasks=total_tasks,
        pending_submissions=pending_submissions,
        total_earnings_usd=float(total_earnings),
        total_withdrawals_usd=float(total_withdrawals),
        open_tickets=open_tickets,
        pending_proposals=pending_proposals,
    )


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    List all users with filters
    """
    query = select(User)
    
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    query = query.order_by(User.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users


@router.get("/submissions/pending")
async def get_pending_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Get pending submissions for review
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.status == SubmissionStatusEnum.PENDING)
        .order_by(Submission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    submissions = result.scalars().all()
    return submissions


@router.post("/submissions/{submission_id}/approve")
async def approve_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Approve a submission (admin review)
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Approve submission
    submission.status = SubmissionStatusEnum.APPROVED
    submission.reviewed_at = datetime.utcnow()
    submission.reviewed_by = admin_user.id
    submission.updated_at = datetime.utcnow()
    
    # Move balance from pending to available
    user_result = await db.execute(
        select(User).where(User.id == submission.user_id)
    )
    user = user_result.scalar_one()
    
    # Get task to get reward amount
    task_result = await db.execute(
        select(Task).where(Task.id == submission.task_id)
    )
    task = task_result.scalar_one()
    
    user.pending_balance_usd -= float(task.reward_usd)
    user.available_balance_usd += float(task.reward_usd)
    
    await db.commit()
    
    return {
        "message": "Submission approved successfully",
        "submission_id": submission_id
    }


@router.post("/submissions/{submission_id}/reject")
async def reject_submission(
    submission_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Reject a submission (admin review)
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Reject submission
    submission.status = SubmissionStatusEnum.REJECTED
    submission.reviewed_at = datetime.utcnow()
    submission.reviewed_by = admin_user.id
    submission.review_notes = reason
    submission.updated_at = datetime.utcnow()
    
    # Remove from pending balance
    user_result = await db.execute(
        select(User).where(User.id == submission.user_id)
    )
    user = user_result.scalar_one()
    
    task_result = await db.execute(
        select(Task).where(Task.id == submission.task_id)
    )
    task = task_result.scalar_one()
    
    user.pending_balance_usd -= float(task.reward_usd)
    
    await db.commit()
    
    return {
        "message": "Submission rejected",
        "submission_id": submission_id,
        "reason": reason
    }


@router.get("/withdrawals/pending")
async def get_pending_withdrawals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Get pending withdrawals for processing
    """
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.status == TransactionStatusEnum.PENDING)
        .order_by(Withdrawal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    withdrawals = result.scalars().all()
    return withdrawals


@router.post("/withdrawals/{withdrawal_id}/complete")
async def complete_withdrawal(
    withdrawal_id: str,
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    Mark withdrawal as completed
    """
    result = await db.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    withdrawal.status = TransactionStatusEnum.COMPLETED
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.transaction_id = transaction_id
    withdrawal.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Withdrawal marked as completed",
        "withdrawal_id": withdrawal_id
    }