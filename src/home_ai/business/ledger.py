"""Business Ledger: Double-entry accounting for financial tracking."""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from loguru import logger


class LedgerMode(Enum):
    """Ledger operation mode."""
    SIMULATION = "simulation"
    LIVE = "live"


class TransactionType(Enum):
    """Transaction types."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


@dataclass
class Transaction:
    """Financial transaction."""
    id: str
    timestamp: str
    type: TransactionType
    amount: float
    category: str
    description: str
    source: Optional[str] = None
    destination: Optional[str] = None
    metadata: Optional[Dict] = None


class BusinessLedger:
    """
    Business Ledger: Double-entry accounting system.
    
    Tracks all financial operations in simulation or live mode.
    Provides financial reporting and analysis.
    """
    
    def __init__(self, mode: LedgerMode = LedgerMode.SIMULATION):
        """
        Initialize Business Ledger.
        
        Args:
            mode: Operation mode (simulation or live)
        """
        self.mode = mode
        self.transactions: List[Transaction] = []
        
        self.ledger_dir = Path.home() / ".home_ai" / "ledger"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_transactions()
        
        logger.info(f"BusinessLedger initialized in {mode.value} mode")
    
    def record_income(self, amount: float, source: str, description: str,
                     category: str = "revenue", metadata: Optional[Dict] = None) -> Transaction:
        """
        Record income transaction.
        
        Args:
            amount: Income amount
            source: Income source
            description: Transaction description
            category: Income category
            metadata: Optional metadata
        
        Returns:
            Created transaction
        """
        transaction = Transaction(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            type=TransactionType.INCOME,
            amount=amount,
            category=category,
            description=description,
            source=source,
            metadata=metadata or {}
        )
        
        self.transactions.append(transaction)
        self._save_transactions()
        
        logger.info(f"Recorded income: ${amount} from {source}")
        return transaction
    
    def record_expense(self, amount: float, destination: str, description: str,
                      category: str = "expense", metadata: Optional[Dict] = None) -> Transaction:
        """
        Record expense transaction.
        
        Args:
            amount: Expense amount
            destination: Expense destination
            description: Transaction description
            category: Expense category
            metadata: Optional metadata
        
        Returns:
            Created transaction
        """
        transaction = Transaction(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            type=TransactionType.EXPENSE,
            amount=amount,
            category=category,
            description=description,
            destination=destination,
            metadata=metadata or {}
        )
        
        self.transactions.append(transaction)
        self._save_transactions()
        
        logger.info(f"Recorded expense: ${amount} to {destination}")
        return transaction
    
    def get_summary(self) -> Dict:
        """
        Get financial summary.
        
        Returns:
            Summary with revenue, expenses, profit
        """
        revenue = sum(
            t.amount for t in self.transactions
            if t.type == TransactionType.INCOME
        )
        
        expenses = sum(
            t.amount for t in self.transactions
            if t.type == TransactionType.EXPENSE
        )
        
        profit = revenue - expenses
        
        return {
            "mode": self.mode.value,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "transaction_count": len(self.transactions),
            "roi": (profit / expenses * 100) if expenses > 0 else 0.0
        }
    
    def get_transactions(self, type: Optional[TransactionType] = None,
                        category: Optional[str] = None) -> List[Transaction]:
        """
        Get filtered transactions.
        
        Args:
            type: Filter by transaction type
            category: Filter by category
        
        Returns:
            Filtered transactions
        """
        filtered = self.transactions
        
        if type:
            filtered = [t for t in filtered if t.type == type]
        
        if category:
            filtered = [t for t in filtered if t.category == category]
        
        return filtered
    
    def export_csv(self, filepath: Path) -> bool:
        """
        Export transactions to CSV.
        
        Args:
            filepath: Output file path
        
        Returns:
            True if successful
        """
        try:
            import csv
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                writer.writerow([
                    'ID', 'Timestamp', 'Type', 'Amount', 'Category',
                    'Description', 'Source', 'Destination'
                ])
                
                for t in self.transactions:
                    writer.writerow([
                        t.id, t.timestamp, t.type.value, t.amount,
                        t.category, t.description, t.source or '', t.destination or ''
                    ])
            
            logger.info(f"Exported transactions to: {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def get_category_breakdown(self) -> Dict[str, float]:
        """Get spending breakdown by category."""
        breakdown = {}
        
        for t in self.transactions:
            if t.category not in breakdown:
                breakdown[t.category] = 0.0
            
            if t.type == TransactionType.INCOME:
                breakdown[t.category] += t.amount
            else:
                breakdown[t.category] -= t.amount
        
        return breakdown
    
    def get_monthly_summary(self) -> Dict[str, Dict]:
        """Get monthly financial summary."""
        from collections import defaultdict
        
        monthly = defaultdict(lambda: {"revenue": 0.0, "expenses": 0.0})
        
        for t in self.transactions:
            month = t.timestamp[:7]  # YYYY-MM
            
            if t.type == TransactionType.INCOME:
                monthly[month]["revenue"] += t.amount
            else:
                monthly[month]["expenses"] += t.amount
        
        for month in monthly:
            monthly[month]["profit"] = monthly[month]["revenue"] - monthly[month]["expenses"]
        
        return dict(monthly)
    
    def _generate_id(self) -> str:
        """Generate unique transaction ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def _save_transactions(self):
        """Save transactions to disk."""
        try:
            filepath = self.ledger_dir / f"ledger_{self.mode.value}.json"
            
            data = {
                "mode": self.mode.value,
                "transactions": [
                    {
                        "id": t.id,
                        "timestamp": t.timestamp,
                        "type": t.type.value,
                        "amount": t.amount,
                        "category": t.category,
                        "description": t.description,
                        "source": t.source,
                        "destination": t.destination,
                        "metadata": t.metadata
                    }
                    for t in self.transactions
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save transactions: {e}")
    
    def _load_transactions(self):
        """Load transactions from disk."""
        try:
            filepath = self.ledger_dir / f"ledger_{self.mode.value}.json"
            
            if not filepath.exists():
                return
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.transactions = [
                Transaction(
                    id=t["id"],
                    timestamp=t["timestamp"],
                    type=TransactionType(t["type"]),
                    amount=t["amount"],
                    category=t["category"],
                    description=t["description"],
                    source=t.get("source"),
                    destination=t.get("destination"),
                    metadata=t.get("metadata")
                )
                for t in data["transactions"]
            ]
            
            logger.info(f"Loaded {len(self.transactions)} transactions")
        
        except Exception as e:
            logger.error(f"Failed to load transactions: {e}")


_simulation_ledger: Optional[BusinessLedger] = None
_live_ledger: Optional[BusinessLedger] = None


def get_ledger(mode: LedgerMode = LedgerMode.SIMULATION) -> BusinessLedger:
    """Get or create ledger instance."""
    global _simulation_ledger, _live_ledger
    
    if mode == LedgerMode.SIMULATION:
        if _simulation_ledger is None:
            _simulation_ledger = BusinessLedger(mode=LedgerMode.SIMULATION)
        return _simulation_ledger
    else:
        if _live_ledger is None:
            _live_ledger = BusinessLedger(mode=LedgerMode.LIVE)
        return _live_ledger
