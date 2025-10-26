"""Platform abstraction layer for cross-platform compatibility."""

import sys
from typing import Protocol, runtime_checkable

@runtime_checkable
class PlatformInterface(Protocol):
    """Protocol for platform-specific implementations."""
    
    def get_system_info(self) -> dict:
        """Get system information."""
        ...
    
    def list_processes(self) -> list:
        """List running processes."""
        ...
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        ...
    
    def list_windows(self) -> list:
        """List open windows."""
        ...
    
    def focus_window(self, window_id: str) -> bool:
        """Focus a window."""
        ...
    
    def resize_window(self, window_id: str, width: int, height: int) -> bool:
        """Resize a window."""
        ...
    
    def move_window(self, window_id: str, x: int, y: int) -> bool:
        """Move a window."""
        ...


def get_platform():
    """Get the appropriate platform implementation."""
    if sys.platform == "win32":
        from home_ai.platform.windows import WindowsPlatform
        return WindowsPlatform()
    elif sys.platform.startswith("linux"):
        from home_ai.platform.linux import LinuxPlatform
        return LinuxPlatform()
    elif sys.platform == "darwin":
        from home_ai.platform.macos import MacOSPlatform
        return MacOSPlatform()
    else:
        raise NotImplementedError(f"Platform {sys.platform} not supported")


__all__ = ["PlatformInterface", "get_platform"]
