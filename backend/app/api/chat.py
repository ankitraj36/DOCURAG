"""
DocuRAG - Chat API Routes
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Conversation, Message
from app.schemas.schemas import (
    ChatRequest, ChatResponse, ConversationResponse, MessageResponse,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Ask a question using the RAG pipeline.
    Retrieves relevant chunks, reranks, and generates an answer with citations.
    """
    start = time.time()
    
    from app.services.rag_service import RAGService
    rag = RAGService()
    response = await rag.answer_question(request, db, user.id)
    
    response.response_time_ms = int((time.time() - start) * 1000)
    logger.info(f"Chat: '{request.query[:80]}' -> {response.response_time_ms}ms, confidence={response.confidence_score}")
    
    return response


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = result.scalars().all()
    
    responses = []
    for conv in conversations:
        count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        msg_count = count_result.scalar()
        resp = ConversationResponse.model_validate(conv)
        resp.message_count = msg_count
        responses.append(resp)
    
    return responses


@router.get("/conversations/{conversation_id}", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all messages in a conversation."""
    # Verify ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    return [MessageResponse.model_validate(m) for m in messages]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conv)
    return {"message": "Conversation deleted"}
