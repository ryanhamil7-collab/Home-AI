"""Tests for spending caps and circuit breaker system."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import shutil

from home_ai.safety.spending_caps import SpendingTracker, SpendingLimits


@pytest.fixture
def spending_tracker():
    """Create spending tracker for testing."""
    limits = SpendingLimits(
        daily_limit=10.0,
        weekly_limit=50.0,
        monthly_limit=200.0,
        per_transaction_limit=50.0
    )
    tracker = SpendingTracker(limits)
    
    tracker.transactions = []
    tracker.circuit_breaker_active = False
    
    yield tracker
    
    data_dir = Path.home() / ".home_ai" / "spending"
    if data_dir.exists():
        shutil.rmtree(data_dir)


def test_record_transaction_within_limits(spending_tracker):
    """Test recording transaction within limits."""
    result = spending_tracker.record_transaction(5.0, "Test transaction")
    
    assert result["allowed"] is True
    assert len(spending_tracker.transactions) == 1


def test_record_transaction_exceeds_daily_limit(spending_tracker):
    """Test transaction that exceeds daily limit."""
    spending_tracker.record_transaction(8.0, "First transaction")
    
    result = spending_tracker.record_transaction(5.0, "Second transaction")
    
    assert result["allowed"] is False
    assert "daily limit" in result["reason"].lower()


def test_record_transaction_exceeds_per_transaction_limit(spending_tracker):
    """Test transaction that exceeds per-transaction limit."""
    result = spending_tracker.record_transaction(100.0, "Large transaction")
    
    assert result["allowed"] is False
    assert "per-transaction limit" in result["reason"].lower()


def test_circuit_breaker_triggers(spending_tracker):
    """Test circuit breaker triggers on excessive spending."""
    spending_tracker.record_transaction(10.0, "Transaction 1")
    spending_tracker.record_transaction(10.0, "Transaction 2")
    
    assert spending_tracker.circuit_breaker_active is True
    assert spending_tracker.circuit_breaker_reason != ""


def test_circuit_breaker_blocks_transactions(spending_tracker):
    """Test circuit breaker blocks new transactions."""
    spending_tracker.circuit_breaker_active = True
    spending_tracker.circuit_breaker_reason = "Test trigger"
    
    result = spending_tracker.record_transaction(1.0, "Blocked transaction")
    
    assert result["allowed"] is False
    assert "circuit breaker" in result["reason"].lower()


def test_reset_circuit_breaker(spending_tracker):
    """Test resetting circuit breaker."""
    spending_tracker.circuit_breaker_active = True
    spending_tracker.circuit_breaker_reason = "Test trigger"
    
    success = spending_tracker.reset_circuit_breaker("Test reset")
    
    assert success is True
    assert spending_tracker.circuit_breaker_active is False


def test_get_spending_summary(spending_tracker):
    """Test getting spending summary."""
    spending_tracker.record_transaction(5.0, "Test transaction")
    
    summary = spending_tracker.get_spending_summary()
    
    assert summary["daily_spent"] == 5.0
    assert summary["daily_limit"] == 10.0
    assert summary["daily_remaining"] == 5.0
    assert summary["total_transactions"] == 1


def test_update_limits(spending_tracker):
    """Test updating spending limits."""
    new_limits = SpendingLimits(
        daily_limit=20.0,
        weekly_limit=100.0,
        monthly_limit=400.0
    )
    
    success = spending_tracker.update_limits(new_limits)
    
    assert success is True
    assert spending_tracker.limits.daily_limit == 20.0
