#!/usr/bin/env python3
"""Main GUI window for Home AI OS - Unified interface."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QListWidget,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon
from loguru import logger

try:
    from home_ai_os.ui.chat_tab import ChatTab
except:
    ChatTab = None

try:
    from home_ai_os.ui.vision_tab import VisionTab
except:
    VisionTab = None

try:
    from home_ai_os.ui.monitoring_tab import MonitoringTab
except:
    MonitoringTab = None

try:
    from home_ai_os.ui.business_tab import BusinessTab
except:
    BusinessTab = None

try:
    from home_ai_os.ui.logs_tab import LogsTab
except:
    LogsTab = None


class HomeAIMainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, kiosk=False):
        super().__init__()
        
        self.kiosk_mode = kiosk
        
        self.setWindowTitle("Home AI OS")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        
        if kiosk:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.showFullScreen()
        else:
            self.show()
        
        logger.info("Home AI OS main window initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        header = self.create_header()
        layout.addWidget(header)
        
        self.tabs = QTabWidget()
        
        if ChatTab:
            self.tabs.addTab(ChatTab(), "💬 Chat")
        
        if VisionTab:
            self.tabs.addTab(VisionTab(), "👁️ Vision")
        
        if MonitoringTab:
            self.tabs.addTab(MonitoringTab(), "📊 Monitoring")
        
        if BusinessTab:
            self.tabs.addTab(BusinessTab(), "💼 Business")
        
        if LogsTab:
            self.tabs.addTab(LogsTab(), "📋 Logs")
        
        layout.addWidget(self.tabs)
        
        self.statusBar().showMessage("Ready")
        
        central_widget.setLayout(layout)
    
    def create_header(self):
        """Create header bar."""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet("background-color: #1a1a2e; padding: 10px;")
        
        layout = QHBoxLayout()
        
        title = QLabel("Home AI OS")
        title.setStyleSheet("color: #00d4ff; font-size: 18pt; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        if self.kiosk_mode:
            kiosk_label = QLabel("🔒 Kiosk Mode (Ctrl+Alt+D to exit)")
            kiosk_label.setStyleSheet("color: orange; font-size: 10pt;")
            layout.addWidget(kiosk_label)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        header.setLayout(layout)
        return header
    
    def open_settings(self):
        """Open settings panel."""
        try:
            import subprocess
            subprocess.Popen(["/opt/home-ai-os/scripts/homeai-settings.py"])
        except Exception as e:
            logger.error(f"Could not open settings: {e}")
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if (self.kiosk_mode and 
            event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier) and
            event.key() == Qt.Key.Key_D):
            logger.info("Kiosk mode escape hatch activated")
            self.showNormal()
            self.kiosk_mode = False
        
        super().keyPressEvent(event)


def run_gui(kiosk=False):
    """Run the GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setApplicationName("Home AI OS")
    app.setOrganizationName("Home AI")
    app.setApplicationVersion("0.2.0")
    
    window = HomeAIMainWindow(kiosk=kiosk)
    
    return app.exec()


if __name__ == "__main__":
    run_gui()
