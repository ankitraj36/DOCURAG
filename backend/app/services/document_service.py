"""
DocuRAG - Document Processing Service
Handles end-to-end document ingestion: extraction, OCR, chunking, embedding.
"""
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.models.models import (
    Document, DocumentPage, DocumentChunk, DocumentImage,
    DocumentStatus, ContentType, FileType,
)
from sqlalchemy import select

settings = get_settings()


class DocumentService:
    """Service for processing uploaded documents."""
    
    async def process_document(self, document_id: str):
        """
        Main processing pipeline for a document.
        1. Extract text, tables, images
        2. Run OCR on scanned pages
        3. Generate chunks
        4. Generate embeddings
        5. Store in vector database
        """
        async with async_session_factory() as db:
            try:
                # Get document
                result = await db.execute(select(Document).where(Document.id == document_id))
                doc = result.scalar_one_or_none()
                if not doc:
                    logger.error(f"Document not found: {document_id}")
                    return
                
                doc.status = DocumentStatus.PROCESSING
                await db.commit()
                
                logger.info(f"Processing document: {doc.original_filename} ({doc.file_type})")
                start = time.time()
                
                # Step 1: Extract content based on file type
                pages_data = await self._extract_content(doc)
                
                # Step 2: Store pages
                total_words = 0
                total_tables = 0
                total_images = 0
                
                for page_data in pages_data:
                    page = DocumentPage(
                        document_id=doc.id,
                        page_number=page_data["page_number"],
                        text_content=page_data.get("text", ""),
                        has_tables=page_data.get("has_tables", False),
                        has_images=page_data.get("has_images", False),
                        has_charts=page_data.get("has_charts", False),
                        ocr_text=page_data.get("ocr_text"),
                        page_image_path=page_data.get("page_image_path"),
                    )
                    db.add(page)
                    
                    text = page_data.get("text", "") or ""
                    total_words += len(text.split())
                    if page_data.get("has_tables"):
                        total_tables += len(page_data.get("tables", []))
                    if page_data.get("has_images"):
                        total_images += len(page_data.get("images", []))
                    
                    # Save extracted images
                    for img_data in page_data.get("images", []):
                        img = DocumentImage(
                            document_id=doc.id,
                            page_number=page_data["page_number"],
                            image_path=img_data["path"],
                            image_type=img_data.get("type", "unknown"),
                            ocr_text=img_data.get("ocr_text"),
                            width=img_data.get("width"),
                            height=img_data.get("height"),
                        )
                        db.add(img)
                
                # Step 3: Generate chunks
                chunks = await self._generate_chunks(doc, pages_data)
                
                for i, chunk_data in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        page_number=chunk_data.get("page_number"),
                        chunk_index=i,
                        content=chunk_data["content"],
                        content_type=ContentType(chunk_data.get("content_type", "text")),
                        section=chunk_data.get("section"),
                        token_count=len(chunk_data["content"].split()),
                        metadata_json={
                            "document_name": doc.original_filename,
                            "page_number": chunk_data.get("page_number"),
                            "content_type": chunk_data.get("content_type", "text"),
                            "section": chunk_data.get("section"),
                        },
                    )
                    db.add(chunk)
                
                # Step 4: Generate and store embeddings
                await self._generate_embeddings(doc.id, chunks, db)
                
                # Update document stats
                doc.num_pages = len(pages_data)
                doc.num_words = total_words
                doc.num_tables = total_tables
                doc.num_images = total_images
                doc.num_chunks = len(chunks)
                doc.status = DocumentStatus.PROCESSED
                doc.processed_at = datetime.utcnow()
                
                await db.commit()
                
                elapsed = time.time() - start
                logger.info(
                    f"Document processed: {doc.original_filename} | "
                    f"{len(pages_data)} pages, {len(chunks)} chunks, "
                    f"{total_words} words in {elapsed:.1f}s"
                )
                
            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")
                doc.status = DocumentStatus.FAILED
                await db.commit()
                raise
    
    async def _extract_content(self, doc: Document) -> List[Dict[str, Any]]:
        """Extract content from document based on file type."""
        from app.services.extractors import extract_pdf, extract_docx, extract_pptx, extract_txt, extract_image
        
        extractors = {
            FileType.PDF: extract_pdf,
            FileType.DOCX: extract_docx,
            FileType.PPTX: extract_pptx,
            FileType.TXT: extract_txt,
            FileType.JPG: extract_image,
            FileType.JPEG: extract_image,
            FileType.PNG: extract_image,
        }
        
        extractor = extractors.get(doc.file_type)
        if not extractor:
            raise ValueError(f"No extractor for file type: {doc.file_type}")
        
        return await extractor(doc.file_path, doc.id)
    
    async def _generate_chunks(self, doc: Document, pages_data: List[Dict]) -> List[Dict]:
        """Generate text chunks with metadata from extracted pages."""
        chunks = []
        
        for page_data in pages_data:
            text = page_data.get("text", "") or ""
            page_num = page_data["page_number"]
            
            # Skip empty pages
            if not text.strip():
                continue
            
            # Split text into chunks
            page_chunks = self._split_text(
                text,
                chunk_size=settings.CHUNK_SIZE,
                overlap=settings.CHUNK_OVERLAP,
            )
            
            for chunk_text in page_chunks:
                chunks.append({
                    "content": chunk_text,
                    "page_number": page_num,
                    "content_type": "text",
                    "section": page_data.get("section"),
                })
            
            # Add table chunks
            for table in page_data.get("tables", []):
                table_text = table if isinstance(table, str) else str(table)
                chunks.append({
                    "content": table_text,
                    "page_number": page_num,
                    "content_type": "table",
                    "section": page_data.get("section"),
                })
            
            # Add OCR text chunks
            ocr_text = page_data.get("ocr_text", "")
            if ocr_text and ocr_text.strip():
                ocr_chunks = self._split_text(ocr_text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
                for chunk_text in ocr_chunks:
                    chunks.append({
                        "content": chunk_text,
                        "page_number": page_num,
                        "content_type": "text",
                        "section": "OCR",
                    })
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks by words."""
        words = text.split()
        if len(words) <= chunk_size:
            return [text] if text.strip() else []
        
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks
    
    async def _generate_embeddings(self, document_id: str, chunks: List[Dict], db):
        """Generate embeddings for chunks and store in vector database."""
        from app.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        texts = [c["content"] for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "page_number": c.get("page_number"),
                "content_type": c.get("content_type", "text"),
                "chunk_index": i,
            }
            for i, c in enumerate(chunks)
        ]
        
        await embedding_service.add_documents(texts, metadatas, document_id)
        
        # Update chunk embedding status
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        db_chunks = result.scalars().all()
        for chunk in db_chunks:
            chunk.has_embedding = True
