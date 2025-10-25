"""CustomTkinter toggle control panel for granular permission management."""

import threading
from typing import Optional, Dict, Any, Callable
from loguru import logger

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from home_ai.core.config import get_settings
from home_ai.security.policy_engine import ActionScope


class TogglePanel:
    """
    CustomTkinter-based toggle control panel.
    Always-visible panel for quick permission management.
    """
    
    def __init__(self, on_change: Optional[Callable[[str, bool], None]] = None):
        """
        Initialize toggle panel.
        
        Args:
            on_change: Callback when toggle changes (toggle_name, new_value)
        """
        if ctk is None:
            raise ImportError("customtkinter required: pip install customtkinter")
        
        self.settings = get_settings()
        self.on_change = on_change
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.window = ctk.CTk()
        self.window.title("Home AI - Toggle Controls")
        self.window.geometry("400x800")
        
        self.window.attributes("-topmost", True)
        
        self.toggles: Dict[str, ctk.CTkSwitch] = {}
        
        self._build_ui()
        
        logger.info("TogglePanel initialized")
    
    def _build_ui(self) -> None:
        """Build the toggle panel UI."""
        main_frame = ctk.CTkScrollableFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(
            main_frame,
            text="🔒 Permission Controls",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 20))
        
        self._add_section(main_frame, "🚨 Master Controls")
        self._add_toggle(
            main_frame,
            "killswitch_active",
            "Emergency Killswitch",
            self.settings.killswitch_active,
            color="red"
        )
        
        self._add_section(main_frame, "💻 System Operations")
        self._add_toggle(main_frame, "allow_file_read", "Read Files", 
                        self.settings.system_toggles.allow_file_read)
        self._add_toggle(main_frame, "allow_file_write", "Write Files", 
                        self.settings.system_toggles.allow_file_write, color="yellow")
        self._add_toggle(main_frame, "allow_file_delete", "Delete Files", 
                        self.settings.system_toggles.allow_file_delete, color="red")
        self._add_toggle(main_frame, "allow_process_termination", "Terminate Processes", 
                        self.settings.system_toggles.allow_process_termination, color="red")
        self._add_toggle(main_frame, "allow_process_creation", "Create Processes", 
                        self.settings.system_toggles.allow_process_creation, color="yellow")
        
        self._add_section(main_frame, "🌐 Network Access")
        self._add_toggle(main_frame, "allow_internet_access", "Internet Access", 
                        self.settings.system_toggles.allow_internet_access, color="yellow")
        self._add_toggle(main_frame, "allow_local_network", "Local Network", 
                        self.settings.system_toggles.allow_local_network)
        
        self._add_section(main_frame, "📝 Registry Access")
        self._add_toggle(main_frame, "allow_registry_read", "Read Registry", 
                        self.settings.system_toggles.allow_registry_read)
        self._add_toggle(main_frame, "allow_registry_write", "Write Registry", 
                        self.settings.system_toggles.allow_registry_write, color="red")
        
        self._add_section(main_frame, "🎥 Hardware Access")
        self._add_toggle(main_frame, "allow_camera_access", "Camera", 
                        self.settings.system_toggles.allow_camera_access, color="yellow")
        self._add_toggle(main_frame, "allow_microphone_access", "Microphone", 
                        self.settings.system_toggles.allow_microphone_access, color="yellow")
        self._add_toggle(main_frame, "allow_speaker_control", "Speakers", 
                        self.settings.system_toggles.allow_speaker_control)
        
        self._add_section(main_frame, "💰 Financial Operations")
        self._add_toggle(main_frame, "master_financial_toggle", "Master Financial Toggle", 
                        self.settings.financial_toggles.master_financial_toggle, color="red")
        self._add_toggle(main_frame, "allow_balance_check", "Check Balances", 
                        self.settings.financial_toggles.allow_balance_check)
        self._add_toggle(main_frame, "allow_transaction_history", "View History", 
                        self.settings.financial_toggles.allow_transaction_history)
        self._add_toggle(main_frame, "paper_trading_only", "Paper Trading Only", 
                        self.settings.financial_toggles.paper_trading_only)
        
        self._add_section(main_frame, "👁️ Computer Vision")
        self._add_toggle(main_frame, "vision_enabled", "Live Screen Capture", True)
        self._add_toggle(main_frame, "autonomous_navigation", "Autonomous Navigation", False, color="yellow")
        
        save_btn = ctk.CTkButton(
            main_frame,
            text="💾 Save Configuration",
            command=self._save_config,
            height=40,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20, fill="x")
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=(0, 10))
    
    def _add_section(self, parent: ctk.CTkFrame, title: str) -> None:
        """Add a section header."""
        label = ctk.CTkLabel(
            parent,
            text=title,
            font=("Arial", 16, "bold"),
            anchor="w"
        )
        label.pack(pady=(20, 10), fill="x")
    
    def _add_toggle(self, parent: ctk.CTkFrame, key: str, label: str, 
                    default: bool, color: str = "green") -> None:
        """
        Add a toggle switch.
        
        Args:
            parent: Parent frame
            key: Toggle key
            label: Display label
            default: Default value
            color: "green" (safe), "yellow" (caution), "red" (dangerous)
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        indicator_colors = {
            "green": "#2ecc71",
            "yellow": "#f39c12",
            "red": "#e74c3c"
        }
        
        indicator = ctk.CTkLabel(
            frame,
            text="●",
            font=("Arial", 20),
            text_color=indicator_colors.get(color, "#2ecc71"),
            width=30
        )
        indicator.pack(side="left", padx=(0, 10))
        
        label_widget = ctk.CTkLabel(
            frame,
            text=label,
            font=("Arial", 13),
            anchor="w"
        )
        label_widget.pack(side="left", fill="x", expand=True)
        
        switch = ctk.CTkSwitch(
            frame,
            text="",
            command=lambda: self._on_toggle_change(key, switch.get()),
            width=50
        )
        
        if default:
            switch.select()
        else:
            switch.deselect()
        
        switch.pack(side="right")
        
        self.toggles[key] = switch
    
    def _on_toggle_change(self, key: str, value: bool) -> None:
        """Handle toggle change."""
        logger.info(f"Toggle changed: {key} = {value}")
        
        self.status_label.configure(text=f"Changed: {key}")
        
        if self.on_change:
            self.on_change(key, value)
    
    def _save_config(self) -> None:
        """Save current configuration."""
        try:
            for key, switch in self.toggles.items():
                value = switch.get() == 1
                
                if key == "killswitch_active":
                    self.settings.killswitch_active = value
                elif key.startswith("allow_") or key in ["vision_enabled", "autonomous_navigation"]:
                    if hasattr(self.settings.system_toggles, key):
                        setattr(self.settings.system_toggles, key, value)
                elif key in ["master_financial_toggle", "allow_balance_check", 
                           "allow_transaction_history", "paper_trading_only"]:
                    if hasattr(self.settings.financial_toggles, key):
                        setattr(self.settings.financial_toggles, key, value)
            
            self.settings.save()
            
            self.status_label.configure(text="✅ Configuration saved!")
            logger.info("Configuration saved successfully")
        
        except Exception as e:
            self.status_label.configure(text=f"❌ Error: {e}")
            logger.error(f"Failed to save configuration: {e}")
    
    def get_toggle_value(self, key: str) -> bool:
        """Get current value of a toggle."""
        if key in self.toggles:
            return self.toggles[key].get() == 1
        return False
    
    def set_toggle_value(self, key: str, value: bool) -> None:
        """Set value of a toggle."""
        if key in self.toggles:
            if value:
                self.toggles[key].select()
            else:
                self.toggles[key].deselect()
    
    def run(self) -> None:
        """Run the toggle panel (blocking)."""
        logger.info("Starting toggle panel...")
        self.window.mainloop()
    
    def run_async(self) -> None:
        """Run the toggle panel in a separate thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        logger.info("Toggle panel started in background thread")


def create_toggle_panel(on_change: Optional[Callable[[str, bool], None]] = None) -> TogglePanel:
    """Create and return a toggle panel instance."""
    return TogglePanel(on_change=on_change)
