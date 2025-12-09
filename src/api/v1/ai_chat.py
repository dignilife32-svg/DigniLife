"""
AI Chat Assistant Endpoints
"""
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.db.session import get_db
from src.db.models import User, ChatMessage
from src.core.deps import get_current_active_user
from src.services.ai_chat import AIChat


router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    message: str
    intent: str
    suggestions: List[str]
    actions: List[dict]
    timestamp: datetime


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send message to AI chat assistant
    """
    # Get conversation history if conversation_id provided
    conversation_history = []
    if request.conversation_id:
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == request.conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(10)  # Last 10 messages
        )
        history_messages = history_result.scalars().all()
        conversation_history = [
            {"role": msg.role, "content": msg.message}
            for msg in history_messages
        ]
    
    # Build user context
    user_context = {
        "subscription_tier": current_user.subscription_tier.value,
        "total_earnings_usd": float(current_user.total_earnings_usd),
        "available_balance_usd": float(current_user.available_balance_usd),
        "current_streak_days": current_user.current_streak_days,
        "is_verified": current_user.is_verified,
        "kyc_verified": current_user.kyc_verified,
        "tasks_today": 0,  # TODO: Calculate from today's submissions
    }
    
    # Process message with AI
    ai_response = await AIChat.process_message(
        user_message=request.message,
        user_context=user_context,
        conversation_history=conversation_history
    )
    
    # Save messages to database
    conversation_id = request.conversation_id or str(uuid4())
    
    # Save user message
    user_msg = ChatMessage(
        id=uuid4(),
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="user",
        message=request.message,
        created_at=datetime.utcnow(),
    )
    db.add(user_msg)
    
    # Save AI response
    ai_msg = ChatMessage(
        id=uuid4(),
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="assistant",
        message=ai_response["message"],
        message_metadata={
            "intent": ai_response["intent"],
            "suggestions": ai_response["suggestions"],
            "actions": ai_response["actions"],
        },
        created_at=datetime.utcnow(),
    )
    db.add(ai_msg)
    
    await db.commit()
    
    return ChatMessageResponse(
        message=ai_response["message"],
        intent=ai_response["intent"],
        suggestions=ai_response["suggestions"],
        actions=ai_response["actions"],
        timestamp=datetime.utcnow(),
    )


@router.get("/conversations")
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's chat conversations
    """
    # Get distinct conversation IDs
    from sqlalchemy import distinct, func
    
    result = await db.execute(
        select(
            ChatMessage.conversation_id,
            func.max(ChatMessage.created_at).label("last_message_at"),
            func.count(ChatMessage.id).label("message_count")
        )
        .where(ChatMessage.user_id == current_user.id)
        .group_by(ChatMessage.conversation_id)
        .order_by(func.max(ChatMessage.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    
    conversations = []
    for row in result:
        # Get first message preview
        preview_result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == current_user.id,
                ChatMessage.conversation_id == row.conversation_id
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        first_message = preview_result.scalar_one_or_none()
        
        conversations.append({
            "conversation_id": row.conversation_id,
            "last_message_at": row.last_message_at,
            "message_count": row.message_count,
            "preview": first_message.message[:100] if first_message else ""
        })
    
    return conversations


@router.get("/conversations/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get messages from a specific conversation
    """
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.user_id == current_user.id,
            ChatMessage.conversation_id == conversation_id
        )
        .order_by(ChatMessage.created_at.asc())
    )
    
    messages = result.scalars().all()
    return messages