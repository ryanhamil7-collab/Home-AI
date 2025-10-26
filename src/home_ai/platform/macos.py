"""macOS platform implementation (stub for future macOS support)."""

from loguru import logger


class MacOSPlatform:
    """macOS-specific platform implementation."""
    
    def __init__(self):
        """Initialize macOS platform."""
        logger.warning("macOS platform support is not yet implemented")
        raise NotImplementedError("macOS platform not supported yet")
    
    def get_system_info(self) -> dict:
        """Get system information."""
        raise NotImplementedError("macOS platform not supported")
    
    def list_processes(self) -> list:
        """List running processes."""
        raise NotImplementedError("macOS platform not supported")
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        raise NotImplementedError("macOS platform not supported")
    
    def list_windows(self) -> list:
        """List open windows."""
        raise NotImplementedError("macOS platform not supported")
    
    def focus_window(self, window_id: str) -> bool:
        """Focus a window."""
        raise NotImplementedError("macOS platform not supported")
    
    def resize_window(self, window_id: str, width: int, height: int) -> bool:
        """Resize a window."""
        raise NotImplementedError("macOS platform not supported")
    
    def move_window(self, window_id: str, x: int, y: int) -> bool:
        """Move a window."""
        raise NotImplementedError("macOS platform not supported")
