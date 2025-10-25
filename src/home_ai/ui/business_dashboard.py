"""Business dashboard for monitoring autonomous operations."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QGroupBox, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from loguru import logger

from home_ai.business.ledger import get_ledger, LedgerMode
from home_ai.safety.spending_caps import get_spending_tracker
from home_ai.agents.meta_agent import get_meta_agent


class BusinessDashboard(QMainWindow):
    """
    Business dashboard for monitoring autonomous operations.
    
    Shows:
    - Financial metrics (revenue, expenses, profit)
    - Agent status and activity
    - Spending limits and usage
    - Recent transactions
    - Active goals and progress
    """
    
    def __init__(self):
        """Initialize business dashboard."""
        super().__init__()
        
        self.ledger = get_ledger(LedgerMode.SIMULATION)
        self.spending_tracker = get_spending_tracker()
        self.meta_agent = get_meta_agent()
        
        self.init_ui()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        logger.info("BusinessDashboard initialized")
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Home AI - Business Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        title = QLabel("🚀 Home AI Business Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        tabs = QTabWidget()
        tabs.addTab(self.create_overview_tab(), "Overview")
        tabs.addTab(self.create_financial_tab(), "Financial")
        tabs.addTab(self.create_agents_tab(), "Agents")
        tabs.addTab(self.create_spending_tab(), "Spending")
        tabs.addTab(self.create_transactions_tab(), "Transactions")
        layout.addWidget(tabs)
        
        self.statusBar().showMessage("Dashboard ready")
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3d3d3d;
                gridline-color: #4d4d4d;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0d7377;
            }
        """)
    
    def create_overview_tab(self) -> QWidget:
        """Create overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        metrics_group = QGroupBox("Key Metrics")
        metrics_layout = QGridLayout()
        
        self.revenue_label = QLabel("$0.00")
        self.revenue_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4ade80;")
        metrics_layout.addWidget(QLabel("Revenue:"), 0, 0)
        metrics_layout.addWidget(self.revenue_label, 0, 1)
        
        self.expenses_label = QLabel("$0.00")
        self.expenses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f87171;")
        metrics_layout.addWidget(QLabel("Expenses:"), 1, 0)
        metrics_layout.addWidget(self.expenses_label, 1, 1)
        
        self.profit_label = QLabel("$0.00")
        self.profit_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #60a5fa;")
        metrics_layout.addWidget(QLabel("Profit:"), 2, 0)
        metrics_layout.addWidget(self.profit_label, 2, 1)
        
        self.roi_label = QLabel("0%")
        self.roi_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        metrics_layout.addWidget(QLabel("ROI:"), 3, 0)
        metrics_layout.addWidget(self.roi_label, 3, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        goals_group = QGroupBox("Active Goals")
        goals_layout = QVBoxLayout()
        self.goals_text = QTextEdit()
        self.goals_text.setReadOnly(True)
        self.goals_text.setMaximumHeight(150)
        goals_layout.addWidget(self.goals_text)
        goals_group.setLayout(goals_layout)
        layout.addWidget(goals_group)
        
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        self.activity_text = QTextEdit()
        self.activity_text.setReadOnly(True)
        activity_layout.addWidget(self.activity_text)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        return widget
    
    def create_financial_tab(self) -> QWidget:
        """Create financial tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        summary_group = QGroupBox("Financial Summary")
        summary_layout = QVBoxLayout()
        self.financial_summary = QTextEdit()
        self.financial_summary.setReadOnly(True)
        summary_layout.addWidget(self.financial_summary)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        breakdown_group = QGroupBox("Category Breakdown")
        breakdown_layout = QVBoxLayout()
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(2)
        self.category_table.setHorizontalHeaderLabels(["Category", "Amount"])
        breakdown_layout.addWidget(self.category_table)
        breakdown_group.setLayout(breakdown_layout)
        layout.addWidget(breakdown_group)
        
        return widget
    
    def create_agents_tab(self) -> QWidget:
        """Create agents tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        status_group = QGroupBox("Agent Status")
        status_layout = QVBoxLayout()
        self.agent_status = QTextEdit()
        self.agent_status.setReadOnly(True)
        status_layout.addWidget(self.agent_status)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        history_group = QGroupBox("Execution History")
        history_layout = QVBoxLayout()
        self.execution_table = QTableWidget()
        self.execution_table.setColumnCount(4)
        self.execution_table.setHorizontalHeaderLabels(["Goal", "Status", "Cost", "Revenue"])
        history_layout.addWidget(self.execution_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        return widget
    
    def create_spending_tab(self) -> QWidget:
        """Create spending tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
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
        self.breaker_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ade80;")
        breaker_layout.addWidget(self.breaker_status)
        self.breaker_reason = QLabel("")
        breaker_layout.addWidget(self.breaker_reason)
        
        reset_button = QPushButton("Reset Circuit Breaker")
        reset_button.clicked.connect(self.reset_circuit_breaker)
        breaker_layout.addWidget(reset_button)
        
        breaker_group.setLayout(breaker_layout)
        layout.addWidget(breaker_group)
        
        layout.addStretch()
        
        return widget
    
    def create_transactions_tab(self) -> QWidget:
        """Create transactions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "Timestamp", "Type", "Amount", "Category", "Description"
        ])
        layout.addWidget(self.transactions_table)
        
        export_button = QPushButton("Export to CSV")
        export_button.clicked.connect(self.export_transactions)
        layout.addWidget(export_button)
        
        return widget
    
    def update_metrics(self):
        """Update all metrics."""
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
                self.breaker_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #f87171;")
                self.breaker_reason.setText(f"Reason: {spending['circuit_breaker_reason']}")
            else:
                self.breaker_status.setText("Status: INACTIVE ✓")
                self.breaker_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ade80;")
                self.breaker_reason.setText("")
            
            self.update_transactions_table()
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    def update_transactions_table(self):
        """Update transactions table."""
        try:
            transactions = self.ledger.get_transactions()
            self.transactions_table.setRowCount(len(transactions))
            
            for i, t in enumerate(transactions):
                self.transactions_table.setItem(i, 0, QTableWidgetItem(t.timestamp))
                self.transactions_table.setItem(i, 1, QTableWidgetItem(t.type.value))
                self.transactions_table.setItem(i, 2, QTableWidgetItem(f"${t.amount:.2f}"))
                self.transactions_table.setItem(i, 3, QTableWidgetItem(t.category))
                self.transactions_table.setItem(i, 4, QTableWidgetItem(t.description))
        
        except Exception as e:
            logger.error(f"Transaction table update failed: {e}")
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker."""
        success = self.spending_tracker.reset_circuit_breaker("User manual reset")
        if success:
            self.statusBar().showMessage("Circuit breaker reset successfully", 3000)
        else:
            self.statusBar().showMessage("Circuit breaker not active", 3000)
    
    def export_transactions(self):
        """Export transactions to CSV."""
        from pathlib import Path
        filepath = Path.home() / "Downloads" / "home_ai_transactions.csv"
        success = self.ledger.export_csv(filepath)
        
        if success:
            self.statusBar().showMessage(f"Exported to: {filepath}", 5000)
        else:
            self.statusBar().showMessage("Export failed", 3000)


def launch_business_dashboard():
    """Launch business dashboard."""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dashboard = BusinessDashboard()
    dashboard.show()
    sys.exit(app.exec())
