"""
DocuRAG - Main Application Entry Point
AI-Powered Multimodal Document & Image Search & Analysis
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import get_settings, ensure_directories
from app.core.database import init_db, close_db
from app.core.logging import setup_logging
from app.api import documents, search, chat, image, evaluation


settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create directories
    ensure_directories()
    os.makedirs("logs", exist_ok=True)
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    logger.info("✅ DocuRAG is ready!")
    yield
    
    # Shutdown
    await close_db()
    logger.info("👋 DocuRAG shut down")


app = FastAPI(
    title="DocuRAG API",
    description="AI-Powered Multimodal Document & Image Search & Analysis",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for processed images / document pages
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/processed", StaticFiles(directory=settings.PROCESSED_DIR), name="processed")
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(image.router)
app.include_router(evaluation.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Multimodal Document & Image Search & Analysis",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
