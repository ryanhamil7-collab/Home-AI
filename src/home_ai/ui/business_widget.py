"""Business dashboard widget for embedding in main window."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from loguru import logger
from pathlib import Path

from home_ai.business.ledger import get_ledger, LedgerMode
from home_ai.safety.spending_caps import get_spending_tracker


class BusinessWidget(QWidget):
    """
    Business dashboard widget for monitoring autonomous operations.
    
    Embeddable version of BusinessDashboard for use in main window tabs.
    """
    
    def __init__(self):
        """Initialize business widget."""
        super().__init__()
        
        try:
            self.ledger = get_ledger(LedgerMode.SIMULATION)
            self.spending_tracker = get_spending_tracker()
        except Exception as e:
            logger.error(f"Failed to initialize business components: {e}")
            self.ledger = None
            self.spending_tracker = None
        
        self.init_ui()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        self.update_metrics()
        
        logger.info("BusinessWidget initialized")
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        title = QLabel("💼 Business Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        metrics_group = QGroupBox("Key Metrics")
        metrics_layout = QGridLayout()
        
        self.revenue_label = QLabel("$0.00")
        self.revenue_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ade80;")
        metrics_layout.addWidget(QLabel("Revenue:"), 0, 0)
        metrics_layout.addWidget(self.revenue_label, 0, 1)
        
        self.expenses_label = QLabel("$0.00")
        self.expenses_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f87171;")
        metrics_layout.addWidget(QLabel("Expenses:"), 1, 0)
        metrics_layout.addWidget(self.expenses_label, 1, 1)
        
        self.profit_label = QLabel("$0.00")
        self.profit_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #60a5fa;")
        metrics_layout.addWidget(QLabel("Profit:"), 2, 0)
        metrics_layout.addWidget(self.profit_label, 2, 1)
        
        self.roi_label = QLabel("0%")
        self.roi_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        metrics_layout.addWidget(QLabel("ROI:"), 3, 0)
        metrics_layout.addWidget(self.roi_label, 3, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        limits_group = QGroupBox("Spending Limits")
        limits_layout = QGridLayout()
        
        limits_layout.addWidget(QLabel("Daily:"), 0, 0)
        self.daily_progress = QProgressBar()
        limits_layout.addWidget(self.daily_progress, 0, 1)
        self.daily_label = QLabel("$0 / $10")
        limits_layout.addWidget(self.daily_label, 0, 2)
        
        limits_layout.addWidget(QLabel("Weekly:"), 1, 0)
        self.weekly_progress = QProgressBar()
        limits_layout.addWidget(self.weekly_progress, 1, 1)
        self.weekly_label = QLabel("$0 / $50")
        limits_layout.addWidget(self.weekly_label, 1, 2)
        
        limits_layout.addWidget(QLabel("Monthly:"), 2, 0)
        self.monthly_progress = QProgressBar()
        limits_layout.addWidget(self.monthly_progress, 2, 1)
        self.monthly_label = QLabel("$0 / $200")
        limits_layout.addWidget(self.monthly_label, 2, 2)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        breaker_group = QGroupBox("Circuit Breaker")
        breaker_layout = QVBoxLayout()
        
        self.breaker_status = QLabel("Status: INACTIVE")
        self.breaker_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ade80;")
        breaker_layout.addWidget(self.breaker_status)
        
        self.breaker_reason = QLabel("")
        breaker_layout.addWidget(self.breaker_reason)
        
        reset_button = QPushButton("Reset Circuit Breaker")
        reset_button.clicked.connect(self.reset_circuit_breaker)
        breaker_layout.addWidget(reset_button)
        
        breaker_group.setLayout(breaker_layout)
        layout.addWidget(breaker_group)
        
        transactions_group = QGroupBox("Recent Transactions")
        transactions_layout = QVBoxLayout()
        
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(4)
        self.transactions_table.setHorizontalHeaderLabels([
            "Timestamp", "Type", "Amount", "Description"
        ])
        self.transactions_table.setMaximumHeight(200)
        transactions_layout.addWidget(self.transactions_table)
        
        export_button = QPushButton("Export to CSV")
        export_button.clicked.connect(self.export_transactions)
        transactions_layout.addWidget(export_button)
        
        transactions_group.setLayout(transactions_layout)
        layout.addWidget(transactions_group)
    
    def update_metrics(self):
        """Update all metrics."""
        if not self.ledger or not self.spending_tracker:
            return
        
        try:
            summary = self.ledger.get_summary()
            self.revenue_label.setText(f"${summary['revenue']:.2f}")
            self.expenses_label.setText(f"${summary['expenses']:.2f}")
            self.profit_label.setText(f"${summary['profit']:.2f}")
            self.roi_label.setText(f"{summary['roi']:.1f}%")
            
            spending = self.spending_tracker.get_spending_summary()
            
            daily_pct = (spending['daily_spent'] / spending['daily_limit'] * 100) if spending['daily_limit'] > 0 else 0
            self.daily_progress.setValue(int(daily_pct))
            self.daily_label.setText(f"${spending['daily_spent']:.2f} / ${spending['daily_limit']:.2f}")
            
            weekly_pct = (spending['weekly_spent'] / spending['weekly_limit'] * 100) if spending['weekly_limit'] > 0 else 0
            self.weekly_progress.setValue(int(weekly_pct))
            self.weekly_label.setText(f"${spending['weekly_spent']:.2f} / ${spending['weekly_limit']:.2f}")
            
            monthly_pct = (spending['monthly_spent'] / spending['monthly_limit'] * 100) if spending['monthly_limit'] > 0 else 0
            self.monthly_progress.setValue(int(monthly_pct))
            self.monthly_label.setText(f"${spending['monthly_spent']:.2f} / ${spending['monthly_limit']:.2f}")
            
            if spending['circuit_breaker_active']:
                self.breaker_status.setText("Status: ACTIVE ⚠️")
                self.breaker_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #f87171;")
                self.breaker_reason.setText(f"Reason: {spending['circuit_breaker_reason']}")
            else:
                self.breaker_status.setText("Status: INACTIVE ✓")
                self.breaker_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ade80;")
                self.breaker_reason.setText("")
            
            self.update_transactions_table()
        
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    def update_transactions_table(self):
        """Update transactions table."""
        if not self.ledger:
            return
        
        try:
            transactions = self.ledger.get_transactions()
            recent = transactions[-10:]  # Last 10 transactions
            
            self.transactions_table.setRowCount(len(recent))
            
            for i, t in enumerate(recent):
                self.transactions_table.setItem(i, 0, QTableWidgetItem(t.timestamp[:19]))
                self.transactions_table.setItem(i, 1, QTableWidgetItem(t.type.value))
                self.transactions_table.setItem(i, 2, QTableWidgetItem(f"${t.amount:.2f}"))
                self.transactions_table.setItem(i, 3, QTableWidgetItem(t.description[:50]))
        
        except Exception as e:
            logger.error(f"Transaction table update failed: {e}")
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker."""
        if not self.spending_tracker:
            return
        
        success = self.spending_tracker.reset_circuit_breaker("User manual reset")
        if success:
            logger.info("Circuit breaker reset successfully")
            self.update_metrics()
    
    def export_transactions(self):
        """Export transactions to CSV."""
        if not self.ledger:
            return
        
        filepath = Path.home() / "Downloads" / "home_ai_transactions.csv"
        success = self.ledger.export_csv(filepath)
        
        if success:
            logger.info(f"Exported transactions to: {filepath}")
