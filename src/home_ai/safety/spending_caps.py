"""Spending caps and circuit breaker system for financial safety."""

from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import json
from loguru import logger

from home_ai.security.audit_logger import get_audit_logger


@dataclass
class SpendingLimits:
    """Spending limits configuration."""
    daily_limit: float = 10.0
    weekly_limit: float = 50.0
    monthly_limit: float = 200.0
    per_transaction_limit: float = 50.0
    circuit_breaker_multiplier: float = 2.0


class SpendingTracker:
    """
    Spending tracker with circuit breaker.
    
    Tracks all financial transactions and enforces spending limits.
    Automatically triggers circuit breaker when limits exceeded.
    """
    
    def __init__(self, limits: Optional[SpendingLimits] = None):
        """
        Initialize spending tracker.
        
        Args:
            limits: Spending limits (uses defaults if not provided)
        """
        self.limits = limits or SpendingLimits()
        self.audit_logger = get_audit_logger()
        
        self.data_dir = Path.home() / ".home_ai" / "spending"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.transactions: list = []
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = ""
        
        self._load_data()
        
        logger.info(f"SpendingTracker initialized with daily limit: ${self.limits.daily_limit}")
    
    def record_transaction(self, amount: float, description: str,
                          category: str = "general") -> Dict[str, bool]:
        """
        Record a transaction and check limits.
        
        Args:
            amount: Transaction amount
            description: Transaction description
            category: Transaction category
        
        Returns:
            Dict with allowed status and reason
        """
        if self.circuit_breaker_active:
            logger.warning(f"Circuit breaker active: {self.circuit_breaker_reason}")
            return {
                "allowed": False,
                "reason": f"Circuit breaker active: {self.circuit_breaker_reason}"
            }
        
        if amount > self.limits.per_transaction_limit:
            logger.warning(f"Transaction ${amount} exceeds per-transaction limit ${self.limits.per_transaction_limit}")
            return {
                "allowed": False,
                "reason": f"Transaction exceeds per-transaction limit of ${self.limits.per_transaction_limit}"
            }
        
        daily_spent = self._get_spending_for_period(days=1)
        if daily_spent + amount > self.limits.daily_limit:
            logger.warning(f"Transaction would exceed daily limit: ${daily_spent + amount} > ${self.limits.daily_limit}")
            return {
                "allowed": False,
                "reason": f"Would exceed daily limit of ${self.limits.daily_limit} (current: ${daily_spent:.2f})"
            }
        
        weekly_spent = self._get_spending_for_period(days=7)
        if weekly_spent + amount > self.limits.weekly_limit:
            logger.warning(f"Transaction would exceed weekly limit")
            return {
                "allowed": False,
                "reason": f"Would exceed weekly limit of ${self.limits.weekly_limit} (current: ${weekly_spent:.2f})"
            }
        
        monthly_spent = self._get_spending_for_period(days=30)
        if monthly_spent + amount > self.limits.monthly_limit:
            logger.warning(f"Transaction would exceed monthly limit")
            return {
                "allowed": False,
                "reason": f"Would exceed monthly limit of ${self.limits.monthly_limit} (current: ${monthly_spent:.2f})"
            }
        
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "amount": amount,
            "description": description,
            "category": category
        }
        
        self.transactions.append(transaction)
        self._save_data()
        
        self._check_circuit_breaker()
        
        self.audit_logger.log_action(
            action_type="spending",
            action="record_transaction",
            status="completed",
            details=transaction
        )
        
        logger.info(f"Recorded transaction: ${amount} - {description}")
        return {"allowed": True, "reason": "Transaction approved"}
    
    def _get_spending_for_period(self, days: int) -> float:
        """Get total spending for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        total = sum(
            t["amount"]
            for t in self.transactions
            if datetime.fromisoformat(t["timestamp"]) > cutoff
        )
        
        return total
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should be triggered."""
        daily_spent = self._get_spending_for_period(days=1)
        circuit_breaker_threshold = self.limits.daily_limit * self.limits.circuit_breaker_multiplier
        
        if daily_spent >= circuit_breaker_threshold:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = f"Daily spending ${daily_spent:.2f} exceeded circuit breaker threshold ${circuit_breaker_threshold:.2f}"
            
            self.audit_logger.log_action(
                action_type="spending",
                action="circuit_breaker_triggered",
                status="critical",
                details={"reason": self.circuit_breaker_reason}
            )
            
            logger.critical(f"CIRCUIT BREAKER TRIGGERED: {self.circuit_breaker_reason}")
        
        recent_transactions = [
            t for t in self.transactions
            if datetime.fromisoformat(t["timestamp"]) > datetime.now() - timedelta(minutes=5)
        ]
        
        if len(recent_transactions) >= 5:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = f"Too many transactions in short period: {len(recent_transactions)} in 5 minutes"
            
            logger.critical(f"CIRCUIT BREAKER TRIGGERED: {self.circuit_breaker_reason}")
    
    def reset_circuit_breaker(self, reason: str = "Manual reset") -> bool:
        """
        Reset circuit breaker.
        
        Args:
            reason: Reason for reset
        
        Returns:
            True if successful
        """
        if not self.circuit_breaker_active:
            return False
        
        self.circuit_breaker_active = False
        old_reason = self.circuit_breaker_reason
        self.circuit_breaker_reason = ""
        
        self.audit_logger.log_action(
            action_type="spending",
            action="circuit_breaker_reset",
            status="completed",
            details={"old_reason": old_reason, "reset_reason": reason}
        )
        
        logger.info(f"Circuit breaker reset: {reason}")
        return True
    
    def get_spending_summary(self) -> Dict:
        """Get spending summary."""
        return {
            "daily_spent": self._get_spending_for_period(days=1),
            "daily_limit": self.limits.daily_limit,
            "daily_remaining": max(0, self.limits.daily_limit - self._get_spending_for_period(days=1)),
            "weekly_spent": self._get_spending_for_period(days=7),
            "weekly_limit": self.limits.weekly_limit,
            "monthly_spent": self._get_spending_for_period(days=30),
            "monthly_limit": self.limits.monthly_limit,
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_reason": self.circuit_breaker_reason,
            "total_transactions": len(self.transactions)
        }
    
    def update_limits(self, new_limits: SpendingLimits) -> bool:
        """
        Update spending limits.
        
        Args:
            new_limits: New spending limits
        
        Returns:
            True if successful
        """
        old_limits = self.limits
        self.limits = new_limits
        
        self.audit_logger.log_action(
            action_type="spending",
            action="update_limits",
            status="completed",
            details={
                "old_daily": old_limits.daily_limit,
                "new_daily": new_limits.daily_limit
            }
        )
        
        logger.info(f"Updated spending limits: daily ${new_limits.daily_limit}")
        return True
    
    def _save_data(self):
        """Save spending data to disk."""
        try:
            data = {
                "limits": {
                    "daily_limit": self.limits.daily_limit,
                    "weekly_limit": self.limits.weekly_limit,
                    "monthly_limit": self.limits.monthly_limit,
                    "per_transaction_limit": self.limits.per_transaction_limit,
                    "circuit_breaker_multiplier": self.limits.circuit_breaker_multiplier
                },
                "transactions": self.transactions,
                "circuit_breaker_active": self.circuit_breaker_active,
                "circuit_breaker_reason": self.circuit_breaker_reason
            }
            
            filepath = self.data_dir / "spending_data.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save spending data: {e}")
    
    def _load_data(self):
        """Load spending data from disk."""
        try:
            filepath = self.data_dir / "spending_data.json"
            
            if not filepath.exists():
                return
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if "limits" in data:
                self.limits = SpendingLimits(**data["limits"])
            
            self.transactions = data.get("transactions", [])
            
            self.circuit_breaker_active = data.get("circuit_breaker_active", False)
            self.circuit_breaker_reason = data.get("circuit_breaker_reason", "")
            
            logger.info(f"Loaded {len(self.transactions)} transactions")
        
        except Exception as e:
            logger.error(f"Failed to load spending data: {e}")


_spending_tracker: Optional[SpendingTracker] = None


def get_spending_tracker() -> SpendingTracker:
    """Get or create spending tracker instance."""
    global _spending_tracker
    if _spending_tracker is None:
        _spending_tracker = SpendingTracker()
    return _spending_tracker
