"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import shutil

from home_ai.core.config import Settings, SystemToggles, FinancialToggles


class TestSettings:
    """Test Settings class."""
    
    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        
        assert settings.app_name == "Home AI"
        assert settings.version == "0.1.0"
        assert settings.debug is False
        
        assert settings.config_dir.exists()
        assert settings.data_dir.exists()
        assert settings.log_dir.exists()
        assert settings.backup_dir.exists()
    
    def test_system_toggles_defaults(self):
        """Test system toggles have safe defaults."""
        toggles = SystemToggles()
        
        assert toggles.allow_file_read is True
        assert toggles.allow_speaker_control is True
        
        assert toggles.allow_file_write is False
        assert toggles.allow_file_delete is False
        assert toggles.allow_process_termination is False
        assert toggles.allow_registry_write is False
        assert toggles.allow_internet_access is False
    
    def test_financial_toggles_defaults(self):
        """Test financial toggles have safe defaults."""
        toggles = FinancialToggles()
        
        assert toggles.master_financial_toggle is False
        
        assert toggles.paper_trading_only is True
        
        assert toggles.allow_balance_check is True
        assert toggles.allow_transaction_history is True
        
        assert toggles.allow_transfers is False
        assert toggles.allow_bill_pay is False
        
        assert toggles.max_single_transaction == 10.00
        assert toggles.daily_limit == 50.00
        assert toggles.monthly_limit == 500.00
    
    def test_save_and_load_settings(self):
        """Test saving and loading settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            settings_file = tmppath / "test_settings.json"
            
            settings = Settings()
            settings.system_toggles.allow_file_write = True
            settings.save_to_file(settings_file, encrypt=False)
            
            loaded = Settings.load_from_file(settings_file, encrypted=False)
            
            assert loaded.system_toggles.allow_file_write is True
            assert loaded.app_name == settings.app_name
