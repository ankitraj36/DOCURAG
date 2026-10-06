"""
DocuRAG - Image Analysis API Routes
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import get_settings
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User
from app.schemas.schemas import ImageAnalysisResponse

router = APIRouter(prefix="/api/image", tags=["Image Analysis"])
settings = get_settings()

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    query: str = Form(default="Describe this image in detail."),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Analyze an uploaded image using OCR and vision model.
    Supports charts, diagrams, tables, screenshots, and scanned documents.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {ext}")
    
    # Save the image
    image_id = str(uuid.uuid4())
    image_filename = f"{image_id}{ext}"
    image_path = os.path.join(settings.UPLOAD_DIR, "images", image_filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    content = await file.read()
    with open(image_path, "wb") as f:
        f.write(content)
    
    logger.info(f"Image uploaded for analysis: {file.filename} -> {image_id}")
    
    from app.services.vision_service import VisionService
    vision = VisionService()
    result = await vision.analyze_image(image_path, query)
    
    return ImageAnalysisResponse(
        image_id=image_id,
        analysis=result.get("analysis", ""),
        ocr_text=result.get("ocr_text"),
        detected_elements=result.get("detected_elements", []),
        confidence_score=result.get("confidence_score", 0.0),
    )
