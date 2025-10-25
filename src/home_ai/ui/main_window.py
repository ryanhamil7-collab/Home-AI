"""Main PyQt6 window with tabbed interface."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLineEdit, QPushButton,
    QLabel, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QIcon
from loguru import logger
import sys

from home_ai.core.config import get_settings
from home_ai.llm.ollama_client import get_ollama_client
from home_ai.monitoring.system_monitor import get_system_monitor
from home_ai.security.audit_logger import get_audit_logger


class ChatThread(QThread):
    """Thread for LLM chat to keep UI responsive."""
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, message: str):
        super().__init__()
        self.message = message
        self.client = get_ollama_client()
    
    def run(self):
        """Run chat in background thread."""
        try:
            for chunk in self.client.chat(self.message):
                self.chunk_received.emit(chunk)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.chat_thread = None
        
        self.init_ui()
        self.setup_timers()
        
        logger.info("MainWindow initialized")
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.version}")
        self.setGeometry(100, 100, self.settings.gui.window_width, self.settings.gui.window_height)
        
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.create_chat_tab()
        self.create_monitoring_tab()
        self.create_toggles_tab()
        self.create_logs_tab()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")
        
        self.apply_theme()
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        tools_menu = menubar.addMenu("&Tools")
        
        clear_history_action = QAction("Clear Chat History", self)
        clear_history_action.triggered.connect(self.clear_chat_history)
        tools_menu.addAction(clear_history_action)
        
        verify_audit_action = QAction("Verify Audit Log", self)
        verify_audit_action.triggered.connect(self.verify_audit_log)
        tools_menu.addAction(verify_audit_action)
        
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self.show_docs)
        help_menu.addAction(docs_action)
    
    def create_chat_tab(self):
        """Create chat interface tab."""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        model_label = QLabel(f"Model: {self.settings.llm.preferred_model}")
        layout.addWidget(model_label)
        
        self.tabs.addTab(chat_widget, "Chat")
    
    def create_monitoring_tab(self):
        """Create system monitoring tab."""
        monitor_widget = QWidget()
        layout = QVBoxLayout(monitor_widget)
        
        self.stats_label = QLabel("System Statistics")
        self.stats_label.setFont(QFont("Consolas", 10))
        layout.addWidget(self.stats_label)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory %", "Memory MB", "Status"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.process_table)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_monitoring)
        layout.addWidget(refresh_button)
        
        self.tabs.addTab(monitor_widget, "Monitoring")
    
    def create_toggles_tab(self):
        """Create toggle controls tab."""
        toggles_widget = QWidget()
        layout = QVBoxLayout(toggles_widget)
        
        info_label = QLabel(
            "Toggle controls will be implemented in CustomTkinter panel.\n"
            "For now, edit settings in config file."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.toggles_display = QTextEdit()
        self.toggles_display.setReadOnly(True)
        self.toggles_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.toggles_display)
        
        self.update_toggles_display()
        
        self.tabs.addTab(toggles_widget, "Toggles")
    
    def create_logs_tab(self):
        """Create audit logs tab."""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.logs_display)
        
        refresh_button = QPushButton("Refresh Logs")
        refresh_button.clicked.connect(self.refresh_logs)
        layout.addWidget(refresh_button)
        
        self.tabs.addTab(logs_widget, "Audit Logs")
    
    def setup_timers(self):
        """Setup periodic update timers."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.refresh_monitoring)
        self.monitor_timer.start(2000)
        
        self.logs_timer = QTimer()
        self.logs_timer.timeout.connect(self.refresh_logs)
        self.logs_timer.start(5000)
    
    def send_message(self):
        """Send chat message."""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        self.chat_input.setEnabled(False)
        self.send_button.setEnabled(False)
        
        self.chat_display.append(f"\n<b>You:</b> {message}\n")
        self.chat_input.clear()
        
        self.chat_display.append("<b>Assistant:</b> ")
        
        self.chat_thread = ChatThread(message)
        self.chat_thread.chunk_received.connect(self.on_chat_chunk)
        self.chat_thread.finished.connect(self.on_chat_finished)
        self.chat_thread.error.connect(self.on_chat_error)
        self.chat_thread.start()
        
        self.update_status("Generating response...")
    
    def on_chat_chunk(self, chunk: str):
        """Handle chat chunk received."""
        self.chat_display.insertPlainText(chunk)
        self.chat_display.ensureCursorVisible()
    
    def on_chat_finished(self):
        """Handle chat finished."""
        self.chat_display.append("\n")
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.chat_input.setFocus()
        self.update_status("Ready")
    
    def on_chat_error(self, error: str):
        """Handle chat error."""
        self.chat_display.append(f"\n<font color='red'>Error: {error}</font>\n")
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.update_status("Error occurred")
    
    def refresh_monitoring(self):
        """Refresh monitoring display."""
        try:
            monitor = get_system_monitor()
            stats = monitor.get_latest_stats()
            
            if stats:
                stats_text = f"""
<b>System Statistics</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU Usage:     {stats.cpu_percent:.1f}%
Memory:        {stats.memory_percent:.1f}% ({stats.memory_used_gb:.1f} / {stats.memory_total_gb:.1f} GB)
Disk:          {stats.disk_percent:.1f}% ({stats.disk_used_gb:.1f} / {stats.disk_total_gb:.1f} GB)
Network:       ↑ {stats.network_sent_mb:.2f} MB/s  ↓ {stats.network_recv_mb:.2f} MB/s
Processes:     {stats.process_count}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """
                self.stats_label.setText(stats_text)
            
            processes = monitor.get_process_list(limit=15)
            self.process_table.setRowCount(len(processes))
            
            for i, proc in enumerate(processes):
                self.process_table.setItem(i, 0, QTableWidgetItem(str(proc.pid)))
                self.process_table.setItem(i, 1, QTableWidgetItem(proc.name))
                self.process_table.setItem(i, 2, QTableWidgetItem(f"{proc.cpu_percent:.1f}"))
                self.process_table.setItem(i, 3, QTableWidgetItem(f"{proc.memory_percent:.1f}"))
                self.process_table.setItem(i, 4, QTableWidgetItem(f"{proc.memory_mb:.1f}"))
                self.process_table.setItem(i, 5, QTableWidgetItem(proc.status))
        
        except Exception as e:
            logger.error(f"Failed to refresh monitoring: {e}")
    
    def refresh_logs(self):
        """Refresh audit logs display."""
        try:
            audit_logger = get_audit_logger()
            entries = audit_logger.get_recent_entries(count=50)
            
            logs_text = ""
            for entry in entries:
                logs_text += f"[{entry.timestamp}] {entry.action_type}.{entry.action} - {entry.status}\n"
            
            self.logs_display.setPlainText(logs_text)
            self.logs_display.moveCursor(self.logs_display.textCursor().End)
        
        except Exception as e:
            logger.error(f"Failed to refresh logs: {e}")
    
    def update_toggles_display(self):
        """Update toggles display."""
        toggles_text = "System Toggles:\n"
        toggles_text += "━" * 50 + "\n\n"
        
        for key, value in self.settings.system_toggles.model_dump().items():
            status = "✓ ENABLED" if value else "✗ DISABLED"
            toggles_text += f"{key}: {status}\n"
        
        toggles_text += "\n" + "━" * 50 + "\n"
        toggles_text += "Financial Toggles:\n"
        toggles_text += "━" * 50 + "\n\n"
        
        for key, value in self.settings.financial_toggles.model_dump().items():
            if isinstance(value, bool):
                status = "✓ ENABLED" if value else "✗ DISABLED"
                toggles_text += f"{key}: {status}\n"
            else:
                toggles_text += f"{key}: {value}\n"
        
        self.toggles_display.setPlainText(toggles_text)
    
    def clear_chat_history(self):
        """Clear chat history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the chat history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            client = get_ollama_client()
            client.clear_history()
            self.chat_display.clear()
            self.update_status("Chat history cleared")
    
    def verify_audit_log(self):
        """Verify audit log integrity."""
        audit_logger = get_audit_logger()
        valid = audit_logger.verify_chain()
        
        if valid:
            QMessageBox.information(
                self,
                "Audit Log Verification",
                "✓ Audit log chain is valid and has not been tampered with."
            )
        else:
            QMessageBox.warning(
                self,
                "Audit Log Verification",
                "✗ Audit log chain verification failed! Log may have been tampered with."
            )
    
    def show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(
            self,
            "Settings",
            "Settings dialog will be implemented in future version.\n"
            "For now, edit config file directly."
        )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Home AI",
            f"""<h2>Home AI</h2>
            <p>Version: {self.settings.version}</p>
            <p>Windows LLM PC Control System with granular toggle controls.</p>
            <p><b>SAFE MODE:</b> All destructive operations disabled by default.</p>
            <p><b>Emergency Killswitch:</b> {self.settings.security.emergency_killswitch_key}</p>
            """
        )
    
    def show_docs(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available in the docs/ directory:\n\n"
            "• README.md - Getting started\n"
            "• SAFETY.md - Security considerations\n"
            "• TOGGLES.md - Toggle controls reference\n"
            "• Architecture.md - System architecture"
        )
    
    def update_status(self, message: str):
        """Update status bar."""
        self.status_bar.showMessage(message)
    
    def apply_theme(self):
        """Apply theme to window."""
        if self.settings.gui.theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTextEdit, QLineEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #0e639c;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    gridline-color: #3c3c3c;
                }
                QHeaderView::section {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #3c3c3c;
                }
            """)
    
    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit Home AI?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()
