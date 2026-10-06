"""
DocuRAG - Search API Routes
"""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, SearchResult
from app.schemas.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Perform hybrid search across all uploaded documents.
    Combines keyword (BM25) and semantic (vector) search with reranking.
    """
    start = time.time()
    
    from app.services.search_service import SearchService
    search_service = SearchService()
    results = await search_service.hybrid_search(
        query=request.query,
        user_id=user.id,
        document_ids=request.document_ids,
        content_types=request.content_types,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        db=db,
    )
    
    elapsed_ms = int((time.time() - start) * 1000)
    
    # Store search result for analytics
    sr = SearchResult(
        user_id=user.id,
        query=request.query,
        results=[r.model_dump() for r in results],
        num_results=len(results),
        search_time_ms=elapsed_ms,
    )
    db.add(sr)
    
    logger.info(f"Search: '{request.query}' -> {len(results)} results in {elapsed_ms}ms")
    
    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        search_time_ms=elapsed_ms,
    )
