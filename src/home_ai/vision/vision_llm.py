"""Vision-enabled LLM integration for screen understanding."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from home_ai.vision.screen_capture import ScreenFrame, get_screen_capture
from home_ai.llm.ollama_client import get_ollama_client


@dataclass
class VisionAnalysis:
    """Result of vision analysis."""
    description: str
    elements: List[Dict[str, Any]]
    suggestions: List[str]
    confidence: float


class VisionLLM:
    """
    Vision-enabled LLM for screen understanding and analysis.
    Combines screen capture with LLM vision capabilities.
    """
    
    def __init__(self, vision_model: str = "llava:7b"):
        """
        Initialize vision LLM.
        
        Args:
            vision_model: Vision-capable model (e.g., llava, bakllava)
        """
        self.vision_model = vision_model
        self.screen_capture = get_screen_capture()
        self.llm_client = get_ollama_client()
        
        self._ensure_vision_model()
        
        logger.info(f"VisionLLM initialized with model: {vision_model}")
    
    def _ensure_vision_model(self) -> bool:
        """Ensure vision model is available."""
        models = self.llm_client.list_models()
        model_names = [m.name for m in models]
        
        if self.vision_model not in model_names:
            logger.info(f"Vision model not found, pulling: {self.vision_model}")
            return self.llm_client.pull_model(self.vision_model)
        
        return True
    
    def analyze_screen(self, prompt: Optional[str] = None) -> VisionAnalysis:
        """
        Analyze current screen state.
        
        Args:
            prompt: Optional specific question about the screen
        
        Returns:
            VisionAnalysis with description and insights
        """
        frame = self.screen_capture.get_current_frame()
        if frame is None:
            frame = self.screen_capture.capture_frame()
        
        return self.analyze_frame(frame, prompt)
    
    def analyze_frame(self, frame: ScreenFrame, prompt: Optional[str] = None) -> VisionAnalysis:
        """
        Analyze a specific frame.
        
        Args:
            frame: ScreenFrame to analyze
            prompt: Optional specific question
        
        Returns:
            VisionAnalysis
        """
        if prompt is None:
            prompt = """Analyze this screenshot and provide:
1. A detailed description of what you see
2. List of UI elements (buttons, text fields, windows, etc.)
3. Suggestions for what actions could be taken
4. Any important information or warnings visible

Be specific and actionable."""
        
        image_base64 = frame.to_base64()
        
        
        logger.info("Analyzing screen with vision model...")
        
        analysis = VisionAnalysis(
            description="Screen analysis in progress. Vision model integration pending.",
            elements=[],
            suggestions=[
                "Enable vision model for detailed analysis",
                "Use OCR for text extraction",
                "Implement UI element detection"
            ],
            confidence=0.5
        )
        
        return analysis
    
    def find_element(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Find a UI element by description.
        
        Args:
            description: Description of element to find (e.g., "Submit button")
        
        Returns:
            Element info with coordinates, or None if not found
        """
        frame = self.screen_capture.get_current_frame()
        if frame is None:
            frame = self.screen_capture.capture_frame()
        
        prompt = f"Find the {description} on this screen. Provide its approximate coordinates and size."
        
        analysis = self.analyze_frame(frame, prompt)
        
        return None
    
    def read_text_at(self, x: int, y: int, width: int, height: int) -> str:
        """
        Read text from a specific region.
        
        Args:
            x, y: Top-left coordinates
            width, height: Region size
        
        Returns:
            Extracted text
        """
        region_frame = self.screen_capture.capture_region(x, y, width, height)
        
        from home_ai.vision.ocr import extract_text
        text = extract_text(region_frame.image)
        
        return text
    
    def get_screen_context(self) -> str:
        """
        Get current screen context for LLM.
        
        Returns:
            Text description of current screen state
        """
        analysis = self.analyze_screen()
        
        context = f"""Current Screen State:
{analysis.description}

Visible Elements:
{', '.join([str(e) for e in analysis.elements])}

Possible Actions:
{', '.join(analysis.suggestions)}
"""
        
        return context
    
    def continuous_monitoring(self, callback: callable) -> None:
        """
        Start continuous screen monitoring with callback.
        
        Args:
            callback: Function called with VisionAnalysis for each frame
        """
        def frame_callback(frame: ScreenFrame):
            analysis = self.analyze_frame(frame)
            callback(analysis)
        
        self.screen_capture.add_frame_callback(frame_callback)
        self.screen_capture.start_capture()
        
        logger.info("Continuous vision monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self.screen_capture.stop_capture()
        logger.info("Continuous vision monitoring stopped")


_vision_llm: Optional[VisionLLM] = None


def get_vision_llm() -> VisionLLM:
    """Get or create global vision LLM instance."""
    global _vision_llm
    if _vision_llm is None:
        _vision_llm = VisionLLM()
    return _vision_llm
