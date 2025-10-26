#!/usr/bin/env python3
"""Session Switcher for Home AI OS - Toggle between Kiosk and Desktop modes."""

import sys
import subprocess
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup,
    QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SessionSwitcher(QDialog):
    """Session switcher dialog."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Home AI OS - Session Switcher")
        self.setMinimumSize(500, 400)
        
        self.current_session = self.detect_current_session()
        self.config_path = Path.home() / ".home_ai" / "config.json"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        title = QLabel("Session Mode")
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        current_label = QLabel(f"Current: {self.current_session.upper()}")
        current_label.setStyleSheet("color: #00d4ff; font-size: 12pt;")
        layout.addWidget(current_label)
        
        layout.addSpacing(20)
        
        self.session_group = QButtonGroup()
        
        self.kiosk_radio = QRadioButton("AI Kiosk Mode")
        self.kiosk_radio.setStyleSheet("font-size: 11pt; font-weight: bold;")
        layout.addWidget(self.kiosk_radio)
        
        kiosk_desc = QLabel(
            "  • Fullscreen AI interface\n"
            "  • Optimized for AI interaction\n"
            "  • Minimal distractions\n"
            "  • Press Ctrl+Alt+D to access desktop"
        )
        kiosk_desc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(kiosk_desc)
        
        layout.addSpacing(15)
        
        self.desktop_radio = QRadioButton("Full Desktop Mode")
        self.desktop_radio.setStyleSheet("font-size: 11pt; font-weight: bold;")
        layout.addWidget(self.desktop_radio)
        
        desktop_desc = QLabel(
            "  • Standard Xfce desktop\n"
            "  • Full application access\n"
            "  • Traditional desktop experience\n"
            "  • Home AI available in applications menu"
        )
        desktop_desc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(desktop_desc)
        
        self.session_group.addButton(self.kiosk_radio)
        self.session_group.addButton(self.desktop_radio)
        
        if self.current_session == "kiosk":
            self.kiosk_radio.setChecked(True)
        else:
            self.desktop_radio.setChecked(True)
        
        layout.addSpacing(20)
        
        info = QLabel(
            "Note: Changing session mode requires logging out.\n"
            "All unsaved work will be lost."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: orange; font-style: italic;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply and Logout")
        apply_btn.setStyleSheet("background-color: #00d4ff; color: black; font-weight: bold;")
        apply_btn.clicked.connect(self.apply_and_logout)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def detect_current_session(self):
        """Detect current session type."""
        config_path = Path.home() / ".home_ai" / "config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get("session_mode", "desktop")
            except:
                pass
        
        try:
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "Home AI" in result.stdout and "fullscreen" in result.stdout.lower():
                return "kiosk"
        except:
            pass
        
        return "desktop"
    
    def apply_and_logout(self):
        """Apply session change and logout."""
        if self.kiosk_radio.isChecked():
            new_session = "kiosk"
            session_name = "homeai"
        else:
            new_session = "desktop"
            session_name = "xfce"
        
        if new_session == self.current_session:
            QMessageBox.information(
                self,
                "No Change",
                f"Already in {new_session} mode."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            f"Switch to {new_session.upper()} mode?\n\n"
            "This will log you out immediately.\n"
            "Make sure to save all work before continuing.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.save_session_preference(new_session)
        
        self.update_lightdm_session(session_name)
        
        self.logout()
    
    def save_session_preference(self, session_mode):
        """Save session preference to config."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            except:
                pass
        
        config["session_mode"] = session_mode
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_lightdm_session(self, session_name):
        """Update LightDM autologin session."""
        try:
            pass
        except Exception as e:
            print(f"Could not update LightDM session: {e}")
    
    def logout(self):
        """Logout current session."""
        try:
            subprocess.run(["xfce4-session-logout", "--logout"], timeout=5)
        except:
            try:
                subprocess.run(["loginctl", "terminate-user", "$USER"], timeout=5)
            except:
                QMessageBox.warning(
                    self,
                    "Logout Failed",
                    "Could not logout automatically.\n"
                    "Please logout manually from the system menu."
                )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    dialog = SessionSwitcher()
    dialog.exec()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
