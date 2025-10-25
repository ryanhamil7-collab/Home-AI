"""Vision analysis using LLM."""

from typing import Dict, Any, List, Optional
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from loguru import logger

from home_ai.llm.ollama_client import get_ollama_client


class VisionAnalyzer:
    """
    Vision analyzer using LLM for screen understanding.
    
    Analyzes screenshots to understand UI elements and content.
    """
    
    def __init__(self, model: str = "llava:7b"):
        """
        Initialize vision analyzer.
        
        Args:
            model: Vision model to use
        """
        self.ollama = get_ollama_client()
        self.model = model
        self.last_analysis = None
        
        logger.info(f"VisionAnalyzer initialized with model: {model}")
    
    def analyze_frame(self, frame: np.ndarray, prompt: str = "Describe what you see on this screen") -> Dict[str, Any]:
        """
        Analyze a frame with LLM.
        
        Args:
            frame: Numpy array (RGB)
            prompt: Analysis prompt
        
        Returns:
            Analysis results
        """
        try:
            img = Image.fromarray(frame)
            
            max_size = 1280
            if img.width > max_size or img.height > max_size:
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                images=[img_base64],
                stream=False
            )
            
            analysis = {
                "success": True,
                "description": response.get("response", ""),
                "model": self.model,
                "prompt": prompt,
                "annotations": []  # Placeholder for future bounding boxes
            }
            
            self.last_analysis = analysis
            logger.info("Frame analyzed successfully")
            
            return analysis
        
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "description": "",
                "annotations": []
            }
    
    def find_element(self, frame: np.ndarray, element_description: str) -> Dict[str, Any]:
        """
        Find a UI element in the frame.
        
        Args:
            frame: Numpy array (RGB)
            element_description: Description of element to find
        
        Returns:
            Element location and info
        """
        prompt = f"Find and describe the location of: {element_description}. Provide coordinates if possible."
        
        analysis = self.analyze_frame(frame, prompt)
        
        return {
            "found": analysis.get("success", False),
            "description": analysis.get("description", ""),
            "coordinates": None  # Placeholder
        }
    
    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get last analysis results."""
        return self.last_analysis


_vision_analyzer: Optional[VisionAnalyzer] = None


def get_vision_analyzer(model: str = "llava:7b") -> VisionAnalyzer:
    """Get or create vision analyzer instance."""
    global _vision_analyzer
    if _vision_analyzer is None:
        _vision_analyzer = VisionAnalyzer(model)
    return _vision_analyzer
