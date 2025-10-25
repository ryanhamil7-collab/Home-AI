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
from home_ai.vision.screen_capture import get_screen_capture
from home_ai.automation.navigator import get_navigator
from home_ai.automation.window_manager import get_window_manager


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
        self.create_vision_tab()
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
    
    def create_vision_tab(self):
        """Create computer vision tab."""
        vision_widget = QWidget()
        layout = QVBoxLayout(vision_widget)
        
        controls_layout = QHBoxLayout()
        
        self.vision_start_button = QPushButton("Start Live Capture")
        self.vision_start_button.clicked.connect(self.start_vision_capture)
        controls_layout.addWidget(self.vision_start_button)
        
        self.vision_stop_button = QPushButton("Stop Capture")
        self.vision_stop_button.clicked.connect(self.stop_vision_capture)
        self.vision_stop_button.setEnabled(False)
        controls_layout.addWidget(self.vision_stop_button)
        
        self.vision_screenshot_button = QPushButton("Take Screenshot")
        self.vision_screenshot_button.clicked.connect(self.take_screenshot)
        controls_layout.addWidget(self.vision_screenshot_button)
        
        layout.addLayout(controls_layout)
        
        self.vision_status_label = QLabel("Vision System: Inactive")
        self.vision_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.vision_status_label)
        
        nav_label = QLabel("Autonomous Navigation:")
        nav_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(nav_label)
        
        nav_layout = QHBoxLayout()
        
        self.nav_enabled_button = QPushButton("Enable Navigation")
        self.nav_enabled_button.clicked.connect(self.toggle_navigation)
        nav_layout.addWidget(self.nav_enabled_button)
        
        nav_layout.addWidget(QLabel("Mouse Position:"))
        self.mouse_pos_label = QLabel("(0, 0)")
        nav_layout.addWidget(self.mouse_pos_label)
        
        layout.addLayout(nav_layout)
        
        window_label = QLabel("Window Management:")
        window_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(window_label)
        
        self.window_list_table = QTableWidget()
        self.window_list_table.setColumnCount(5)
        self.window_list_table.setHorizontalHeaderLabels([
            "Title", "X", "Y", "Width", "Height"
        ])
        self.window_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.window_list_table)
        
        window_controls_layout = QHBoxLayout()
        
        refresh_windows_button = QPushButton("Refresh Windows")
        refresh_windows_button.clicked.connect(self.refresh_windows)
        window_controls_layout.addWidget(refresh_windows_button)
        
        activate_window_button = QPushButton("Activate Selected")
        activate_window_button.clicked.connect(self.activate_selected_window)
        window_controls_layout.addWidget(activate_window_button)
        
        layout.addLayout(window_controls_layout)
        
        info_text = QLabel(
            "Live computer vision enables the LLM to see and navigate the desktop autonomously.\n"
            "All navigation actions are gated through the policy engine and logged."
        )
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        self.tabs.addTab(vision_widget, "Vision")
    
    def start_vision_capture(self):
        """Start live vision capture."""
        try:
            screen_capture = get_screen_capture()
            screen_capture.start_capture()
            
            self.vision_status_label.setText("Vision System: Active (Capturing)")
            self.vision_start_button.setEnabled(False)
            self.vision_stop_button.setEnabled(True)
            
            self.update_status("Vision capture started")
            logger.info("Vision capture started from GUI")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to start vision capture: {e}")
    
    def stop_vision_capture(self):
        """Stop live vision capture."""
        try:
            screen_capture = get_screen_capture()
            screen_capture.stop_capture()
            
            self.vision_status_label.setText("Vision System: Inactive")
            self.vision_start_button.setEnabled(True)
            self.vision_stop_button.setEnabled(False)
            
            self.update_status("Vision capture stopped")
            logger.info("Vision capture stopped from GUI")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to stop vision capture: {e}")
    
    def take_screenshot(self):
        """Take a screenshot."""
        try:
            from pathlib import Path
            
            screen_capture = get_screen_capture()
            frame = screen_capture.capture_frame()
            
            screenshots_dir = Path.home() / "Documents" / "HomeAI" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = screenshots_dir / f"screenshot_{frame.timestamp.replace(':', '-')}.png"
            frame.save(filepath)
            
            QMessageBox.information(self, "Screenshot", f"Screenshot saved to:\n{filepath}")
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to take screenshot: {e}")
    
    def toggle_navigation(self):
        """Toggle autonomous navigation."""
        if self.nav_enabled_button.text() == "Enable Navigation":
            reply = QMessageBox.question(
                self,
                "Enable Navigation",
                "Enable autonomous navigation?\n\n"
                "This allows the LLM to control mouse and keyboard.\n"
                "All actions are logged and gated through policy engine.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.nav_enabled_button.setText("Disable Navigation")
                self.update_status("Autonomous navigation enabled")
                logger.info("Autonomous navigation enabled")
        else:
            self.nav_enabled_button.setText("Enable Navigation")
            self.update_status("Autonomous navigation disabled")
            logger.info("Autonomous navigation disabled")
    
    def refresh_windows(self):
        """Refresh window list."""
        try:
            window_manager = get_window_manager()
            windows = window_manager.list_windows(include_minimized=False)
            
            self.window_list_table.setRowCount(len(windows))
            
            for i, window in enumerate(windows):
                self.window_list_table.setItem(i, 0, QTableWidgetItem(window.title))
                self.window_list_table.setItem(i, 1, QTableWidgetItem(str(window.x)))
                self.window_list_table.setItem(i, 2, QTableWidgetItem(str(window.y)))
                self.window_list_table.setItem(i, 3, QTableWidgetItem(str(window.width)))
                self.window_list_table.setItem(i, 4, QTableWidgetItem(str(window.height)))
            
            self.update_status(f"Found {len(windows)} windows")
        except Exception as e:
            logger.error(f"Failed to refresh windows: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh windows: {e}")
    
    def activate_selected_window(self):
        """Activate selected window."""
        try:
            current_row = self.window_list_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Warning", "Please select a window first")
                return
            
            title = self.window_list_table.item(current_row, 0).text()
            
            window_manager = get_window_manager()
            success = window_manager.activate_window(title)
            
            if success:
                self.update_status(f"Activated window: {title}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to activate window: {title}")
        except Exception as e:
            logger.error(f"Failed to activate window: {e}")
            QMessageBox.warning(self, "Error", f"Failed to activate window: {e}")
    
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
        
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.update_mouse_position)
        self.mouse_timer.start(100)
    
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
    
    def update_mouse_position(self):
        """Update mouse position display."""
        try:
            import pyautogui
            x, y = pyautogui.position()
            if hasattr(self, 'mouse_pos_label'):
                self.mouse_pos_label.setText(f"({x}, {y})")
        except:
            pass
    
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
