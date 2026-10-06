"""
DocuRAG - File Content Extractors
Extract text, tables, images from different document formats.
"""
import os
import json
from typing import List, Dict, Any
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


async def extract_pdf(file_path: str, document_id: str) -> List[Dict[str, Any]]:
    """Extract content from PDF using PyMuPDF."""
    import fitz  # PyMuPDF
    
    pages_data = []
    doc = fitz.open(file_path)
    
    output_dir = os.path.join(settings.PROCESSED_DIR, document_id)
    os.makedirs(output_dir, exist_ok=True)
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text
        text = page.get_text("text")
        
        # Extract tables (using text blocks heuristic)
        tables = []
        try:
            table_data = page.find_tables()
            if table_data and table_data.tables:
                for table in table_data.tables:
                    table_text = ""
                    extracted = table.extract()
                    for row in extracted:
                        row_str = " | ".join([str(cell) if cell else "" for cell in row])
                        table_text += row_str + "\n"
                    if table_text.strip():
                        tables.append(table_text.strip())
        except Exception as e:
            logger.debug(f"Table extraction failed on page {page_num + 1}: {e}")
        
        # Extract images
        images = []
        image_list = page.get_images(full=True)
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    img_ext = base_image.get("ext", "png")
                    img_filename = f"page_{page_num + 1}_img_{img_idx + 1}.{img_ext}"
                    img_path = os.path.join(img_dir, img_filename)
                    
                    with open(img_path, "wb") as f:
                        f.write(base_image["image"])
                    
                    images.append({
                        "path": img_path,
                        "type": "embedded",
                        "width": base_image.get("width"),
                        "height": base_image.get("height"),
                    })
            except Exception as e:
                logger.debug(f"Image extraction failed: {e}")
        
        # Check if OCR is needed (very little text but page has content)
        ocr_text = None
        if len(text.strip()) < 50 and (images or page.get_pixmap().samples):
            ocr_text = await _run_ocr_on_page(page, page_num, output_dir)
        
        # Save page as image for viewer
        page_img_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        try:
            pix = page.get_pixmap(dpi=150)
            pix.save(page_img_path)
        except Exception:
            page_img_path = None
        
        pages_data.append({
            "page_number": page_num + 1,
            "text": text,
            "tables": tables,
            "images": images,
            "has_tables": len(tables) > 0,
            "has_images": len(images) > 0,
            "has_charts": False,  # Will be enhanced with vision analysis
            "ocr_text": ocr_text,
            "page_image_path": page_img_path,
        })
    
    doc.close()
    logger.info(f"PDF extracted: {len(pages_data)} pages")
    return pages_data


async def _run_ocr_on_page(page, page_num: int, output_dir: str) -> str:
    """Run OCR on a PDF page."""
    try:
        import pytesseract
        from PIL import Image
        import io
        
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        ocr_text = pytesseract.image_to_string(img)
        logger.debug(f"OCR on page {page_num + 1}: {len(ocr_text)} chars")
        return ocr_text
    except ImportError:
        logger.warning("pytesseract not installed, skipping OCR")
        return None
    except Exception as e:
        logger.warning(f"OCR failed on page {page_num + 1}: {e}")
        return None


async def extract_docx(file_path: str, document_id: str) -> List[Dict[str, Any]]:
    """Extract content from DOCX files."""
    from docx import Document as DocxDocument
    
    doc = DocxDocument(file_path)
    
    # DOCX doesn't have true pages, we treat the whole doc as sections
    full_text = []
    tables = []
    current_section = None
    
    for para in doc.paragraphs:
        if para.style and para.style.name and "Heading" in para.style.name:
            current_section = para.text
        full_text.append(para.text)
    
    # Extract tables
    for table in doc.tables:
        table_text = ""
        for row in table.rows:
            row_text = " | ".join([cell.text.strip() for cell in row.cells])
            table_text += row_text + "\n"
        if table_text.strip():
            tables.append(table_text.strip())
    
    # Simulate pages (every ~3000 chars)
    combined_text = "\n".join(full_text)
    pages_data = []
    chars_per_page = 3000
    
    for i in range(0, max(1, len(combined_text)), chars_per_page):
        page_text = combined_text[i:i + chars_per_page]
        page_num = (i // chars_per_page) + 1
        
        # Attach tables to first page
        page_tables = tables if page_num == 1 else []
        
        pages_data.append({
            "page_number": page_num,
            "text": page_text,
            "tables": page_tables,
            "images": [],
            "has_tables": len(page_tables) > 0,
            "has_images": False,
            "has_charts": False,
            "ocr_text": None,
        })
    
    if not pages_data:
        pages_data.append({
            "page_number": 1,
            "text": combined_text,
            "tables": tables,
            "images": [],
            "has_tables": len(tables) > 0,
            "has_images": False,
            "has_charts": False,
            "ocr_text": None,
        })
    
    logger.info(f"DOCX extracted: {len(pages_data)} pages")
    return pages_data


async def extract_pptx(file_path: str, document_id: str) -> List[Dict[str, Any]]:
    """Extract content from PPTX files."""
    from pptx import Presentation
    
    prs = Presentation(file_path)
    pages_data = []
    
    for slide_num, slide in enumerate(prs.slides, 1):
        text_parts = []
        tables = []
        
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text_parts.append(para.text)
            
            if shape.has_table:
                table_text = ""
                for row in shape.table.rows:
                    row_text = " | ".join([cell.text.strip() for cell in row.cells])
                    table_text += row_text + "\n"
                if table_text.strip():
                    tables.append(table_text.strip())
        
        slide_text = "\n".join(text_parts)
        
        pages_data.append({
            "page_number": slide_num,
            "text": slide_text,
            "tables": tables,
            "images": [],
            "has_tables": len(tables) > 0,
            "has_images": False,
            "has_charts": False,
            "ocr_text": None,
        })
    
    logger.info(f"PPTX extracted: {len(pages_data)} slides")
    return pages_data


async def extract_txt(file_path: str, document_id: str) -> List[Dict[str, Any]]:
    """Extract content from plain text files."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    # Split into pages by line count
    lines = content.split("\n")
    lines_per_page = 60
    pages_data = []
    
    for i in range(0, max(1, len(lines)), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        page_text = "\n".join(page_lines)
        page_num = (i // lines_per_page) + 1
        
        pages_data.append({
            "page_number": page_num,
            "text": page_text,
            "tables": [],
            "images": [],
            "has_tables": False,
            "has_images": False,
            "has_charts": False,
            "ocr_text": None,
        })
    
    if not pages_data:
        pages_data.append({
            "page_number": 1,
            "text": content,
            "tables": [],
            "images": [],
            "has_tables": False,
            "has_images": False,
            "has_charts": False,
            "ocr_text": None,
        })
    
    logger.info(f"TXT extracted: {len(pages_data)} pages")
    return pages_data


async def extract_image(file_path: str, document_id: str) -> List[Dict[str, Any]]:
    """Extract content from image files using OCR."""
    ocr_text = None
    try:
        import pytesseract
        from PIL import Image
        
        img = Image.open(file_path)
        ocr_text = pytesseract.image_to_string(img)
    except ImportError:
        logger.warning("pytesseract not installed")
    except Exception as e:
        logger.warning(f"OCR failed on image: {e}")
    
    return [{
        "page_number": 1,
        "text": ocr_text or "",
        "tables": [],
        "images": [{"path": file_path, "type": "uploaded", "width": None, "height": None}],
        "has_tables": False,
        "has_images": True,
        "has_charts": False,
        "ocr_text": ocr_text,
    }]
