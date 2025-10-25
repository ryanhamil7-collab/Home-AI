"""Unified main window with integrated vision, commands, business, and monitoring."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLineEdit, QPushButton,
    QLabel, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QToolBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QIcon
from loguru import logger
import sys

from home_ai.core.config import get_settings, reload_settings
from home_ai.llm.ollama_client import get_ollama_client
from home_ai.monitoring.system_monitor import get_system_monitor
from home_ai.security.audit_logger import get_audit_logger
from home_ai.ui.settings_dialog import SettingsDialog
from home_ai.ui.vision_tab import VisionTab
from home_ai.ui.business_widget import BusinessWidget


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
        self.create_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.create_vision_tab()
        self.create_commands_tab()
        self.create_business_tab()
        self.create_monitoring_tab()
        self.create_logs_tab()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")
        
        self.apply_theme()
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        
        settings_action = QAction("⚙ &Settings", self)
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
    
    def create_toolbar(self):
        """Create toolbar with quick actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.safety_status = QLabel("🟢 Safe Mode")
        self.safety_status.setStyleSheet("padding: 5px; font-weight: bold; color: #4ade80;")
        toolbar.addWidget(self.safety_status)
        
        toolbar.addSeparator()
        
        self.model_label = QLabel(f"Model: {self.settings.llm.preferred_model}")
        self.model_label.setStyleSheet("padding: 5px;")
        toolbar.addWidget(self.model_label)
        
        toolbar.addSeparator()
        
        gpu_text = "🎮 GPU" if self.settings.llm.gpu_acceleration else "💻 CPU"
        self.gpu_label = QLabel(gpu_text)
        self.gpu_label.setStyleSheet("padding: 5px;")
        toolbar.addWidget(self.gpu_label)
        
        toolbar.addWidget(QLabel("  "))
        
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)
    
    def create_vision_tab(self):
        """Create computer vision tab."""
        self.vision_tab = VisionTab()
        self.tabs.addTab(self.vision_tab, "👁 Vision")
    
    def create_commands_tab(self):
        """Create commands interface tab."""
        commands_widget = QWidget()
        layout = QVBoxLayout(commands_widget)
        
        info_label = QLabel("💬 Give natural language commands to the AI")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your command here (e.g., 'open Chrome', 'search for Python tutorials')...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        help_text = QLabel(
            "Examples: 'What's on my screen?', 'Open notepad', 'Search for AI news', "
            "'Take a screenshot', 'Show me system stats'"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("padding: 5px; color: #888;")
        layout.addWidget(help_text)
        
        self.tabs.addTab(commands_widget, "💬 Commands")
    
    def create_business_tab(self):
        """Create business dashboard tab."""
        try:
            self.business_widget = BusinessWidget()
            self.tabs.addTab(self.business_widget, "💼 Business")
        except Exception as e:
            logger.error(f"Failed to create business tab: {e}")
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel(f"Business dashboard unavailable: {e}"))
            self.tabs.addTab(placeholder, "💼 Business")
    
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
    
    
    def create_logs_tab(self):
        """Create audit logs tab."""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        header = QLabel("🔒 Audit Logs - Tamper-Proof Security Log")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.logs_display)
        
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Refresh Logs")
        refresh_button.clicked.connect(self.refresh_logs)
        button_layout.addWidget(refresh_button)
        
        verify_button = QPushButton("✓ Verify Integrity")
        verify_button.clicked.connect(self.verify_audit_log)
        button_layout.addWidget(verify_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tabs.addTab(logs_widget, "🔒 Logs")
    
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
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()
    
    def on_settings_changed(self):
        """Handle settings changed."""
        self.settings = reload_settings()
        
        self.model_label.setText(f"Model: {self.settings.llm.preferred_model}")
        gpu_text = "🎮 GPU" if self.settings.llm.gpu_acceleration else "💻 CPU"
        self.gpu_label.setText(gpu_text)
        
        self.apply_theme()
        
        self.update_status("Settings updated successfully")
        logger.info("Settings changed by user")
    
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
