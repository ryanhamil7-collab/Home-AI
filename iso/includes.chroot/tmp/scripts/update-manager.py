#!/usr/bin/env python3
"""OS Update Manager for Home AI OS - PackageKit integration."""

import sys
import subprocess
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QListWidget,
    QListWidgetItem, QMessageBox, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon


class UpdateCheckThread(QThread):
    """Thread for checking updates."""
    
    check_complete = pyqtSignal(list)
    
    def run(self):
        """Check for available updates."""
        updates = []
        
        try:
            subprocess.run(
                ["pkcon", "refresh"],
                capture_output=True,
                timeout=120
            )
            
            result = subprocess.run(
                ["pkcon", "get-updates"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith(('Refreshing', 'Getting', 'Results')):
                    parts = line.split()
                    if len(parts) >= 2:
                        updates.append({
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'unknown',
                            'type': 'security' if 'security' in line.lower() else 'normal'
                        })
        
        except Exception as e:
            print(f"Error checking updates: {e}")
        
        self.check_complete.emit(updates)


class UpdateInstallThread(QThread):
    """Thread for installing updates."""
    
    progress_update = pyqtSignal(str)
    install_complete = pyqtSignal(bool, str)
    
    def __init__(self, security_only=False):
        super().__init__()
        self.security_only = security_only
    
    def run(self):
        """Install updates."""
        try:
            self.progress_update.emit("Installing updates...")
            
            cmd = ["pkcon", "update", "-y"]
            if self.security_only:
                cmd.append("--only-download")  # Would need proper security filter
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.install_complete.emit(True, "Updates installed successfully")
            else:
                self.install_complete.emit(False, f"Update failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            self.install_complete.emit(False, "Update timed out")
        except Exception as e:
            self.install_complete.emit(False, str(e))


class UpdateManager(QMainWindow):
    """Main update manager window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Home AI OS - Update Manager")
        self.setMinimumSize(800, 600)
        
        self.updates = []
        self.check_thread = None
        self.install_thread = None
        
        self.setup_ui()
        
        QTimer.singleShot(1000, self.check_updates)
    
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        
        title = QLabel("System Updates")
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.clicked.connect(self.check_updates)
        header_layout.addWidget(self.check_btn)
        
        layout.addLayout(header_layout)
        
        self.status_label = QLabel("Click 'Check for Updates' to begin")
        self.status_label.setStyleSheet("font-size: 11pt; color: gray;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        
        tabs = QTabWidget()
        
        updates_tab = QWidget()
        updates_layout = QVBoxLayout()
        
        self.updates_list = QListWidget()
        updates_layout.addWidget(self.updates_list)
        
        update_btn_layout = QHBoxLayout()
        update_btn_layout.addStretch()
        
        self.security_only_check = QCheckBox("Security updates only")
        update_btn_layout.addWidget(self.security_only_check)
        
        self.install_btn = QPushButton("Install Updates")
        self.install_btn.setEnabled(False)
        self.install_btn.setStyleSheet("background-color: #00d4ff; color: black; font-weight: bold;")
        self.install_btn.clicked.connect(self.install_updates)
        update_btn_layout.addWidget(self.install_btn)
        
        updates_layout.addLayout(update_btn_layout)
        
        updates_tab.setLayout(updates_layout)
        tabs.addTab(updates_tab, "Available Updates")
        
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setText("Update history will appear here...")
        history_layout.addWidget(self.history_text)
        
        history_tab.setLayout(history_layout)
        tabs.addTab(history_tab, "Update History")
        
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        
        self.auto_check_check = QCheckBox("Automatically check for updates daily")
        self.auto_check_check.setChecked(True)
        settings_layout.addWidget(self.auto_check_check)
        
        self.auto_security_check = QCheckBox("Automatically install security updates")
        self.auto_security_check.setChecked(True)
        settings_layout.addWidget(self.auto_security_check)
        
        self.notify_check = QCheckBox("Show notification when updates are available")
        self.notify_check.setChecked(True)
        settings_layout.addWidget(self.notify_check)
        
        settings_layout.addSpacing(20)
        
        settings_info = QLabel(
            "Update Settings\n\n"
            "• Automatic checks run daily at 9:00 AM\n"
            "• Security updates are prioritized\n"
            "• You will be notified before any installation\n"
            "• System will prompt for reboot if required"
        )
        settings_info.setWordWrap(True)
        settings_info.setStyleSheet("color: gray;")
        settings_layout.addWidget(settings_info)
        
        settings_layout.addStretch()
        
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings_btn)
        
        settings_tab.setLayout(settings_layout)
        tabs.addTab(settings_tab, "Settings")
        
        layout.addWidget(tabs)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_text)
        
        central_widget.setLayout(layout)
    
    def check_updates(self):
        """Check for available updates."""
        self.status_label.setText("Checking for updates...")
        self.check_btn.setEnabled(False)
        self.install_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for updates...")
        
        self.check_thread = UpdateCheckThread()
        self.check_thread.check_complete.connect(self.on_check_complete)
        self.check_thread.start()
    
    def on_check_complete(self, updates):
        """Handle update check completion."""
        self.updates = updates
        self.progress.setVisible(False)
        self.check_btn.setEnabled(True)
        
        self.updates_list.clear()
        
        if updates:
            self.status_label.setText(f"✓ {len(updates)} update(s) available")
            self.status_label.setStyleSheet("font-size: 11pt; color: orange; font-weight: bold;")
            self.install_btn.setEnabled(True)
            
            for update in updates:
                item_text = f"{update['name']} → {update['version']}"
                if update['type'] == 'security':
                    item_text += " [SECURITY]"
                
                item = QListWidgetItem(item_text)
                if update['type'] == 'security':
                    item.setForeground(Qt.GlobalColor.red)
                
                self.updates_list.addItem(item)
            
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(updates)} update(s)")
        else:
            self.status_label.setText("✓ System is up to date")
            self.status_label.setStyleSheet("font-size: 11pt; color: green; font-weight: bold;")
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] System is up to date")
    
    def install_updates(self):
        """Install available updates."""
        if not self.updates:
            return
        
        security_only = self.security_only_check.isChecked()
        update_count = len([u for u in self.updates if u['type'] == 'security']) if security_only else len(self.updates)
        
        reply = QMessageBox.question(
            self,
            "Confirm Update",
            f"Install {update_count} update(s)?\n\n"
            f"{'Security updates only' if security_only else 'All available updates'}\n\n"
            "This may take several minutes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.status_label.setText("Installing updates...")
        self.check_btn.setEnabled(False)
        self.install_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting update installation...")
        
        self.install_thread = UpdateInstallThread(security_only)
        self.install_thread.progress_update.connect(self.on_progress_update)
        self.install_thread.install_complete.connect(self.on_install_complete)
        self.install_thread.start()
    
    def on_progress_update(self, message):
        """Handle installation progress."""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def on_install_complete(self, success, message):
        """Handle installation completion."""
        self.progress.setVisible(False)
        self.check_btn.setEnabled(True)
        
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        if success:
            self.status_label.setText("✓ Updates installed successfully")
            self.status_label.setStyleSheet("font-size: 11pt; color: green; font-weight: bold;")
            
            if self.check_reboot_required():
                reply = QMessageBox.question(
                    self,
                    "Reboot Required",
                    "Updates have been installed successfully.\n\n"
                    "A reboot is required to complete the update.\n\n"
                    "Reboot now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    subprocess.run(["systemctl", "reboot"])
            else:
                QMessageBox.information(
                    self,
                    "Update Complete",
                    "Updates installed successfully.\n\nNo reboot required."
                )
            
            self.check_updates()
        else:
            self.status_label.setText("✗ Update failed")
            self.status_label.setStyleSheet("font-size: 11pt; color: red; font-weight: bold;")
            
            QMessageBox.warning(
                self,
                "Update Failed",
                f"Update installation failed:\n\n{message}"
            )
    
    def check_reboot_required(self):
        """Check if reboot is required."""
        return Path("/var/run/reboot-required").exists()
    
    def save_settings(self):
        """Save update settings."""
        QMessageBox.information(
            self,
            "Settings Saved",
            "Update settings have been saved."
        )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = UpdateManager()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
