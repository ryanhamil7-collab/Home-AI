"""Business automation and financial tracking tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from loguru import logger

try:
    from home_ai_os.business.ledger import get_ledger, LedgerMode, TransactionType
except ImportError as e:
    logger.warning(f"Business modules not available: {e}")
    get_ledger = None
    LedgerMode = None
    TransactionType = None


class BusinessTab(QWidget):
    """Business automation and financial tracking."""
    
    def __init__(self):
        super().__init__()
        
        self.ledger = None
        if get_ledger:
            try:
                self.ledger = get_ledger(LedgerMode.SIMULATION)
            except Exception as e:
                logger.error(f"Could not initialize ledger: {e}")
        
        self.setup_ui()
        self.refresh_summary()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        header = QLabel("Business Automation & Financial Tracking")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        mode_label = QLabel("📊 Mode: SIMULATION (Safe Mode)")
        mode_label.setStyleSheet("color: green; font-size: 12pt; font-weight: bold;")
        layout.addWidget(mode_label)
        
        summary_group = QGroupBox("Financial Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)
        
        refresh_btn = QPushButton("🔄 Refresh Summary")
        refresh_btn.clicked.connect(self.refresh_summary)
        summary_layout.addWidget(refresh_btn)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        entry_group = QGroupBox("Record Transaction")
        entry_layout = QFormLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Income", "Expense"])
        entry_layout.addRow("Type:", self.type_combo)
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 1000000.00)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(100.00)
        entry_layout.addRow("Amount:", self.amount_spin)
        
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., revenue, marketing, development")
        entry_layout.addRow("Category:", self.category_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Transaction description")
        entry_layout.addRow("Description:", self.description_edit)
        
        self.source_dest_edit = QLineEdit()
        self.source_dest_edit.setPlaceholderText("Source (income) or Destination (expense)")
        entry_layout.addRow("Source/Dest:", self.source_dest_edit)
        
        record_btn = QPushButton("💰 Record Transaction")
        record_btn.clicked.connect(self.record_transaction)
        entry_layout.addRow("", record_btn)
        
        entry_group.setLayout(entry_layout)
        layout.addWidget(entry_group)
        
        history_group = QGroupBox("Transaction History")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Type", "Amount", "Category", "Description", "Source/Dest"
        ])
        history_layout.addWidget(self.history_table)
        
        export_btn = QPushButton("📥 Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        history_layout.addWidget(export_btn)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        self.setLayout(layout)
    
    def refresh_summary(self):
        """Refresh financial summary."""
        if not self.ledger:
            self.summary_text.setText("❌ Ledger not available")
            return
        
        try:
            summary = self.ledger.get_summary()
            
            text = f"""
📊 Financial Summary (Simulation Mode)

💰 Revenue: ${summary['revenue']:.2f}
💸 Expenses: ${summary['expenses']:.2f}
📈 Profit: ${summary['profit']:.2f}
📊 ROI: {summary['roi']:.2f}%
📝 Transactions: {summary['transaction_count']}

⚠️ Note: This is simulation mode. No real money is involved.
"""
            self.summary_text.setText(text)
            
            self.refresh_history()
        
        except Exception as e:
            self.summary_text.setText(f"❌ Error: {e}")
            logger.error(f"Summary refresh error: {e}")
    
    def record_transaction(self):
        """Record a new transaction."""
        if not self.ledger:
            QMessageBox.warning(self, "Error", "Ledger not available")
            return
        
        try:
            trans_type = self.type_combo.currentText()
            amount = self.amount_spin.value()
            category = self.category_edit.text() or "uncategorized"
            description = self.description_edit.text() or "No description"
            source_dest = self.source_dest_edit.text() or "Unknown"
            
            if trans_type == "Income":
                self.ledger.record_income(
                    amount=amount,
                    source=source_dest,
                    description=description,
                    category=category
                )
            else:
                self.ledger.record_expense(
                    amount=amount,
                    destination=source_dest,
                    description=description,
                    category=category
                )
            
            QMessageBox.information(self, "Success", f"Transaction recorded: ${amount:.2f}")
            
            self.amount_spin.setValue(100.00)
            self.category_edit.clear()
            self.description_edit.clear()
            self.source_dest_edit.clear()
            
            self.refresh_summary()
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to record transaction: {e}")
            logger.error(f"Transaction recording error: {e}")
    
    def refresh_history(self):
        """Refresh transaction history table."""
        if not self.ledger:
            return
        
        try:
            transactions = self.ledger.get_transactions()
            
            self.history_table.setRowCount(len(transactions))
            
            for i, trans in enumerate(reversed(transactions[-50:])):  # Last 50
                self.history_table.setItem(i, 0, QTableWidgetItem(trans.timestamp[:19]))
                self.history_table.setItem(i, 1, QTableWidgetItem(trans.type.value))
                self.history_table.setItem(i, 2, QTableWidgetItem(f"${trans.amount:.2f}"))
                self.history_table.setItem(i, 3, QTableWidgetItem(trans.category))
                self.history_table.setItem(i, 4, QTableWidgetItem(trans.description))
                self.history_table.setItem(i, 5, QTableWidgetItem(trans.source or trans.destination or ""))
            
            self.history_table.resizeColumnsToContents()
        
        except Exception as e:
            logger.error(f"History refresh error: {e}")
    
    def export_csv(self):
        """Export transactions to CSV."""
        if not self.ledger:
            QMessageBox.warning(self, "Error", "Ledger not available")
            return
        
        try:
            from pathlib import Path
            filepath = Path.home() / "Documents" / f"homeai_ledger_{LedgerMode.SIMULATION.value}.csv"
            
            if self.ledger.export_csv(filepath):
                QMessageBox.information(self, "Success", f"Exported to:\n{filepath}")
            else:
                QMessageBox.warning(self, "Error", "Export failed")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")
            logger.error(f"CSV export error: {e}")
