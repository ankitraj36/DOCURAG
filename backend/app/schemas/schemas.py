"""
DocuRAG - Pydantic Schemas
Request/Response models for the API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class DocumentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ContentTypeEnum(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    HEADING = "heading"


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Document Schemas ────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    num_pages: int
    num_words: int
    num_tables: int
    num_images: int
    num_chunks: int
    ocr_applied: bool
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentDetailResponse(DocumentResponse):
    pages: List[Dict[str, Any]] = []
    metadata_json: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


# ─── Search Schemas ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    document_ids: Optional[List[str]] = None
    content_types: Optional[List[ContentTypeEnum]] = None
    top_k: int = Field(default=10, ge=1, le=50)
    use_hybrid: bool = True


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    content: str
    content_type: str
    score: float
    section: Optional[str] = None
    highlights: Optional[List[str]] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_time_ms: int


# ─── Chat Schemas ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    stream: bool = False


class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    content: str
    chunk_id: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str
    citations: List[Citation] = []
    confidence_score: float
    response_time_ms: int
    retrieved_chunks: int
    model_used: str
    related_questions: List[str] = []


class ConversationResponse(BaseModel):
    id: str
    title: str
    document_ids: List[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    confidence_score: Optional[float] = None
    response_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Comparison Schemas ──────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2)
    aspects: Optional[List[str]] = None
    query: Optional[str] = None


class CompareResponse(BaseModel):
    comparison_table: Dict[str, Dict[str, str]]
    summary: str
    citations: List[Citation] = []
    confidence_score: float


# ─── Summary Schemas ─────────────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    document_id: str
    summary_type: str = Field(default="detailed", pattern="^(executive|short|detailed|key_points)$")


class SummarizeResponse(BaseModel):
    document_id: str
    document_name: str
    summary_type: str
    summary: str
    key_points: List[str] = []
    entities: List[str] = []
    important_dates: List[str] = []
    conclusions: List[str] = []
    action_items: List[str] = []
    citations: List[Citation] = []


# ─── Image Analysis Schemas ──────────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    image_id: str
    analysis: str
    ocr_text: Optional[str] = None
    detected_elements: List[str] = []
    confidence_score: float


# ─── Page Explanation Schema ─────────────────────────────────────────────────

class PageExplainRequest(BaseModel):
    document_id: str
    page_number: int


class PageExplainResponse(BaseModel):
    document_id: str
    page_number: int
    summary: str
    key_information: List[str]
    important_numbers: List[Dict[str, Any]]
    tables_explained: List[str]
    charts_explained: List[str]
    main_conclusion: str


# ─── Evaluation Schemas ──────────────────────────────────────────────────────

class EvaluationMetrics(BaseModel):
    retrieval: Dict[str, float] = {}
    generation: Dict[str, float] = {}
    system: Dict[str, Any] = {}


class EvaluationResponse(BaseModel):
    metrics: EvaluationMetrics
    history: List[Dict[str, Any]] = []
    total_evaluations: int


# ─── Analytics Schemas ───────────────────────────────────────────────────────

class AnalyticsDashboard(BaseModel):
    total_documents: int
    total_pages: int
    total_chunks: int
    total_questions: int
    total_searches: int
    avg_response_time_ms: float
    documents_by_type: Dict[str, int]
    questions_over_time: List[Dict[str, Any]]
    most_searched_documents: List[Dict[str, Any]]


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_store: str
    llm: str
    timestamp: datetime
