"""Tests for audit logger."""

import pytest
from pathlib import Path
import tempfile

from home_ai.security.audit_logger import AuditLogger


class TestAuditLogger:
    """Test AuditLogger class."""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            yield logger
    
    def test_log_action(self, audit_logger):
        """Test logging an action."""
        entry = audit_logger.log_action(
            action_type="file",
            action="read",
            status="executed",
            details={"path": "/test/file.txt"}
        )
        
        assert entry.action_type == "file"
        assert entry.action == "read"
        assert entry.status == "executed"
        assert entry.details["path"] == "/test/file.txt"
        assert entry.entry_hash is not None
        assert entry.previous_hash is not None
    
    def test_hash_chain(self, audit_logger):
        """Test that hash chain is maintained."""
        entry1 = audit_logger.log_action("file", "read", "executed", {})
        entry2 = audit_logger.log_action("file", "write", "executed", {})
        entry3 = audit_logger.log_action("file", "delete", "blocked", {})
        
        assert entry2.previous_hash == entry1.entry_hash
        assert entry3.previous_hash == entry2.entry_hash
    
    def test_verify_chain(self, audit_logger):
        """Test chain verification."""
        for i in range(10):
            audit_logger.log_action("test", f"action_{i}", "executed", {})
        
        assert audit_logger.verify_chain() is True
    
    def test_redact_sensitive(self, audit_logger):
        """Test that sensitive data is redacted."""
        entry = audit_logger.log_action(
            action_type="auth",
            action="login",
            status="executed",
            details={
                "username": "testuser",
                "password": "secret123",
                "api_key": "sk-1234567890"
            }
        )
        
        assert entry.details["username"] == "testuser"
        assert entry.details["password"] == "[REDACTED]"
        assert entry.details["api_key"] == "[REDACTED]"
    
    def test_get_recent_entries(self, audit_logger):
        """Test getting recent entries."""
        for i in range(20):
            audit_logger.log_action("test", f"action_{i}", "executed", {})
        
        entries = audit_logger.get_recent_entries(count=10)
        
        assert len(entries) == 10
        assert entries[-1].action == "action_19"
    
    def test_search_entries(self, audit_logger):
        """Test searching entries."""
        audit_logger.log_action("file", "read", "executed", {})
        audit_logger.log_action("file", "write", "blocked", {})
        audit_logger.log_action("network", "request", "executed", {})
        
        file_entries = audit_logger.search_entries(action_type="file")
        assert len(file_entries) == 2
        
        blocked_entries = audit_logger.search_entries(status="blocked")
        assert len(blocked_entries) == 1
        assert blocked_entries[0].action == "write"
