"""
DocuRAG - Search Service
Hybrid keyword (BM25) + semantic (vector) search with reranking.
"""
import re
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Document, DocumentChunk
from app.schemas.schemas import SearchResultItem, ContentTypeEnum


class SearchService:
    """Hybrid search combining BM25 keyword search with FAISS semantic search."""
    
    async def hybrid_search(
        self,
        query: str,
        user_id: str,
        document_ids: Optional[List[str]],
        content_types: Optional[List[ContentTypeEnum]],
        top_k: int,
        use_hybrid: bool,
        db: AsyncSession,
    ) -> List[SearchResultItem]:
        """
        Perform hybrid search combining keyword and semantic results.
        1. BM25 keyword search on stored chunks
        2. FAISS semantic vector search
        3. Reciprocal Rank Fusion (RRF) to merge results
        4. Reranking
        """
        # Get user's documents
        if document_ids:
            doc_filter = document_ids
        else:
            result = await db.execute(
                select(Document.id).where(Document.user_id == user_id)
            )
            doc_filter = [r[0] for r in result.all()]
        
        if not doc_filter:
            return []
        
        # Semantic search
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        semantic_results = await embedding_service.search(query, top_k=top_k * 2, filter_doc_ids=doc_filter)
        
        # Keyword search (BM25-style)
        keyword_results = await self._keyword_search(query, doc_filter, top_k * 2, db)
        
        if use_hybrid:
            # Reciprocal Rank Fusion
            merged = self._reciprocal_rank_fusion(semantic_results, keyword_results, k=60)
        else:
            merged = semantic_results
        
        # Get document names for results
        doc_names = {}
        if doc_filter:
            doc_result = await db.execute(
                select(Document.id, Document.original_filename).where(Document.id.in_(doc_filter))
            )
            doc_names = {row[0]: row[1] for row in doc_result.all()}
        
        # Build response
        results = []
        seen = set()
        for item in merged[:top_k]:
            doc_id = item["metadata"].get("document_id", "")
            text = item.get("text", "")
            
            # Dedup by content hash
            content_key = f"{doc_id}:{hash(text[:200])}"
            if content_key in seen:
                continue
            seen.add(content_key)
            
            # Generate highlights
            highlights = self._extract_highlights(text, query)
            
            results.append(SearchResultItem(
                chunk_id=str(item["metadata"].get("chunk_index", 0)),
                document_id=doc_id,
                document_name=doc_names.get(doc_id, "Unknown"),
                page_number=item["metadata"].get("page_number"),
                content=text[:1000],
                content_type=item["metadata"].get("content_type", "text"),
                score=round(item.get("score", 0.0), 4),
                section=item["metadata"].get("section"),
                highlights=highlights,
            ))
        
        return results
    
    async def _keyword_search(
        self, query: str, doc_ids: List[str], top_k: int, db: AsyncSession
    ) -> List[Dict]:
        """Simple keyword-based search on stored chunks."""
        # Tokenize query
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        if not query_terms:
            return []
        
        # Get all chunks for the user's documents
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(doc_ids))
        )
        chunks = result.scalars().all()
        
        # Score chunks using BM25-like term frequency
        scored = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            score = 0.0
            for term in query_terms:
                count = content_lower.count(term)
                if count > 0:
                    # BM25-inspired scoring (simplified)
                    tf = count / (len(content_lower.split()) + 1)
                    score += tf * (1.5 + 1) / (tf + 1.5)
            
            if score > 0:
                scored.append({
                    "text": chunk.content,
                    "score": score,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "page_number": chunk.page_number,
                        "content_type": chunk.content_type.value if chunk.content_type else "text",
                        "chunk_index": chunk.chunk_index,
                        "section": chunk.section,
                    },
                })
        
        # Sort by score
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
    
    def _reciprocal_rank_fusion(
        self, semantic: List[Dict], keyword: List[Dict], k: int = 60
    ) -> List[Dict]:
        """Merge two ranked lists using Reciprocal Rank Fusion."""
        scores = {}
        items = {}
        
        for rank, item in enumerate(semantic):
            key = f"{item['metadata'].get('document_id')}_{item['metadata'].get('chunk_index')}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            items[key] = item
        
        for rank, item in enumerate(keyword):
            key = f"{item['metadata'].get('document_id')}_{item['metadata'].get('chunk_index')}"
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
            if key not in items:
                items[key] = item
        
        # Sort by fused score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for key in sorted_keys:
            item = items[key].copy()
            item["score"] = scores[key]
            results.append(item)
        
        return results
    
    def _extract_highlights(self, text: str, query: str, max_highlights: int = 3) -> List[str]:
        """Extract text snippets around query terms for highlighting."""
        query_terms = set(re.findall(r'\w+', query.lower()))
        highlights = []
        
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(term in sentence.lower() for term in query_terms):
                snippet = sentence.strip()[:200]
                if snippet:
                    highlights.append(snippet)
            if len(highlights) >= max_highlights:
                break
        
        return highlights
