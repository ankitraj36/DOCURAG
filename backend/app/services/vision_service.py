"""
DocuRAG - Vision Service
Image/chart/diagram analysis using OCR and vision models.
"""
import os
from typing import Dict, Any
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class VisionService:
    """Service for analyzing images using OCR and vision-capable LLMs."""
    
    async def analyze_image(self, image_path: str, query: str = "Describe this image.") -> Dict[str, Any]:
        """
        Analyze an image:
        1. Run OCR to extract text
        2. Use vision LLM (if available) for understanding
        3. Combine results
        """
        result = {
            "analysis": "",
            "ocr_text": None,
            "detected_elements": [],
            "confidence_score": 0.0,
        }
        
        # Step 1: OCR
        ocr_text = await self._run_ocr(image_path)
        result["ocr_text"] = ocr_text
        
        # Step 2: Vision model analysis
        try:
            if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your-google-api-key":
                analysis = await self._vision_llm_analysis(image_path, query)
                result["analysis"] = analysis
                result["confidence_score"] = 0.85
            else:
                # Fallback to OCR-based description
                if ocr_text:
                    result["analysis"] = f"Text detected in image:\n{ocr_text}"
                    result["confidence_score"] = 0.6
                else:
                    result["analysis"] = "Image uploaded. OCR found no text. Connect an OpenAI API key for visual understanding."
                    result["confidence_score"] = 0.2
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            result["analysis"] = f"Analysis partially completed. OCR text: {ocr_text or 'None detected'}"
            result["confidence_score"] = 0.3
        
        # Detect element types
        result["detected_elements"] = self._detect_elements(ocr_text, result["analysis"])
        
        return result
    
    async def _run_ocr(self, image_path: str) -> str:
        """Run OCR on an image."""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip() if text.strip() else None
        except ImportError:
            logger.warning("pytesseract not installed")
            return None
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return None
    
    async def _vision_llm_analysis(self, image_path: str, query: str) -> str:
        """Use a vision-capable LLM to analyze the image."""
        import base64
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.schema import HumanMessage
        
        llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", google_api_key=settings.GOOGLE_API_KEY, temperature=0.2)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"""Analyze this image and answer: {query}

Provide:
1. Description of what the image shows
2. Any text visible in the image
3. If it's a chart/graph: data points, trends, and conclusions
4. If it's a table: structured data extraction
5. If it's a diagram: components and relationships
6. If it's a document: key information"""},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                },
            ]
        )
        
        response = await llm.ainvoke([message])
        return response.content
    
    def _detect_elements(self, ocr_text: str, analysis: str) -> list:
        """Detect types of elements in the image."""
        elements = []
        combined = f"{ocr_text or ''} {analysis}".lower()
        
        if any(w in combined for w in ["table", "row", "column", "header"]):
            elements.append("table")
        if any(w in combined for w in ["chart", "graph", "plot", "axis"]):
            elements.append("chart")
        if any(w in combined for w in ["diagram", "flow", "architecture", "component"]):
            elements.append("diagram")
        if ocr_text and len(ocr_text) > 50:
            elements.append("text")
        if any(w in combined for w in ["photo", "image", "picture"]):
            elements.append("photo")
        
        return elements if elements else ["image"]
