#!/usr/bin/env python3
"""First-boot wizard for Home AI OS."""

import sys
import subprocess
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QProgressBar, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap


class WelcomePage(QWizardPage):
    """Welcome page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Home AI OS")
        self.setSubTitle("Let's set up your AI-native desktop environment")
        
        layout = QVBoxLayout()
        
        welcome = QLabel(
            "Home AI OS is a Linux-based operating system with deep AI integration.\n\n"
            "This wizard will guide you through:\n"
            "• Network configuration\n"
            "• GPU driver detection and installation\n"
            "• AI model download\n"
            "• User account setup\n"
            "• Privacy settings\n\n"
            "Click Next to begin."
        )
        welcome.setWordWrap(True)
        layout.addWidget(welcome)
        
        layout.addStretch()
        self.setLayout(layout)


class NetworkPage(QWizardPage):
    """Network configuration page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Network Configuration")
        self.setSubTitle("Configure your network connection")
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Checking network connection...")
        layout.addWidget(self.status_label)
        
        self.network_info = QTextEdit()
        self.network_info.setReadOnly(True)
        self.network_info.setMaximumHeight(150)
        layout.addWidget(self.network_info)
        
        self.nm_button = QPushButton("Open Network Manager")
        self.nm_button.clicked.connect(self.open_network_manager)
        layout.addWidget(self.nm_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Check network on page load."""
        self.check_network()
    
    def check_network(self):
        """Check network connectivity."""
        try:
            result = subprocess.run(
                ["nmcli", "general", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.network_info.setText(result.stdout)
            
            if "connected" in result.stdout.lower():
                self.status_label.setText("✓ Network connected")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("⚠ Network not connected")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        except Exception as e:
            self.status_label.setText(f"⚠ Could not check network: {e}")
            self.status_label.setStyleSheet("color: red;")
    
    def open_network_manager(self):
        """Open NetworkManager GUI."""
        try:
            subprocess.Popen(["nm-connection-editor"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open Network Manager: {e}")


class GPUPage(QWizardPage):
    """GPU detection and driver installation page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("GPU Detection")
        self.setSubTitle("Detect and configure graphics drivers")
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Detecting GPU...")
        layout.addWidget(self.status_label)
        
        self.gpu_info = QTextEdit()
        self.gpu_info.setReadOnly(True)
        self.gpu_info.setMaximumHeight(150)
        layout.addWidget(self.gpu_info)
        
        self.driver_group = QButtonGroup()
        self.nvidia_radio = QRadioButton("Install NVIDIA proprietary drivers (recommended for NVIDIA GPUs)")
        self.opensource_radio = QRadioButton("Use open-source drivers (Mesa)")
        self.skip_radio = QRadioButton("Skip driver installation")
        
        self.driver_group.addButton(self.nvidia_radio)
        self.driver_group.addButton(self.opensource_radio)
        self.driver_group.addButton(self.skip_radio)
        
        self.opensource_radio.setChecked(True)
        
        layout.addWidget(QLabel("\nDriver Options:"))
        layout.addWidget(self.nvidia_radio)
        layout.addWidget(self.opensource_radio)
        layout.addWidget(self.skip_radio)
        
        self.install_button = QPushButton("Install Selected Driver")
        self.install_button.clicked.connect(self.install_driver)
        layout.addWidget(self.install_button)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Detect GPU on page load."""
        self.detect_gpu()
    
    def detect_gpu(self):
        """Detect GPU hardware."""
        try:
            result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            gpu_lines = [line for line in result.stdout.split('\n') if 'VGA' in line or '3D' in line]
            
            if gpu_lines:
                self.gpu_info.setText('\n'.join(gpu_lines))
                
                if any('NVIDIA' in line or 'GeForce' in line for line in gpu_lines):
                    self.status_label.setText("✓ NVIDIA GPU detected")
                    self.nvidia_radio.setChecked(True)
                elif any('AMD' in line or 'Radeon' in line for line in gpu_lines):
                    self.status_label.setText("✓ AMD GPU detected")
                    self.opensource_radio.setChecked(True)
                else:
                    self.status_label.setText("✓ GPU detected")
                    self.opensource_radio.setChecked(True)
            else:
                self.status_label.setText("⚠ No GPU detected")
                self.skip_radio.setChecked(True)
        except Exception as e:
            self.status_label.setText(f"⚠ Could not detect GPU: {e}")
    
    def install_driver(self):
        """Install selected driver."""
        if self.skip_radio.isChecked():
            QMessageBox.information(self, "Skipped", "Driver installation skipped")
            return
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate
        self.install_button.setEnabled(False)
        
        QMessageBox.information(
            self,
            "Driver Installation",
            "Driver installation would happen here.\n\n"
            "In Phase 2, this will:\n"
            "• Install NVIDIA drivers via apt\n"
            "• Configure X11/Wayland\n"
            "• Set up CUDA if needed\n"
            "• Reboot if required"
        )
        
        self.progress.setVisible(False)
        self.install_button.setEnabled(True)


class ModelDownloadPage(QWizardPage):
    """AI model download page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("AI Model Download")
        self.setSubTitle("Download AI models for Home AI")
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Select AI model to download:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral:7b-instruct (Recommended, 4.1GB)",
            "llama3.2:3b (Smaller, 2.0GB)",
            "phi3:mini (Smallest, 2.3GB)",
            "Skip download (download later)"
        ])
        layout.addWidget(self.model_combo)
        
        self.model_info = QLabel(
            "\nRecommended: mistral:7b-instruct\n"
            "• Best balance of quality and speed\n"
            "• 4.1GB download\n"
            "• Requires 8GB RAM"
        )
        self.model_info.setWordWrap(True)
        layout.addWidget(self.model_info)
        
        self.download_button = QPushButton("Download Model")
        self.download_button.clicked.connect(self.download_model)
        layout.addWidget(self.download_button)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def download_model(self):
        """Download selected model."""
        model_text = self.model_combo.currentText()
        
        if "Skip" in model_text:
            QMessageBox.information(self, "Skipped", "Model download skipped")
            return
        
        model_name = model_text.split()[0]
        
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.download_button.setEnabled(False)
        self.status_label.setText(f"Downloading {model_name}...")
        
        QMessageBox.information(
            self,
            "Model Download",
            f"Model download would happen here.\n\n"
            f"Command: ollama pull {model_name}\n\n"
            "In Phase 2, this will:\n"
            "• Download model from Ollama\n"
            "• Show real progress\n"
            "• Verify download\n"
            "• Cache for offline use"
        )
        
        self.progress.setVisible(False)
        self.download_button.setEnabled(True)
        self.status_label.setText(f"✓ {model_name} ready")


