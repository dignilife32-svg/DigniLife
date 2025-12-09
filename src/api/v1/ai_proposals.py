"""
AI Proposal System - User Suggestions
Users can suggest features and get rewarded if implemented
"""
from datetime import datetime
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import AIProposal, User, AIProposalStatusEnum
from src.core.deps import get_current_active_user, require_admin


router = APIRouter()


class ProposalCreate(BaseModel):
    title: str
    description: str
    category: str  # feature, improvement, bug_fix, other


class ProposalResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: AIProposalStatusEnum
    upvotes: int
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/create", response_model=ProposalResponse)
async def create_proposal(
    proposal: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit a new proposal/suggestion
    """
    new_proposal = AIProposal(
        id=uuid4(),
        user_id=current_user.id,
        title=proposal.title,
        description=proposal.description,
        category=proposal.category,
        status=AIProposalStatusEnum.PENDING,
        upvotes=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_proposal)
    await db.commit()
    await db.refresh(new_proposal)
    
    return ProposalResponse(
        id=str(new_proposal.id),
        title=new_proposal.title,
        description=new_proposal.description,
        category=new_proposal.category,
        status=new_proposal.status,
        upvotes=new_proposal.upvotes,
        created_at=new_proposal.created_at,
    )


@router.get("/", response_model=List[ProposalResponse])
async def list_proposals(
    status_filter: AIProposalStatusEnum = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all proposals
    """
    query = select(AIProposal)
    
    if status_filter:
        query = query.where(AIProposal.status == status_filter)
    
    query = query.order_by(AIProposal.upvotes.desc(), AIProposal.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    proposals = result.scalars().all()
    
    return [
        ProposalResponse(
            id=str(p.id),
            title=p.title,
            description=p.description,
            category=p.category,
            status=p.status,
            upvotes=p.upvotes,
            created_at=p.created_at,
        )
        for p in proposals
    ]


@router.post("/{proposal_id}/upvote")
async def upvote_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upvote a proposal
    """
    result = await db.execute(
        select(AIProposal).where(AIProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    proposal.upvotes += 1
    proposal.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Upvoted successfully",
        "upvotes": proposal.upvotes
    }


@router.get("/my-proposals")
async def get_my_proposals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's proposals
    """
    result = await db.execute(
        select(AIProposal)
        .where(AIProposal.user_id == current_user.id)
        .order_by(AIProposal.created_at.desc())
    )
    
    proposals = result.scalars().all()
    return proposals