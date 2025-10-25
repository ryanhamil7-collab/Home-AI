"""Emergency killswitch for immediate system pause."""

import sys
from typing import Optional, Callable
from loguru import logger

try:
    from pynput import keyboard
except ImportError:
    keyboard = None
    logger.warning("pynput not available, killswitch will not work")


class Killswitch:
    """
    Emergency killswitch that immediately pauses all operations.
    Activated by Ctrl+Alt+Shift+K by default.
    """
    
    def __init__(self, hotkey: str = "<ctrl>+<alt>+<shift>+k"):
        """
        Initialize killswitch.
        
        Args:
            hotkey: Hotkey combination (pynput format)
        """
        self.hotkey = hotkey
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._active = False
        self._on_activate_callback: Optional[Callable] = None
        
        logger.info(f"Killswitch initialized: {hotkey}")
    
    def set_callback(self, callback: Callable) -> None:
        """
        Set callback function to execute when killswitch is activated.
        
        Args:
            callback: Function to call on activation
        """
        self._on_activate_callback = callback
        logger.info("Killswitch callback set")
    
    def _on_activate(self) -> None:
        """Internal activation handler."""
        if self._active:
            logger.warning("Killswitch already active")
            return
        
        self._active = True
        logger.critical("=" * 60)
        logger.critical("EMERGENCY KILLSWITCH ACTIVATED")
        logger.critical("All operations paused immediately")
        logger.critical("=" * 60)
        
        if self._on_activate_callback:
            try:
                self._on_activate_callback()
            except Exception as e:
                logger.error(f"Killswitch callback error: {e}")
        
        try:
            from home_ai.security.policy_engine import get_policy_engine
            policy_engine = get_policy_engine()
            policy_engine.pause_all()
        except Exception as e:
            logger.error(f"Failed to pause policy engine: {e}")
    
    def start(self) -> bool:
        """
        Start listening for killswitch hotkey.
        
        Returns:
            True if started successfully
        """
        if keyboard is None:
            logger.error("pynput not available, cannot start killswitch")
            return False
        
        if self._listener is not None:
            logger.warning("Killswitch already started")
            return True
        
        try:
            self._listener = keyboard.GlobalHotKeys({
                self.hotkey: self._on_activate
            })
            self._listener.start()
            logger.info(f"Killswitch listening: {self.hotkey}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start killswitch: {e}")
            return False
    
    def stop(self) -> None:
        """Stop listening for killswitch hotkey."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
            logger.info("Killswitch stopped")
    
    def is_active(self) -> bool:
        """Check if killswitch is active."""
        return self._active
    
    def reset(self) -> None:
        """Reset killswitch (allow reactivation)."""
        self._active = False
        logger.info("Killswitch reset")
    
    def resume_system(self) -> None:
        """Resume system operations after killswitch."""
        if not self._active:
            logger.warning("Killswitch not active, nothing to resume")
            return
        
        try:
            from home_ai.security.policy_engine import get_policy_engine
            policy_engine = get_policy_engine()
            policy_engine.resume()
            
            self._active = False
            logger.info("System resumed after killswitch")
        
        except Exception as e:
            logger.error(f"Failed to resume system: {e}")


_killswitch: Optional[Killswitch] = None


def get_killswitch() -> Killswitch:
    """Get or create global killswitch instance."""
    global _killswitch
    if _killswitch is None:
        from home_ai.core.config import get_settings
        settings = get_settings()
        _killswitch = Killswitch(hotkey=settings.security.emergency_killswitch_key)
    return _killswitch
