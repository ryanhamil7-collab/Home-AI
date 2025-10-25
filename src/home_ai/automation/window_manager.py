"""Window management for controlling application windows."""

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import pywinauto
    from pywinauto import Desktop
except ImportError:
    pywinauto = None

from home_ai.security.policy_engine import (
    get_policy_engine, Action, ActionScope, ActionRisk
)
from home_ai.security.audit_logger import get_audit_logger


@dataclass
class WindowInfo:
    """Information about a window."""
    title: str
    handle: int
    x: int
    y: int
    width: int
    height: int
    is_active: bool
    is_minimized: bool
    is_maximized: bool


class WindowManager:
    """
    Window management system for controlling application windows.
    Provides safe window manipulation capabilities.
    """
    
    def __init__(self):
        """Initialize window manager."""
        if gw is None:
            raise ImportError("pygetwindow required: pip install pygetwindow")
        
        self.policy_engine = get_policy_engine()
        self.audit_logger = get_audit_logger()
        
        logger.info("WindowManager initialized")
    
    def list_windows(self, include_minimized: bool = True) -> List[WindowInfo]:
        """
        List all visible windows.
        
        Args:
            include_minimized: Include minimized windows
        
        Returns:
            List of WindowInfo objects
        """
        windows = []
        
        try:
            for window in gw.getAllWindows():
                if not include_minimized and window.isMinimized:
                    continue
                
                if window.title:  # Skip windows without titles
                    windows.append(WindowInfo(
                        title=window.title,
                        handle=window._hWnd if hasattr(window, '_hWnd') else 0,
                        x=window.left,
                        y=window.top,
                        width=window.width,
                        height=window.height,
                        is_active=window.isActive,
                        is_minimized=window.isMinimized,
                        is_maximized=window.isMaximized
                    ))
        
        except Exception as e:
            logger.error(f"Failed to list windows: {e}")
        
        return windows
    
    def find_window(self, title: str, exact: bool = False) -> Optional[WindowInfo]:
        """
        Find a window by title.
        
        Args:
            title: Window title to search for
            exact: Require exact match (default: partial match)
        
        Returns:
            WindowInfo if found, None otherwise
        """
        try:
            if exact:
                windows = gw.getWindowsWithTitle(title)
            else:
                all_windows = gw.getAllWindows()
                windows = [w for w in all_windows if title.lower() in w.title.lower()]
            
            if windows:
                window = windows[0]
                return WindowInfo(
                    title=window.title,
                    handle=window._hWnd if hasattr(window, '_hWnd') else 0,
                    x=window.left,
                    y=window.top,
                    width=window.width,
                    height=window.height,
                    is_active=window.isActive,
                    is_minimized=window.isMinimized,
                    is_maximized=window.isMaximized
                )
        
        except Exception as e:
            logger.error(f"Failed to find window: {e}")
        
        return None
    
    def activate_window(self, title: str) -> bool:
        """
        Activate (bring to front) a window.
        
        Args:
            title: Window title
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="activate_window",
            risk=ActionRisk.SAFE,
            params={"title": title},
            description=f"Activate window: {title}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Window activation blocked: {reason}")
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].activate()
                
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="activate",
                    status="executed",
                    details={"title": title}
                )
                
                logger.info(f"Window activated: {title}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to activate window: {e}")
        
        return False
    
    def resize_window(self, title: str, width: int, height: int) -> bool:
        """
        Resize a window.
        
        Args:
            title: Window title
            width: New width
            height: New height
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="resize_window",
            risk=ActionRisk.SAFE,
            params={"title": title, "width": width, "height": height},
            description=f"Resize window: {title}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Window resize blocked: {reason}")
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].resizeTo(width, height)
                
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="resize",
                    status="executed",
                    details={"title": title, "width": width, "height": height}
                )
                
                logger.info(f"Window resized: {title} to {width}x{height}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to resize window: {e}")
        
        return False
    
    def move_window(self, title: str, x: int, y: int) -> bool:
        """
        Move a window to coordinates.
        
        Args:
            title: Window title
            x, y: New position
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="move_window",
            risk=ActionRisk.SAFE,
            params={"title": title, "x": x, "y": y},
            description=f"Move window: {title}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Window move blocked: {reason}")
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].moveTo(x, y)
                
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="move",
                    status="executed",
                    details={"title": title, "x": x, "y": y}
                )
                
                logger.info(f"Window moved: {title} to ({x}, {y})")
                return True
        
        except Exception as e:
            logger.error(f"Failed to move window: {e}")
        
        return False
    
    def minimize_window(self, title: str) -> bool:
        """Minimize a window."""
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="minimize_window",
            risk=ActionRisk.SAFE,
            params={"title": title},
            description=f"Minimize window: {title}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].minimize()
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="minimize",
                    status="executed",
                    details={"title": title}
                )
                return True
        except Exception as e:
            logger.error(f"Failed to minimize window: {e}")
        
        return False
    
    def maximize_window(self, title: str) -> bool:
        """Maximize a window."""
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="maximize_window",
            risk=ActionRisk.SAFE,
            params={"title": title},
            description=f"Maximize window: {title}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].maximize()
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="maximize",
                    status="executed",
                    details={"title": title}
                )
                return True
        except Exception as e:
            logger.error(f"Failed to maximize window: {e}")
        
        return False
    
    def close_window(self, title: str) -> bool:
        """
        Close a window.
        
        Args:
            title: Window title
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="close_window",
            risk=ActionRisk.LOW,
            params={"title": title},
            description=f"Close window: {title}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Window close blocked: {reason}")
            return False
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].close()
                
                self.audit_logger.log_action(
                    action_type="window_management",
                    action="close",
                    status="executed",
                    details={"title": title}
                )
                
                logger.info(f"Window closed: {title}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to close window: {e}")
        
        return False
    
    def snap_window(self, title: str, position: str) -> bool:
        """
        Snap window to screen position.
        
        Args:
            title: Window title
            position: "left", "right", "top", "bottom"
        
        Returns:
            True if successful
        """
        try:
            import pyautogui
            
            screen_width, screen_height = pyautogui.size()
            
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return False
            
            window = windows[0]
            
            if position == "left":
                window.moveTo(0, 0)
                window.resizeTo(screen_width // 2, screen_height)
            elif position == "right":
                window.moveTo(screen_width // 2, 0)
                window.resizeTo(screen_width // 2, screen_height)
            elif position == "top":
                window.moveTo(0, 0)
                window.resizeTo(screen_width, screen_height // 2)
            elif position == "bottom":
                window.moveTo(0, screen_height // 2)
                window.resizeTo(screen_width, screen_height // 2)
            else:
                return False
            
            self.audit_logger.log_action(
                action_type="window_management",
                action="snap",
                status="executed",
                details={"title": title, "position": position}
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to snap window: {e}")
            return False
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get currently active window."""
        try:
            window = gw.getActiveWindow()
            if window:
                return WindowInfo(
                    title=window.title,
                    handle=window._hWnd if hasattr(window, '_hWnd') else 0,
                    x=window.left,
                    y=window.top,
                    width=window.width,
                    height=window.height,
                    is_active=True,
                    is_minimized=window.isMinimized,
                    is_maximized=window.isMaximized
                )
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
        
        return None


_window_manager: Optional[WindowManager] = None


def get_window_manager() -> WindowManager:
    """Get or create global window manager instance."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager
