"""OCR (Optical Character Recognition) for text extraction from images."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


@dataclass
class TextRegion:
    """Detected text region."""
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


class OCREngine:
    """OCR engine for text extraction from screen captures."""
    
    def __init__(self):
        """Initialize OCR engine."""
        if pytesseract is None:
            logger.warning("pytesseract not available. OCR functionality limited.")
            logger.warning("Install with: pip install pytesseract")
            logger.warning("Also install Tesseract: https://github.com/tesseract-ocr/tesseract")
        
        self.available = pytesseract is not None
        
        if self.available:
            logger.info("OCR engine initialized")
    
    def extract_text(self, image: any) -> str:
        """
        Extract all text from an image.
        
        Args:
            image: PIL Image object
        
        Returns:
            Extracted text as string
        """
        if not self.available:
            return "[OCR not available - install pytesseract]"
        
        try:
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_text_regions(self, image: any) -> List[TextRegion]:
        """
        Extract text with bounding boxes.
        
        Args:
            image: PIL Image object
        
        Returns:
            List of TextRegion objects
        """
        if not self.available:
            return []
        
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:  # Only include non-empty text
                    confidence = float(data['conf'][i])
                    if confidence > 0:  # Only include confident detections
                        regions.append(TextRegion(
                            text=text,
                            confidence=confidence / 100.0,  # Normalize to 0-1
                            x=data['left'][i],
                            y=data['top'][i],
                            width=data['width'][i],
                            height=data['height'][i]
                        ))
            
            return regions
        
        except Exception as e:
            logger.error(f"OCR region extraction failed: {e}")
            return []
    
    def find_text(self, image: any, search_text: str) -> Optional[TextRegion]:
        """
        Find specific text in image.
        
        Args:
            image: PIL Image object
            search_text: Text to search for
        
        Returns:
            TextRegion if found, None otherwise
        """
        regions = self.extract_text_regions(image)
        
        search_lower = search_text.lower()
        for region in regions:
            if search_lower in region.text.lower():
                return region
        
        return None
    
    def extract_structured_data(self, image: any) -> Dict[str, Any]:
        """
        Extract structured data from image (tables, forms, etc.).
        
        Args:
            image: PIL Image object
        
        Returns:
            Dictionary with structured data
        """
        regions = self.extract_text_regions(image)
        
        rows = {}
        for region in regions:
            row_key = region.y // 20  # Group by 20px rows
            if row_key not in rows:
                rows[row_key] = []
            rows[row_key].append(region)
        
        for row_key in rows:
            rows[row_key].sort(key=lambda r: r.x)
        
        structured = {
            "rows": len(rows),
            "data": []
        }
        
        for row_key in sorted(rows.keys()):
            row_data = {
                "y": row_key * 20,
                "text": " ".join([r.text for r in rows[row_key]]),
                "regions": [
                    {
                        "text": r.text,
                        "x": r.x,
                        "confidence": r.confidence
                    }
                    for r in rows[row_key]
                ]
            }
            structured["data"].append(row_data)
        
        return structured


_ocr_engine: Optional[OCREngine] = None


def get_ocr_engine() -> OCREngine:
    """Get or create global OCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _ocr_engine


def extract_text(image: any) -> str:
    """Convenience function to extract text from image."""
    engine = get_ocr_engine()
    return engine.extract_text(image)


def find_text(image: any, search_text: str) -> Optional[TextRegion]:
    """Convenience function to find text in image."""
    engine = get_ocr_engine()
    return engine.find_text(image, search_text)
