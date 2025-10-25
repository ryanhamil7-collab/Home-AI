"""Screen capture system for computer vision."""

import mss
import numpy as np
from PIL import Image
from typing import Optional, Dict, Any
from loguru import logger


class ScreenCapture:
    """
    Screen capture system using mss.
    
    Captures screenshots for AI vision analysis.
    """
    
    def __init__(self, monitor: int = 1):
        """
        Initialize screen capture.
        
        Args:
            monitor: Monitor index (1 = primary, 0 = all monitors)
        """
        self.sct = mss.mss()
        self.monitor = monitor
        
        logger.info(f"ScreenCapture initialized for monitor {monitor}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        
        Returns:
            Numpy array (RGB) or None if capture fails
        """
        try:
            if self.monitor == 0:
                monitor = self.sct.monitors[0]  # All monitors
            else:
                monitor = self.sct.monitors[self.monitor]
            
            screenshot = self.sct.grab(monitor)
            
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            frame = np.array(img)
            
            return frame
        
        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return None
    
    def get_monitor_info(self) -> Dict[str, Any]:
        """Get information about available monitors."""
        monitors = []
        for i, monitor in enumerate(self.sct.monitors):
            monitors.append({
                "index": i,
                "width": monitor["width"],
                "height": monitor["height"],
                "left": monitor.get("left", 0),
                "top": monitor.get("top", 0)
            })
        
        return {
            "count": len(self.sct.monitors) - 1,  # Exclude "all monitors"
            "monitors": monitors,
            "current": self.monitor
        }
    
    def set_monitor(self, monitor: int):
        """Change active monitor."""
        self.monitor = monitor
        logger.info(f"Switched to monitor {monitor}")


def get_screen_capture(monitor: int = 1) -> ScreenCapture:
    """Get or create screen capture instance."""
    return ScreenCapture(monitor)
