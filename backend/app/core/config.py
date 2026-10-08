"""
DocuRAG Backend - Core Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "DocuRAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/docurag.db"
    
    # LLM
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.8-flash"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Storage paths
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    VECTOR_DIR: str = "data/vectors"
    
    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    
    # OCR
    OCR_ENGINE: str = "tesseract"
    
    # Vector DB
    VECTOR_DB: str = "faiss"
    FAISS_INDEX_PATH: str = "data/vectors/faiss_index"
    
    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Retrieval
    TOP_K: int = 10
    RERANK_TOP_K: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def ensure_directories():
    """Create required data directories."""
    settings = get_settings()
    dirs = [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.VECTOR_DIR,
        os.path.join(settings.PROCESSED_DIR, "images"),
        os.path.join(settings.PROCESSED_DIR, "text"),
        os.path.join(settings.PROCESSED_DIR, "metadata"),
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
