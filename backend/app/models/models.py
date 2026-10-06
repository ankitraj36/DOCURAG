"""
DocuRAG - Database Models
Complete data model for the document intelligence platform.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime, 
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


def generate_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ContentType(str, enum.Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    HEADING = "heading"
    CODE = "code"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(SAEnum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(1000), nullable=False)
    
    # Processing info
    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.PENDING)
    num_pages = Column(Integer, default=0)
    num_words = Column(Integer, default=0)
    num_tables = Column(Integer, default=0)
    num_images = Column(Integer, default=0)
    num_chunks = Column(Integer, default=0)
    ocr_applied = Column(Boolean, default=False)
    
    # Metadata
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    images = relationship("DocumentImage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=True)
    has_tables = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)
    has_charts = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)
    page_image_path = Column(String(1000), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="pages")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(SAEnum(ContentType), default=ContentType.TEXT)
    
    # Metadata for retrieval
    section = Column(String(500), nullable=True)
    token_count = Column(Integer, default=0)
    
    # Embedding reference
    embedding_id = Column(String(100), nullable=True)
    has_embedding = Column(Boolean, default=False)
    
    # Source tracking
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class DocumentImage(Base):
    __tablename__ = "document_images"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    image_path = Column(String(1000), nullable=False)
    image_type = Column(String(50), nullable=True)  # chart, diagram, photo, table_image
    caption = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)  # Vision model analysis
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="images")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), default="New Conversation")
    document_ids = Column(JSON, default=list)  # List of document IDs in scope
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # RAG metadata
    retrieved_chunks = Column(JSON, nullable=True)  # Chunk IDs used
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    
    citations = Column(JSON, nullable=True)  # [{doc_id, page, text, chunk_id}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class SearchResult(Base):
    __tablename__ = "search_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    results = Column(JSON, nullable=True)  # Stored search results
    num_results = Column(Integer, default=0)
    search_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    evaluation_type = Column(String(50), nullable=False)  # retrieval, generation, system
    query = Column(Text, nullable=True)
    
    # Retrieval metrics
    precision_at_k = Column(Float, nullable=True)
    recall_at_k = Column(Float, nullable=True)
    mrr = Column(Float, nullable=True)
    
    # Generation metrics
    answer_relevance = Column(Float, nullable=True)
    context_relevance = Column(Float, nullable=True)
    faithfulness = Column(Float, nullable=True)
    citation_accuracy = Column(Float, nullable=True)
    
    # System metrics
    response_time_ms = Column(Integer, nullable=True)
    retrieval_time_ms = Column(Integer, nullable=True)
    
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
