"""Audit logs and system logs tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from loguru import logger
from pathlib import Path

try:
    from home_ai_os.security.audit_logger import get_audit_logger
except ImportError as e:
    logger.warning(f"Security module not available: {e}")
    get_audit_logger = None


class LogsTab(QWidget):
    """Audit logs and system logs tab."""
    
    def __init__(self):
        super().__init__()
        
        self.audit_logger = None
        if get_audit_logger:
            try:
                self.audit_logger = get_audit_logger()
            except Exception as e:
                logger.error(f"Could not initialize audit logger: {e}")
        
        self.setup_ui()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        header = QLabel("System Logs & Audit Trail")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("Log Type:"))
        
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["Audit Logs", "System Logs", "All Logs"])
        self.log_type_combo.currentTextChanged.connect(self.refresh_logs)
        controls.addWidget(self.log_type_combo)
        
        controls.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        controls.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear Display")
        self.clear_btn.clicked.connect(self.clear_display)
        controls.addWidget(self.clear_btn)
        
        layout.addLayout(controls)
        
        logs_group = QGroupBox("Log Entries")
        logs_layout = QVBoxLayout()
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setPlaceholderText("Logs will appear here...")
        self.logs_display.setStyleSheet("font-family: monospace;")
        logs_layout.addWidget(self.logs_display)
        
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Total entries: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        
        self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh log display."""
        log_type = self.log_type_combo.currentText()
        
        if log_type == "Audit Logs":
            self.load_audit_logs()
        elif log_type == "System Logs":
            self.load_system_logs()
        else:
            self.load_all_logs()
    
    def load_audit_logs(self):
        """Load audit logs."""
        if not self.audit_logger:
            self.logs_display.setText("❌ Audit logger not available")
            return
        
        try:
            entries = self.audit_logger.get_recent_entries(limit=100)
            
            self.logs_display.clear()
            self.logs_display.append("=== AUDIT LOGS ===\n")
            
            for entry in reversed(entries):
                timestamp = entry.get("timestamp", "")
                action = entry.get("action", "")
                status = entry.get("status", "")
                details = entry.get("details", "")
                
                self.logs_display.append(f"[{timestamp}] {status.upper()}: {action}")
                if details:
                    self.logs_display.append(f"  Details: {details}")
                self.logs_display.append("")
            
            self.stats_label.setText(f"Total entries: {len(entries)}")
        
        except Exception as e:
            self.logs_display.setText(f"❌ Error loading audit logs: {e}")
            logger.error(f"Audit log load error: {e}")
    
    def load_system_logs(self):
        """Load system logs."""
        try:
            log_dir = Path.home() / ".home_ai" / "logs"
            
            if not log_dir.exists():
                self.logs_display.setText("❌ No system logs found")
                return
            
            log_files = sorted(log_dir.glob("homeai_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if not log_files:
                self.logs_display.setText("❌ No log files found")
                return
            
            latest_log = log_files[0]
            
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-100:]
            
            self.logs_display.clear()
            self.logs_display.append(f"=== SYSTEM LOGS ({latest_log.name}) ===\n")
            self.logs_display.append("".join(recent_lines))
            
            self.stats_label.setText(f"Total lines: {len(recent_lines)}")
        
        except Exception as e:
            self.logs_display.setText(f"❌ Error loading system logs: {e}")
            logger.error(f"System log load error: {e}")
    
    def load_all_logs(self):
        """Load all logs."""
        self.logs_display.clear()
        self.logs_display.append("=== ALL LOGS ===\n\n")
        
        if self.audit_logger:
            try:
                entries = self.audit_logger.get_recent_entries(limit=50)
                self.logs_display.append("--- Audit Logs (Recent 50) ---\n")
                for entry in reversed(entries):
                    timestamp = entry.get("timestamp", "")
                    action = entry.get("action", "")
                    status = entry.get("status", "")
                    self.logs_display.append(f"[{timestamp}] {status}: {action}")
                self.logs_display.append("\n")
            except Exception as e:
                logger.error(f"Error loading audit logs: {e}")
        
        try:
            log_dir = Path.home() / ".home_ai" / "logs"
            if log_dir.exists():
                log_files = sorted(log_dir.glob("homeai_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                if log_files:
                    latest_log = log_files[0]
                    with open(latest_log, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-50:]
                    
                    self.logs_display.append(f"--- System Logs (Recent 50 from {latest_log.name}) ---\n")
                    self.logs_display.append("".join(recent_lines))
        except Exception as e:
            logger.error(f"Error loading system logs: {e}")
    
    def clear_display(self):
        """Clear log display."""
        self.logs_display.clear()
        self.stats_label.setText("Total entries: 0")
