"""
DocuRAG - Evaluation & Analytics API Routes
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import (
    User, Document, DocumentChunk, Message, SearchResult, 
    EvaluationResult, Conversation,
)
from app.schemas.schemas import (
    EvaluationResponse, EvaluationMetrics, AnalyticsDashboard, HealthResponse,
)
from app.core.config import get_settings

router = APIRouter(tags=["Evaluation & Analytics"])
settings = get_settings()


@router.get("/api/evaluation", response_model=EvaluationResponse)
async def get_evaluation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get RAG evaluation metrics (computed from stored evaluation results)."""
    result = await db.execute(
        select(EvaluationResult).order_by(EvaluationResult.created_at.desc()).limit(100)
    )
    evaluations = result.scalars().all()
    
    # Compute aggregate metrics
    retrieval_metrics = {}
    generation_metrics = {}
    system_metrics = {}
    
    precision_vals = [e.precision_at_k for e in evaluations if e.precision_at_k is not None]
    recall_vals = [e.recall_at_k for e in evaluations if e.recall_at_k is not None]
    mrr_vals = [e.mrr for e in evaluations if e.mrr is not None]
    
    if precision_vals:
        retrieval_metrics["precision_at_k"] = sum(precision_vals) / len(precision_vals)
    if recall_vals:
        retrieval_metrics["recall_at_k"] = sum(recall_vals) / len(recall_vals)
    if mrr_vals:
        retrieval_metrics["mrr"] = sum(mrr_vals) / len(mrr_vals)
    
    relevance_vals = [e.answer_relevance for e in evaluations if e.answer_relevance is not None]
    context_vals = [e.context_relevance for e in evaluations if e.context_relevance is not None]
    faith_vals = [e.faithfulness for e in evaluations if e.faithfulness is not None]
    cite_vals = [e.citation_accuracy for e in evaluations if e.citation_accuracy is not None]
    
    if relevance_vals:
        generation_metrics["answer_relevance"] = sum(relevance_vals) / len(relevance_vals)
    if context_vals:
        generation_metrics["context_relevance"] = sum(context_vals) / len(context_vals)
    if faith_vals:
        generation_metrics["faithfulness"] = sum(faith_vals) / len(faith_vals)
    if cite_vals:
        generation_metrics["citation_accuracy"] = sum(cite_vals) / len(cite_vals)
    
    # System metrics
    docs_result = await db.execute(select(func.count(Document.id)))
    chunks_result = await db.execute(select(func.count(DocumentChunk.id)))
    
    resp_times = [e.response_time_ms for e in evaluations if e.response_time_ms is not None]
    
    system_metrics["total_documents"] = docs_result.scalar() or 0
    system_metrics["total_chunks"] = chunks_result.scalar() or 0
    system_metrics["avg_response_time_ms"] = (sum(resp_times) / len(resp_times)) if resp_times else 0
    system_metrics["total_evaluations"] = len(evaluations)
    
    history = [
        {
            "id": e.id,
            "type": e.evaluation_type,
            "query": e.query,
            "precision": e.precision_at_k,
            "recall": e.recall_at_k,
            "faithfulness": e.faithfulness,
            "response_time_ms": e.response_time_ms,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evaluations[:20]
    ]
    
    return EvaluationResponse(
        metrics=EvaluationMetrics(
            retrieval=retrieval_metrics,
            generation=generation_metrics,
            system=system_metrics,
        ),
        history=history,
        total_evaluations=len(evaluations),
    )


@router.get("/api/analytics", response_model=AnalyticsDashboard)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get analytics dashboard data."""
    # Counts
    docs_count = (await db.execute(
        select(func.count(Document.id)).where(Document.user_id == user.id)
    )).scalar() or 0
    
    pages_count = (await db.execute(
        select(func.sum(Document.num_pages)).where(Document.user_id == user.id)
    )).scalar() or 0
    
    chunks_count = (await db.execute(
        select(func.count(DocumentChunk.id))
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.user_id == user.id)
    )).scalar() or 0
    
    questions_count = (await db.execute(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user.id, Message.role == "user")
    )).scalar() or 0
    
    searches_count = (await db.execute(
        select(func.count(SearchResult.id)).where(SearchResult.user_id == user.id)
    )).scalar() or 0
    
    # Average response time
    avg_time_result = await db.execute(
        select(func.avg(Message.response_time_ms))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user.id, Message.role == "assistant")
    )
    avg_time = avg_time_result.scalar() or 0
    
    # Documents by type
    type_result = await db.execute(
        select(Document.file_type, func.count(Document.id))
        .where(Document.user_id == user.id)
        .group_by(Document.file_type)
    )
    docs_by_type = {str(row[0].value) if row[0] else "unknown": row[1] for row in type_result.all()}
    
    return AnalyticsDashboard(
        total_documents=docs_count,
        total_pages=pages_count,
        total_chunks=chunks_count,
        total_questions=questions_count,
        total_searches=searches_count,
        avg_response_time_ms=float(avg_time),
        documents_by_type=docs_by_type,
        questions_over_time=[],
        most_searched_documents=[],
    )


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected",
        vector_store="faiss",
        llm=settings.LLM_MODEL,
        timestamp=datetime.utcnow(),
    )
