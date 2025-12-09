"""
Support Ticket System
"""
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import (
    SupportTicket, SupportTicketMessage, User,
    TicketPriorityEnum, TicketStatusEnum
)
from src.core.deps import get_current_active_user, require_admin


router = APIRouter()


class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: TicketPriorityEnum = TicketPriorityEnum.MEDIUM


class TicketMessageCreate(BaseModel):
    message: str


class TicketResponse(BaseModel):
    id: str
    subject: str
    description: str
    priority: TicketPriorityEnum
    status: TicketStatusEnum
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/create", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new support ticket
    """
    ticket = SupportTicket(
        id=uuid4(),
        user_id=current_user.id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        priority=ticket_data.priority,
        status=TicketStatusEnum.OPEN,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    
    return TicketResponse(
        id=str(ticket.id),
        subject=ticket.subject,
        description=ticket.description,
        priority=ticket.priority,
        status=ticket.status,
        created_at=ticket.created_at,
    )


@router.get("/my-tickets", response_model=List[TicketResponse])
async def get_my_tickets(
    status_filter: Optional[TicketStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's support tickets
    """
    query = select(SupportTicket).where(SupportTicket.user_id == current_user.id)
    
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)
    
    query = query.order_by(SupportTicket.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    
    return [
        TicketResponse(
            id=str(t.id),
            subject=t.subject,
            description=t.description,
            priority=t.priority,
            status=t.status,
            created_at=t.created_at,
        )
        for t in tickets
    ]


@router.get("/{ticket_id}")
async def get_ticket_details(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get ticket details with messages
    """
    # Get ticket
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user.id
        )
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Get messages
    messages_result = await db.execute(
        select(SupportTicketMessage)
        .where(SupportTicketMessage.ticket_id == ticket_id)
        .order_by(SupportTicketMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    
    return {
        "ticket": ticket,
        "messages": messages
    }


@router.post("/{ticket_id}/message")
async def add_ticket_message(
    ticket_id: str,
    message_data: TicketMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a message to ticket
    """
    # Verify ticket ownership
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user.id
        )
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Create message
    message = SupportTicketMessage(
        id=uuid4(),
        ticket_id=ticket.id,
        user_id=current_user.id,
        message=message_data.message,
        is_staff=False,
        created_at=datetime.utcnow(),
    )
    
    db.add(message)
    
    # Update ticket status to in_progress if it was open
    if ticket.status == TicketStatusEnum.OPEN:
        ticket.status = TicketStatusEnum.IN_PROGRESS
    
    ticket.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return {
        "message": "Message added successfully",
        "message_id": str(message.id)
    }


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Close a ticket
    """
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user.id
        )
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket.status = TicketStatusEnum.CLOSED
    ticket.resolved_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Ticket closed successfully"
    }