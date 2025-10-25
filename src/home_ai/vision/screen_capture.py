"""Live screen capture system for real-time desktop monitoring."""

import time
import threading
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

try:
    from PIL import Image
except ImportError:
    Image = None

from loguru import logger


@dataclass
class ScreenFrame:
    """Single screen capture frame."""
    timestamp: str
    image: any  # PIL Image
    width: int
    height: int
    monitor_index: int
    
    def to_base64(self, format: str = "PNG") -> str:
        """Convert image to base64 string."""
        if self.image is None:
            return ""
        
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def save(self, filepath: Path) -> None:
        """Save frame to file."""
        if self.image:
            self.image.save(filepath)


class LiveScreenCapture:
    """
    Live screen capture system for real-time desktop monitoring.
    Continuously captures screenshots for LLM vision analysis.
    """
    
    def __init__(self, fps: float = 1.0, monitor: int = 0):
        """
        Initialize live screen capture.
        
        Args:
            fps: Frames per second to capture (default 1.0)
            monitor: Monitor index to capture (0 = primary)
        """
        if mss is None:
            raise ImportError("mss library required: pip install mss")
        if Image is None:
            raise ImportError("Pillow library required: pip install Pillow")
        
        self.fps = fps
        self.monitor_index = monitor
        self.interval = 1.0 / fps
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_frame: Optional[ScreenFrame] = None
        self._frame_callbacks: List[Callable[[ScreenFrame], None]] = []
        
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        
        logger.info(f"LiveScreenCapture initialized: {fps} FPS, monitor {monitor}")
        logger.info(f"Available monitors: {len(self.monitors) - 1}")  # -1 for "all monitors"
    
    def get_monitor_info(self) -> List[dict]:
        """Get information about available monitors."""
        info = []
        for i, monitor in enumerate(self.monitors[1:], 1):  # Skip "all monitors"
            info.append({
                "index": i - 1,
                "width": monitor["width"],
                "height": monitor["height"],
                "left": monitor["left"],
                "top": monitor["top"]
            })
        return info
    
    def capture_frame(self, monitor: Optional[int] = None) -> ScreenFrame:
        """
        Capture a single frame from the specified monitor.
        
        Args:
            monitor: Monitor index (None for default)
        
        Returns:
            ScreenFrame object
        """
        if monitor is None:
            monitor = self.monitor_index
        
        monitor_config = self.monitors[monitor + 1]  # +1 because index 0 is "all monitors"
        screenshot = self.sct.grab(monitor_config)
        
        img = Image.frombytes(
            "RGB",
            (screenshot.width, screenshot.height),
            screenshot.rgb
        )
        
        frame = ScreenFrame(
            timestamp=datetime.now().isoformat(),
            image=img,
            width=screenshot.width,
            height=screenshot.height,
            monitor_index=monitor
        )
        
        return frame
    
    def start_capture(self) -> None:
        """Start continuous screen capture in background thread."""
        if self._running:
            logger.warning("Screen capture already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Live screen capture started: {self.fps} FPS")
    
    def stop_capture(self) -> None:
        """Stop continuous screen capture."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Live screen capture stopped")
    
    def _capture_loop(self) -> None:
        """Background capture loop."""
        while self._running:
            try:
                start_time = time.time()
                
                frame = self.capture_frame()
                self._current_frame = frame
                
                for callback in self._frame_callbacks:
                    try:
                        callback(frame)
                    except Exception as e:
                        logger.error(f"Frame callback error: {e}")
                
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)
                time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(self.interval)
    
    def get_current_frame(self) -> Optional[ScreenFrame]:
        """Get the most recent captured frame."""
        return self._current_frame
    
    def add_frame_callback(self, callback: Callable[[ScreenFrame], None]) -> None:
        """
        Add callback to be called for each captured frame.
        
        Args:
            callback: Function that takes ScreenFrame as argument
        """
        self._frame_callbacks.append(callback)
        logger.info(f"Frame callback added: {callback.__name__}")
    
    def remove_frame_callback(self, callback: Callable[[ScreenFrame], None]) -> None:
        """Remove frame callback."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)
            logger.info(f"Frame callback removed: {callback.__name__}")
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> ScreenFrame:
        """
        Capture a specific region of the screen.
        
        Args:
            x: Left coordinate
            y: Top coordinate
            width: Region width
            height: Region height
        
        Returns:
            ScreenFrame of the region
        """
        region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        
        screenshot = self.sct.grab(region)
        img = Image.frombytes(
            "RGB",
            (screenshot.width, screenshot.height),
            screenshot.rgb
        )
        
        return ScreenFrame(
            timestamp=datetime.now().isoformat(),
            image=img,
            width=width,
            height=height,
            monitor_index=self.monitor_index
        )
    
    def capture_window(self, window_title: str) -> Optional[ScreenFrame]:
        """
        Capture a specific window by title.
        
        Args:
            window_title: Window title to capture
        
        Returns:
            ScreenFrame of the window, or None if not found
        """
        try:
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                logger.warning(f"Window not found: {window_title}")
                return None
            
            window = windows[0]
            return self.capture_region(
                window.left,
                window.top,
                window.width,
                window.height
            )
        
        except Exception as e:
            logger.error(f"Failed to capture window: {e}")
            return None
    
    def set_fps(self, fps: float) -> None:
        """Change capture frame rate."""
        self.fps = fps
        self.interval = 1.0 / fps
        logger.info(f"FPS changed to: {fps}")
    
    def get_stats(self) -> dict:
        """Get capture statistics."""
        return {
            "running": self._running,
            "fps": self.fps,
            "monitor": self.monitor_index,
            "callbacks": len(self._frame_callbacks),
            "current_frame": self._current_frame is not None
        }


_screen_capture: Optional[LiveScreenCapture] = None


def get_screen_capture() -> LiveScreenCapture:
    """Get or create global screen capture instance."""
    global _screen_capture
    if _screen_capture is None:
        _screen_capture = LiveScreenCapture(fps=1.0)
    return _screen_capture
