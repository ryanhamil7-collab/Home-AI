"""Tests for policy engine."""

import pytest

from home_ai.security.policy_engine import (
    PolicyEngine, Action, ActionScope, ActionRisk
)
from home_ai.core.config import Settings


class TestPolicyEngine:
    """Test PolicyEngine class."""
    
    @pytest.fixture
    def policy_engine(self):
        """Create policy engine for testing."""
        return PolicyEngine()
    
    def test_deny_by_default(self, policy_engine):
        """Test that dangerous operations are denied by default."""
        action = Action(
            scope=ActionScope.FILE,
            operation="write",
            risk=ActionRisk.MEDIUM,
            params={"path": "C:\\Users\\test\\Documents\\test.txt"},
            description="Write to file"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is False
        assert "disabled" in reason.lower()
    
    def test_allow_safe_operations(self, policy_engine):
        """Test that safe operations are allowed."""
        action = Action(
            scope=ActionScope.FILE,
            operation="read",
            risk=ActionRisk.SAFE,
            params={"path": "C:\\Users\\test\\Documents\\test.txt"},
            description="Read file"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is True
    
    def test_restricted_paths(self, policy_engine):
        """Test that restricted paths are blocked."""
        action = Action(
            scope=ActionScope.FILE,
            operation="read",
            risk=ActionRisk.SAFE,
            params={"path": "C:\\Windows\\System32\\test.txt"},
            description="Read system file"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is False
        assert "restricted" in reason.lower()
    
    def test_killswitch_blocks_all(self, policy_engine):
        """Test that killswitch blocks all operations."""
        policy_engine.pause_all()
        
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="monitor",
            risk=ActionRisk.SAFE,
            params={},
            description="Monitor system"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is False
        assert "killswitch" in reason.lower() or "paused" in reason.lower()
    
    def test_financial_master_toggle(self, policy_engine):
        """Test that financial master toggle blocks all financial ops."""
        action = Action(
            scope=ActionScope.FINANCIAL,
            operation="transfer",
            risk=ActionRisk.CRITICAL,
            params={"amount": 5.00},
            description="Transfer money"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is False
        assert "financial" in reason.lower()
        assert "disabled" in reason.lower()
    
    def test_transaction_limits(self, policy_engine):
        """Test that transaction limits are enforced."""
        policy_engine.settings.financial_toggles.master_financial_toggle = True
        policy_engine.settings.financial_toggles.allow_transfers = True
        
        action = Action(
            scope=ActionScope.FINANCIAL,
            operation="transfer",
            risk=ActionRisk.CRITICAL,
            params={"amount": 100.00},  # Over $10 limit
            description="Large transfer"
        )
        
        allowed, reason = policy_engine.check_permission(action)
        assert allowed is False
        assert "limit" in reason.lower()