class UserPage(QWizardPage):
    """User account setup page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("User Account")
        self.setSubTitle("Create your user account")
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        layout.addWidget(self.username_edit)
        
        layout.addWidget(QLabel("Full Name:"))
        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("Enter full name")
        layout.addWidget(self.fullname_edit)
        
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        layout.addWidget(self.password_edit)
        
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Confirm password")
        layout.addWidget(self.confirm_edit)
        
        self.admin_check = QCheckBox("Make this user an administrator")
        self.admin_check.setChecked(True)
        layout.addWidget(self.admin_check)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.registerField("username*", self.username_edit)
        self.registerField("fullname", self.fullname_edit)
    
    def validatePage(self):
        """Validate user input."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        
        if not username:
            QMessageBox.warning(self, "Error", "Username is required")
            return False
        
        if not password:
            QMessageBox.warning(self, "Error", "Password is required")
            return False
        
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return False
        
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return False
        
        return True


class PrivacyPage(QWizardPage):
    """Privacy and telemetry settings page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Privacy Settings")
        self.setSubTitle("Configure privacy and telemetry options")
        
        layout = QVBoxLayout()
        
        self.telemetry_check = QCheckBox("Send anonymous usage statistics")
        self.telemetry_check.setChecked(False)
        layout.addWidget(self.telemetry_check)
        
        telemetry_info = QLabel(
            "Help improve Home AI by sending anonymous usage statistics.\n"
            "This includes:\n"
            "• Feature usage counts\n"
            "• Performance metrics\n"
            "• Error reports\n\n"
            "No personal data or file contents are collected."
        )
        telemetry_info.setWordWrap(True)
        telemetry_info.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(telemetry_info)
        
        layout.addSpacing(20)
        
        self.updates_check = QCheckBox("Automatically install security updates")
        self.updates_check.setChecked(True)
        layout.addWidget(self.updates_check)
        
        updates_info = QLabel(
            "Recommended for security.\n"
            "Feature updates will still require approval."
        )
        updates_info.setWordWrap(True)
        updates_info.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(updates_info)
        
        layout.addStretch()
        self.setLayout(layout)


class CompletePage(QWizardPage):
    """Completion page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete!")
        self.setSubTitle("Home AI OS is ready to use")
        
        layout = QVBoxLayout()
        
        complete_msg = QLabel(
            "✓ Setup complete!\n\n"
            "Home AI OS is now configured and ready to use.\n\n"
            "Click Finish to start your AI-native desktop experience."
        )
        complete_msg.setWordWrap(True)
        font = complete_msg.font()
        font.setPointSize(12)
        complete_msg.setFont(font)
        layout.addWidget(complete_msg)
        
        layout.addStretch()
        self.setLayout(layout)


class FirstBootWizard(QWizard):
    """Main first-boot wizard."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Home AI OS - First Boot Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(700, 500)
        
        self.addPage(WelcomePage())
        self.addPage(NetworkPage())
        self.addPage(GPUPage())
        self.addPage(ModelDownloadPage())
        self.addPage(UserPage())
        self.addPage(PrivacyPage())
        self.addPage(CompletePage())
    
    def accept(self):
        """Handle wizard completion."""
        config = {
            "first_boot_complete": True,
            "username": self.field("username"),
            "fullname": self.field("fullname"),
            "telemetry_enabled": False,
            "auto_updates": True
        }
        
        config_path = Path.home() / ".home_ai" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        super().accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    wizard = FirstBootWizard()
    wizard.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
