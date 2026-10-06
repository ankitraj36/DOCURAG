"""
DocuRAG - Document API Routes
"""
import os
import uuid
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.config import get_settings
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Document, DocumentPage, DocumentChunk, DocumentImage, User, FileType, DocumentStatus
from app.schemas.schemas import (
    DocumentResponse, DocumentListResponse, DocumentUploadResponse,
    DocumentDetailResponse, SummarizeRequest, SummarizeResponse,
    CompareRequest, CompareResponse, PageExplainRequest, PageExplainResponse,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".jpg", ".jpeg", ".png"}


def get_file_type(filename: str) -> FileType:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    try:
        return FileType(ext)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload a document for processing."""
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Save file
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    content = await file.read()
    file_size = len(content)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    doc = Document(
        id=file_id,
        user_id=user.id,
        filename=safe_filename,
        original_filename=file.filename,
        file_type=get_file_type(file.filename),
        file_size=file_size,
        file_path=file_path,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.flush()
    
    logger.info(f"Document uploaded: {file.filename} ({file_size} bytes) -> {file_id}")
    
    # Trigger background processing
    background_tasks.add_task(process_document_task, file_id)
    
    return DocumentUploadResponse(
        id=file_id,
        filename=file.filename,
        status="pending",
        message="Document uploaded successfully. Processing started.",
    )


async def process_document_task(document_id: str):
    """Background task to process a document. Delegates to the ingestion service."""
    from app.services.document_service import DocumentService
    try:
        service = DocumentService()
        await service.process_document(document_id)
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all documents for the current user."""
    query = select(Document).where(Document.user_id == user.id)
    count_query = select(func.count(Document.id)).where(Document.user_id == user.id)
    
    if file_type:
        query = query.where(Document.file_type == file_type)
        count_query = count_query.where(Document.file_type == file_type)
    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)
    if search:
        query = query.where(Document.original_filename.ilike(f"%{search}%"))
        count_query = count_query.where(Document.original_filename.ilike(f"%{search}%"))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    query = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get document details."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get pages
    pages_result = await db.execute(
        select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)
    )
    pages = pages_result.scalars().all()
    
    response = DocumentDetailResponse.model_validate(doc)
    response.pages = [
        {
            "page_number": p.page_number,
            "has_tables": p.has_tables,
            "has_images": p.has_images,
            "has_charts": p.has_charts,
            "text_preview": (p.text_content or "")[:500],
        }
        for p in pages
    ]
    return response


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a document and all associated data."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from storage
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    await db.delete(doc)
    logger.info(f"Document deleted: {document_id}")
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/process")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reprocess a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.status = DocumentStatus.PENDING
    await db.flush()
    
    background_tasks.add_task(process_document_task, document_id)
    return {"message": "Reprocessing started"}


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a summary of a document."""
    from app.services.rag_service import RAGService
    rag = RAGService()
    return await rag.summarize_document(request, db, user.id)


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare two or more documents."""
    from app.services.rag_service import RAGService
    rag = RAGService()
    return await rag.compare_documents(request, db, user.id)


@router.post("/explain-page", response_model=PageExplainResponse)
async def explain_page(
    request: PageExplainRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Explain everything on a specific page."""
    from app.services.rag_service import RAGService
    rag = RAGService()
    return await rag.explain_page(request, db, user.id)
