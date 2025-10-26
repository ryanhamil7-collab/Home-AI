"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from cryptography.fernet import Fernet
from loguru import logger


class LLMConfig(BaseModel):
    """LLM engine configuration."""
    preferred_model: str = "mistral:7b-instruct"
    fallback_models: List[str] = ["llama3.2:3b", "phi3:mini"]
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    context_window: int = 4096
    streaming: bool = True
    gpu_acceleration: bool = True
    auto_detect_gpu: bool = True


class GUIConfig(BaseModel):
    """GUI configuration."""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    toggle_panel_width: int = 300
    enable_system_tray: bool = True
    multi_monitor_support: bool = True


class SecurityConfig(BaseModel):
    """Security and safety configuration."""
    enable_audit_log: bool = True
    require_confirmation: bool = True
    screenshot_actions: bool = True
    sandbox_mode: bool = True
    rate_limit_actions_per_minute: int = 60
    session_timeout_minutes: int = 30
    emergency_killswitch_key: str = "ctrl+alt+shift+k"


class SystemToggles(BaseModel):
    """System-level toggle controls."""
    allow_process_termination: bool = False
    allow_process_creation: bool = False
    allow_service_control: bool = False
    allow_startup_modification: bool = False
    allow_file_read: bool = True
    allow_file_write: bool = False
    allow_file_delete: bool = False
    allow_folder_creation: bool = False
    allow_file_execution: bool = False
    allow_internet_access: bool = False
    allow_local_network: bool = False
    allow_registry_read: bool = False
    allow_registry_write: bool = False
    allow_camera_access: bool = False
    allow_microphone_access: bool = False
    allow_speaker_control: bool = True
    allow_usb_access: bool = False
    allow_bluetooth_control: bool = False


class FinancialToggles(BaseModel):
    """Financial safety controls."""
    master_financial_toggle: bool = False
    require_2fa_confirmation: bool = True
    require_biometric: bool = False
    paper_trading_only: bool = True
    allow_balance_check: bool = True
    allow_transaction_history: bool = True
    allow_transfers: bool = False
    allow_bill_pay: bool = False
    max_single_transaction: float = 10.00
    daily_limit: float = 50.00
    monthly_limit: float = 500.00
    cooldown_between_transactions: int = 300


class PathConfig(BaseModel):
    """Path configuration."""
    restricted_paths: List[str] = Field(default_factory=lambda: [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)"
    ])
    whitelisted_paths: List[str] = Field(default_factory=lambda: [
        "C:\\Users\\{username}\\Documents\\AI_Workspace"
    ])


class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    app_name: str = "Home AI"
    version: str = "0.1.0"
    debug: bool = False
    
    config_dir: Path = Path.home() / ".home_ai" / "config"
    data_dir: Path = Path.home() / ".home_ai" / "data"
    log_dir: Path = Path.home() / ".home_ai" / "logs"
    backup_dir: Path = Path.home() / ".home_ai" / "backups"
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    gui: GUIConfig = Field(default_factory=GUIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    system_toggles: SystemToggles = Field(default_factory=SystemToggles)
    financial_toggles: FinancialToggles = Field(default_factory=FinancialToggles)
    paths: PathConfig = Field(default_factory=PathConfig)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.config_dir, self.data_dir, self.log_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_to_file(self, filepath: Optional[Path] = None, encrypt: bool = True) -> None:
        """Save settings to file with optional encryption."""
        if filepath is None:
            filepath = self.config_dir / "settings.json"
        
        data = self.model_dump_json(indent=2)
        
        if encrypt:
            key_file = self.config_dir / ".key"
            if key_file.exists():
                key = key_file.read_bytes()
            else:
                key = Fernet.generate_key()
                key_file.write_bytes(key)
                key_file.chmod(0o600)  # Restrict permissions
            
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode())
            filepath.write_bytes(encrypted_data)
            logger.info(f"Settings saved (encrypted) to {filepath}")
        else:
            filepath.write_text(data)
            logger.info(f"Settings saved to {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: Optional[Path] = None, encrypted: bool = True) -> "Settings":
        """Load settings from file with optional decryption."""
        if filepath is None:
            config_dir = Path.home() / ".home_ai" / "config"
            filepath = config_dir / "settings.json"
        
        if not filepath.exists():
            logger.warning(f"Settings file not found at {filepath}, using defaults")
            return cls()
        
        if encrypted:
            key_file = filepath.parent / ".key"
            if not key_file.exists():
                logger.error("Encryption key not found")
                return cls()
            
            key = key_file.read_bytes()
            fernet = Fernet(key)
            encrypted_data = filepath.read_bytes()
            data = fernet.decrypt(encrypted_data).decode()
        else:
            data = filepath.read_text()
        
        settings_dict = json.loads(data)
        logger.info(f"Settings loaded from {filepath}")
        return cls(**settings_dict)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings.load_from_file()
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}, using defaults")
            _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from file."""
    global _settings
    _settings = None
    return get_settings()
