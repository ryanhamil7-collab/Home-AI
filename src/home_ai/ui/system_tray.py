"""System tray integration for quick access to Home AI controls."""

import threading
from typing import Optional, Callable
from pathlib import Path
from loguru import logger

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Image = None

from home_ai.core.config import get_settings
from home_ai.core.killswitch import get_killswitch


class SystemTray:
    """
    System tray application for Home AI.
    Provides quick access to controls and status.
    """
    
    def __init__(self, 
                 on_show_dashboard: Optional[Callable] = None,
                 on_show_toggles: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None):
        """
        Initialize system tray.
        
        Args:
            on_show_dashboard: Callback to show main dashboard
            on_show_toggles: Callback to show toggle panel
            on_exit: Callback on exit
        """
        if pystray is None:
            raise ImportError("pystray required: pip install pystray")
        
        self.settings = get_settings()
        self.killswitch = get_killswitch()
        
        self.on_show_dashboard = on_show_dashboard
        self.on_show_toggles = on_show_toggles
        self.on_exit = on_exit
        
        self.icon: Optional[pystray.Icon] = None
        self._running = False
        
        logger.info("SystemTray initialized")
    
    def _create_icon_image(self) -> Image:
        """Create system tray icon image."""
        width = 64
        height = 64
        
        image = Image.new('RGB', (width, height), color='#2c3e50')
        draw = ImageDraw.Draw(image)
        
        draw.ellipse([8, 8, 56, 56], fill='#3498db', outline='#2980b9')
        
        draw.text((20, 20), "AI", fill='white')
        
        return image
    
    def _create_menu(self) -> pystray.Menu:
        """Create system tray menu."""
        return pystray.Menu(
            item(
                '🏠 Show Dashboard',
                self._show_dashboard,
                default=True
            ),
            item(
                '🎛️ Toggle Controls',
                self._show_toggles
            ),
            pystray.Menu.SEPARATOR,
            item(
                '📊 Status',
                pystray.Menu(
                    item(
                        f'Killswitch: {"🔴 ACTIVE" if self.killswitch.is_active() else "🟢 Inactive"}',
                        None,
                        enabled=False
                    ),
                    item(
                        f'File Write: {"✅" if self.settings.system_toggles.allow_file_write else "❌"}',
                        None,
                        enabled=False
                    ),
                    item(
                        f'Network: {"✅" if self.settings.system_toggles.allow_internet_access else "❌"}',
                        None,
                        enabled=False
                    ),
                    item(
                        f'Financial: {"✅" if self.settings.financial_toggles.master_financial_toggle else "❌"}',
                        None,
                        enabled=False
                    )
                )
            ),
            item(
                '⚡ Quick Actions',
                pystray.Menu(
                    item(
                        '🔴 Activate Killswitch',
                        self._activate_killswitch
                    ),
                    item(
                        '🟢 Deactivate Killswitch',
                        self._deactivate_killswitch
                    ),
                    pystray.Menu.SEPARATOR,
                    item(
                        '🔒 Lock Financial',
                        self._lock_financial
                    ),
                    item(
                        '🔓 Unlock Financial',
                        self._unlock_financial
                    ),
                    pystray.Menu.SEPARATOR,
                    item(
                        '📸 Take Screenshot',
                        self._take_screenshot
                    )
                )
            ),
            pystray.Menu.SEPARATOR,
            item(
                '📋 View Logs',
                self._view_logs
            ),
            item(
                '⚙️ Settings',
                self._show_settings
            ),
            pystray.Menu.SEPARATOR,
            item(
                '❌ Exit',
                self._exit
            )
        )
    
    def _show_dashboard(self, icon, item) -> None:
        """Show main dashboard."""
        logger.info("Show dashboard requested from tray")
        if self.on_show_dashboard:
            self.on_show_dashboard()
    
    def _show_toggles(self, icon, item) -> None:
        """Show toggle control panel."""
        logger.info("Show toggles requested from tray")
        if self.on_show_toggles:
            self.on_show_toggles()
    
    def _activate_killswitch(self, icon, item) -> None:
        """Activate emergency killswitch."""
        logger.warning("Killswitch activated from tray")
        self.killswitch.activate()
        self._update_menu()
    
    def _deactivate_killswitch(self, icon, item) -> None:
        """Deactivate killswitch."""
        logger.info("Killswitch deactivated from tray")
        self.killswitch.deactivate()
        self._update_menu()
    
    def _lock_financial(self, icon, item) -> None:
        """Lock financial operations."""
        logger.info("Financial operations locked from tray")
        self.settings.financial_toggles.master_financial_toggle = False
        self.settings.save()
        self._update_menu()
    
    def _unlock_financial(self, icon, item) -> None:
        """Unlock financial operations."""
        logger.warning("Financial operations unlocked from tray")
        self.settings.financial_toggles.master_financial_toggle = True
        self.settings.save()
        self._update_menu()
    
    def _take_screenshot(self, icon, item) -> None:
        """Take a screenshot."""
        logger.info("Screenshot requested from tray")
        try:
            from home_ai.vision.screen_capture import get_screen_capture
            
            screen_capture = get_screen_capture()
            frame = screen_capture.capture_frame()
            
            screenshots_dir = Path.home() / "Documents" / "HomeAI" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = screenshots_dir / f"screenshot_{frame.timestamp.replace(':', '-')}.png"
            frame.save(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
        
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
    
    def _view_logs(self, icon, item) -> None:
        """Open logs directory."""
        logger.info("View logs requested from tray")
        try:
            import subprocess
            import platform
            
            logs_dir = Path.home() / ".home_ai" / "logs"
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(logs_dir)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(logs_dir)])
            else:
                subprocess.run(["xdg-open", str(logs_dir)])
        
        except Exception as e:
            logger.error(f"Failed to open logs: {e}")
    
    def _show_settings(self, icon, item) -> None:
        """Show settings."""
        logger.info("Settings requested from tray")
    
    def _exit(self, icon, item) -> None:
        """Exit application."""
        logger.info("Exit requested from tray")
        self.stop()
        if self.on_exit:
            self.on_exit()
    
    def _update_menu(self) -> None:
        """Update menu to reflect current state."""
        if self.icon:
            self.icon.menu = self._create_menu()
    
    def start(self) -> None:
        """Start system tray (blocking)."""
        if self._running:
            logger.warning("System tray already running")
            return
        
        self._running = True
        
        image = self._create_icon_image()
        menu = self._create_menu()
        
        self.icon = pystray.Icon(
            "home_ai",
            image,
            "Home AI - Windows LLM Control",
            menu
        )
        
        logger.info("Starting system tray...")
        self.icon.run()
    
    def start_async(self) -> None:
        """Start system tray in background thread."""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        logger.info("System tray started in background thread")
    
    def stop(self) -> None:
        """Stop system tray."""
        if self.icon:
            self.icon.stop()
        self._running = False
        logger.info("System tray stopped")
    
    def is_running(self) -> bool:
        """Check if system tray is running."""
        return self._running


_system_tray: Optional[SystemTray] = None


def get_system_tray(
    on_show_dashboard: Optional[Callable] = None,
    on_show_toggles: Optional[Callable] = None,
    on_exit: Optional[Callable] = None
) -> SystemTray:
    """Get or create global system tray instance."""
    global _system_tray
    if _system_tray is None:
        _system_tray = SystemTray(
            on_show_dashboard=on_show_dashboard,
            on_show_toggles=on_show_toggles,
            on_exit=on_exit
        )
    return _system_tray
