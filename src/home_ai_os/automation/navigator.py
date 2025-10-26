"""Autonomous navigation system for desktop control."""

import time
from typing import Optional, Tuple, List
from dataclasses import dataclass
from loguru import logger

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from pynput.mouse import Controller as MouseController, Button
    from pynput.keyboard import Controller as KeyboardController, Key
except ImportError:
    MouseController = None
    KeyboardController = None

from home_ai_os.security.policy_engine import (
    get_policy_engine, Action, ActionScope, ActionRisk
)
from home_ai_os.security.audit_logger import get_audit_logger
from home_ai_os.vision.screen_capture import get_screen_capture
from home_ai_os.vision.ocr import find_text


@dataclass
class NavigationAction:
    """Navigation action result."""
    success: bool
    action_type: str
    details: dict
    message: str


class AutonomousNavigator:
    """
    Autonomous navigation system for desktop control.
    Enables LLM to control mouse, keyboard, and navigate UI.
    """
    
    def __init__(self):
        """Initialize autonomous navigator."""
        if pyautogui is None:
            raise ImportError("pyautogui required: pip install pyautogui")
        
        self.policy_engine = get_policy_engine()
        self.audit_logger = get_audit_logger()
        self.screen_capture = get_screen_capture()
        
        if MouseController:
            self.mouse = MouseController()
        else:
            self.mouse = None
            logger.warning("pynput mouse controller not available")
        
        if KeyboardController:
            self.keyboard = KeyboardController()
        else:
            self.keyboard = None
            logger.warning("pynput keyboard controller not available")
        
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Pause between actions
        
        self.screen_width, self.screen_height = pyautogui.size()
        
        logger.info(f"AutonomousNavigator initialized: {self.screen_width}x{self.screen_height}")
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> NavigationAction:
        """
        Move mouse to coordinates.
        
        Args:
            x, y: Target coordinates
            duration: Movement duration in seconds
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="move_mouse",
            risk=ActionRisk.SAFE,
            params={"x": x, "y": y},
            description=f"Move mouse to ({x}, {y})",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="move_mouse",
                details={"x": x, "y": y},
                message=f"Blocked: {reason}"
            )
        
        try:
            pyautogui.moveTo(x, y, duration=duration)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="move_mouse",
                status="executed",
                details={"x": x, "y": y}
            )
            
            return NavigationAction(
                success=True,
                action_type="move_mouse",
                details={"x": x, "y": y},
                message=f"Mouse moved to ({x}, {y})"
            )
        
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return NavigationAction(
                success=False,
                action_type="move_mouse",
                details={"x": x, "y": y, "error": str(e)},
                message=f"Failed: {e}"
            )
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = "left", clicks: int = 1) -> NavigationAction:
        """
        Click at coordinates or current position.
        
        Args:
            x, y: Coordinates (None for current position)
            button: "left", "right", or "middle"
            clicks: Number of clicks (1 for single, 2 for double)
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="mouse_click",
            risk=ActionRisk.LOW,
            params={"x": x, "y": y, "button": button, "clicks": clicks},
            description=f"Click {button} button at ({x}, {y})",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="click",
                details={"x": x, "y": y, "button": button},
                message=f"Blocked: {reason}"
            )
        
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="click",
                status="executed",
                details={"x": x, "y": y, "button": button, "clicks": clicks}
            )
            
            return NavigationAction(
                success=True,
                action_type="click",
                details={"x": x, "y": y, "button": button, "clicks": clicks},
                message=f"Clicked {button} button"
            )
        
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return NavigationAction(
                success=False,
                action_type="click",
                details={"error": str(e)},
                message=f"Failed: {e}"
            )
    
    def type_text(self, text: str, interval: float = 0.05) -> NavigationAction:
        """
        Type text at current cursor position.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="type_text",
            risk=ActionRisk.LOW,
            params={"text": text[:50] + "..." if len(text) > 50 else text},
            description=f"Type text: {text[:50]}...",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="type_text",
                details={"length": len(text)},
                message=f"Blocked: {reason}"
            )
        
        try:
            pyautogui.write(text, interval=interval)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="type_text",
                status="executed",
                details={"length": len(text), "preview": text[:50]}
            )
            
            return NavigationAction(
                success=True,
                action_type="type_text",
                details={"length": len(text)},
                message=f"Typed {len(text)} characters"
            )
        
        except Exception as e:
            logger.error(f"Type text failed: {e}")
            return NavigationAction(
                success=False,
                action_type="type_text",
                details={"error": str(e)},
                message=f"Failed: {e}"
            )
    
    def press_key(self, key: str) -> NavigationAction:
        """
        Press a keyboard key.
        
        Args:
            key: Key name (e.g., "enter", "tab", "esc", "ctrl", "alt")
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="press_key",
            risk=ActionRisk.SAFE,
            params={"key": key},
            description=f"Press key: {key}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="press_key",
                details={"key": key},
                message=f"Blocked: {reason}"
            )
        
        try:
            pyautogui.press(key)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="press_key",
                status="executed",
                details={"key": key}
            )
            
            return NavigationAction(
                success=True,
                action_type="press_key",
                details={"key": key},
                message=f"Pressed key: {key}"
            )
        
        except Exception as e:
            logger.error(f"Press key failed: {e}")
            return NavigationAction(
                success=False,
                action_type="press_key",
                details={"key": key, "error": str(e)},
                message=f"Failed: {e}"
            )
    
    def hotkey(self, *keys: str) -> NavigationAction:
        """
        Press a hotkey combination.
        
        Args:
            *keys: Keys to press together (e.g., "ctrl", "c")
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="hotkey",
            risk=ActionRisk.LOW,
            params={"keys": list(keys)},
            description=f"Press hotkey: {'+'.join(keys)}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="hotkey",
                details={"keys": list(keys)},
                message=f"Blocked: {reason}"
            )
        
        try:
            pyautogui.hotkey(*keys)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="hotkey",
                status="executed",
                details={"keys": list(keys)}
            )
            
            return NavigationAction(
                success=True,
                action_type="hotkey",
                details={"keys": list(keys)},
                message=f"Pressed hotkey: {'+'.join(keys)}"
            )
        
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            return NavigationAction(
                success=False,
                action_type="hotkey",
                details={"keys": list(keys), "error": str(e)},
                message=f"Failed: {e}"
            )
    
    def find_and_click(self, text: str, button: str = "left") -> NavigationAction:
        """
        Find text on screen and click it.
        
        Args:
            text: Text to find
            button: Mouse button to click
        
        Returns:
            NavigationAction result
        """
        frame = self.screen_capture.capture_frame()
        
        text_region = find_text(frame.image, text)
        
        if text_region is None:
            return NavigationAction(
                success=False,
                action_type="find_and_click",
                details={"text": text},
                message=f"Text not found: {text}"
            )
        
        center_x = text_region.x + text_region.width // 2
        center_y = text_region.y + text_region.height // 2
        
        return self.click(center_x, center_y, button=button)
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> NavigationAction:
        """
        Scroll at position.
        
        Args:
            clicks: Positive for up, negative for down
            x, y: Position to scroll at (None for current)
        
        Returns:
            NavigationAction result
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="scroll",
            risk=ActionRisk.SAFE,
            params={"clicks": clicks, "x": x, "y": y},
            description=f"Scroll {clicks} clicks",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            return NavigationAction(
                success=False,
                action_type="scroll",
                details={"clicks": clicks},
                message=f"Blocked: {reason}"
            )
        
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x, y)
            else:
                pyautogui.scroll(clicks)
            
            self.audit_logger.log_action(
                action_type="navigation",
                action="scroll",
                status="executed",
                details={"clicks": clicks, "x": x, "y": y}
            )
            
            return NavigationAction(
                success=True,
                action_type="scroll",
                details={"clicks": clicks},
                message=f"Scrolled {clicks} clicks"
            )
        
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return NavigationAction(
                success=False,
                action_type="scroll",
                details={"error": str(e)},
                message=f"Failed: {e}"
            )
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen size."""
        return (self.screen_width, self.screen_height)


_navigator: Optional[AutonomousNavigator] = None


def get_navigator() -> AutonomousNavigator:
    """Get or create global navigator instance."""
    global _navigator
    if _navigator is None:
        _navigator = AutonomousNavigator()
    return _navigator
