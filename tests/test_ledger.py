"""Tests for business ledger."""

import pytest
from pathlib import Path
import shutil

from home_ai.business.ledger import get_ledger, LedgerMode, TransactionType


@pytest.fixture
def ledger():
    """Create ledger for testing."""
    ledger = get_ledger(LedgerMode.SIMULATION)
    ledger.transactions = []  # Clear any existing transactions
    
    yield ledger
    
    ledger_dir = Path.home() / ".home_ai" / "ledger"
    if ledger_dir.exists():
        shutil.rmtree(ledger_dir)


def test_record_income(ledger):
    """Test recording income."""
    transaction = ledger.record_income(
        amount=100.0,
        source="product_sale",
        description="Test sale"
    )
    
    assert transaction.amount == 100.0
    assert transaction.type == TransactionType.INCOME
    assert len(ledger.transactions) == 1


def test_record_expense(ledger):
    """Test recording expense."""
    transaction = ledger.record_expense(
        amount=50.0,
        destination="marketing",
        description="Test expense"
    )
    
    assert transaction.amount == 50.0
    assert transaction.type == TransactionType.EXPENSE
    assert len(ledger.transactions) == 1


def test_get_summary(ledger):
    """Test getting financial summary."""
    ledger.record_income(100.0, "sale", "Sale 1")
    ledger.record_expense(30.0, "marketing", "Ad spend")
    
    summary = ledger.get_summary()
    
    assert summary["revenue"] == 100.0
    assert summary["expenses"] == 30.0
    assert summary["profit"] == 70.0
    assert summary["roi"] > 0


def test_get_transactions_filtered(ledger):
    """Test getting filtered transactions."""
    ledger.record_income(100.0, "sale", "Sale 1")
    ledger.record_expense(30.0, "marketing", "Ad spend")
    
    income_transactions = ledger.get_transactions(type=TransactionType.INCOME)
    
    assert len(income_transactions) == 1
    assert income_transactions[0].type == TransactionType.INCOME


def test_get_category_breakdown(ledger):
    """Test getting category breakdown."""
    ledger.record_income(100.0, "sale", "Sale 1", category="revenue")
    ledger.record_expense(30.0, "marketing", "Ad spend", category="marketing")
    
    breakdown = ledger.get_category_breakdown()
    
    assert "revenue" in breakdown
    assert "marketing" in breakdown
    assert breakdown["revenue"] == 100.0
    assert breakdown["marketing"] == -30.0


def test_export_csv(ledger, tmp_path):
    """Test exporting to CSV."""
    ledger.record_income(100.0, "sale", "Sale 1")
    
    filepath = tmp_path / "test_export.csv"
    success = ledger.export_csv(filepath)
    
    assert success is True
    assert filepath.exists()
