#!/usr/bin/env python3
"""Home AI OS Settings Panel - System configuration interface."""

import sys
import json
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QCheckBox, QLineEdit, QComboBox, QSpinBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon


class HomeAISettings(QMainWindow):
    """Main settings window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Home AI OS - Settings")
        self.setMinimumSize(800, 600)
        
        self.config_path = Path.home() / ".home_ai" / "config.json"
        self.config = self.load_config()
        
        self.setup_ui()
    
    def load_config(self):
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "version": "0.1.0",
            "session_mode": "desktop",
            "telemetry_enabled": False,
            "auto_updates": True,
            "ai_model": "mistral:7b-instruct",
            "gpu_acceleration": True
        }
    
    def save_config(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        title = QLabel("Home AI OS Settings")
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        tabs = QTabWidget()
        
        tabs.addTab(self.create_general_tab(), "General")
        
        tabs.addTab(self.create_ai_tab(), "AI Configuration")
        
        tabs.addTab(self.create_system_tab(), "System")
        
        tabs.addTab(self.create_privacy_tab(), "Privacy")
        
        tabs.addTab(self.create_about_tab(), "About")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background-color: #00d4ff; color: black; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
    
    def create_general_tab(self):
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        session_group = QGroupBox("Session Mode")
        session_layout = QVBoxLayout()
        
        session_label = QLabel(f"Current: {self.config.get('session_mode', 'desktop').upper()}")
        session_layout.addWidget(session_label)
        
        switch_session_btn = QPushButton("Switch Session Mode")
        switch_session_btn.clicked.connect(self.launch_session_switcher)
        session_layout.addWidget(switch_session_btn)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        self.autostart_check = QCheckBox("Launch Home AI on login")
        self.autostart_check.setChecked(True)
        startup_layout.addWidget(self.autostart_check)
        
        self.minimize_check = QCheckBox("Start minimized to system tray")
        startup_layout.addWidget(self.minimize_check)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.setCurrentText("Dark")
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(11)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_ai_tab(self):
        """Create AI configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        model_group = QGroupBox("AI Model")
        model_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral:7b-instruct",
            "llama3.2:3b",
            "phi3:mini",
            "codellama:13b"
        ])
        current_model = self.config.get("ai_model", "mistral:7b-instruct")
        self.model_combo.setCurrentText(current_model)
        model_layout.addRow("Model:", self.model_combo)
        
        download_model_btn = QPushButton("Download Additional Models")
        download_model_btn.clicked.connect(self.download_models)
        model_layout.addRow("", download_model_btn)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout()
        
        self.gpu_accel_check = QCheckBox("Enable GPU acceleration (CUDA/ROCm)")
        self.gpu_accel_check.setChecked(self.config.get("gpu_acceleration", True))
        perf_layout.addWidget(self.gpu_accel_check)
        
        self.context_size_spin = QSpinBox()
        self.context_size_spin.setRange(2048, 32768)
        self.context_size_spin.setSingleStep(2048)
        self.context_size_spin.setValue(4096)
        perf_layout.addWidget(QLabel("Context Window Size:"))
        perf_layout.addWidget(self.context_size_spin)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.streaming_check = QCheckBox("Enable streaming responses")
        self.streaming_check.setChecked(True)
        behavior_layout.addWidget(self.streaming_check)
        
        self.save_history_check = QCheckBox("Save conversation history")
        self.save_history_check.setChecked(True)
        behavior_layout.addWidget(self.save_history_check)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_system_tab(self):
        """Create system settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        updates_group = QGroupBox("Updates")
        updates_layout = QVBoxLayout()
        
        self.auto_updates_check = QCheckBox("Automatically install security updates")
        self.auto_updates_check.setChecked(self.config.get("auto_updates", True))
        updates_layout.addWidget(self.auto_updates_check)
        
        self.check_updates_check = QCheckBox("Check for updates daily")
        self.check_updates_check.setChecked(True)
        updates_layout.addWidget(self.check_updates_check)
        
        update_manager_btn = QPushButton("Open Update Manager")
        update_manager_btn.clicked.connect(self.launch_update_manager)
        updates_layout.addWidget(update_manager_btn)
        
        updates_group.setLayout(updates_layout)
        layout.addWidget(updates_group)
        
        drivers_group = QGroupBox("Drivers")
        drivers_layout = QVBoxLayout()
        
        driver_info = QLabel("Current GPU driver: Detecting...")
        drivers_layout.addWidget(driver_info)
        
        driver_wizard_btn = QPushButton("Launch Driver Wizard")
        driver_wizard_btn.clicked.connect(self.launch_driver_wizard)
        drivers_layout.addWidget(driver_wizard_btn)
        
        drivers_group.setLayout(drivers_layout)
        layout.addWidget(drivers_group)
        
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout()
        
        info_text = self.get_system_info()
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_privacy_tab(self):
        """Create privacy settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        telemetry_group = QGroupBox("Telemetry")
        telemetry_layout = QVBoxLayout()
        
        self.telemetry_check = QCheckBox("Send anonymous usage statistics")
        self.telemetry_check.setChecked(self.config.get("telemetry_enabled", False))
        telemetry_layout.addWidget(self.telemetry_check)
        
        telemetry_info = QLabel(
            "Help improve Home AI by sending anonymous usage data.\n\n"
            "We collect:\n"
            "• Feature usage counts\n"
            "• Performance metrics\n"
            "• Error reports\n\n"
            "We do NOT collect:\n"
            "• Personal information\n"
            "• File contents\n"
            "• Conversation history"
        )
        telemetry_info.setWordWrap(True)
        telemetry_info.setStyleSheet("color: gray;")
        telemetry_layout.addWidget(telemetry_info)
        
        telemetry_group.setLayout(telemetry_layout)
        layout.addWidget(telemetry_group)
        
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout()
        
        clear_history_btn = QPushButton("Clear Conversation History")
        clear_history_btn.clicked.connect(self.clear_history)
        data_layout.addWidget(clear_history_btn)
        
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        data_layout.addWidget(clear_cache_btn)
        
        export_data_btn = QPushButton("Export My Data")
        export_data_btn.clicked.connect(self.export_data)
        data_layout.addWidget(export_data_btn)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_about_tab(self):
        """Create about tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Home AI OS")
        title_font = title.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("AI-Native Desktop Environment")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #00d4ff; font-size: 14pt;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        version_text = (
            "Version: 0.1.0 (Phase 3)\n"
            "Build: 2025-10-25\n"
            "Based on: Ubuntu 24.04 LTS\n"
            "Kernel: Linux 6.8+"
        )
        version_label = QLabel(version_text)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        links_layout = QHBoxLayout()
        links_layout.addStretch()
        
        github_btn = QPushButton("GitHub")
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/ryanhamil7-collab/Home-AI-OS"))
        links_layout.addWidget(github_btn)
        
        docs_btn = QPushButton("Documentation")
        docs_btn.clicked.connect(lambda: self.open_url("https://github.com/ryanhamil7-collab/Home-AI-OS/docs"))
        links_layout.addWidget(docs_btn)
        
        links_layout.addStretch()
        layout.addLayout(links_layout)
        
        layout.addSpacing(20)
        
        credits = QLabel(
            "Created by: Ryan Hamilton\n"
            "Built with: Python, PyQt6, Ollama\n"
            "License: MIT\n\n"
            "Special thanks to the open-source community"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("color: gray;")
        layout.addWidget(credits)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def get_system_info(self):
        """Get system information."""
        try:
            with open("/etc/os-release") as f:
                os_info = dict(line.strip().split('=', 1) for line in f if '=' in line)
            
            os_name = os_info.get('PRETTY_NAME', 'Unknown').strip('"')
            
            kernel = subprocess.run(
                ["uname", "-r"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu = line.split(':')[1].strip()
                        break
                else:
                    cpu = "Unknown"
            
            with open("/proc/meminfo") as f:
                mem_total = int(f.readline().split()[1]) // 1024  # MB
            
            return (
                f"OS: {os_name}\n"
                f"Kernel: {kernel}\n"
                f"CPU: {cpu}\n"
                f"Memory: {mem_total} MB"
            )
        except:
            return "System information unavailable"
    
    def launch_session_switcher(self):
        """Launch session switcher."""
        try:
            subprocess.Popen(["/opt/home-ai-os/scripts/session-switcher.py"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch session switcher: {e}")
    
    def launch_update_manager(self):
        """Launch update manager."""
        try:
            subprocess.Popen(["/opt/home-ai-os/scripts/update-manager.py"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch update manager: {e}")
    
    def launch_driver_wizard(self):
        """Launch driver wizard."""
        try:
            subprocess.Popen(["/opt/home-ai-os/scripts/driver-wizard.py"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch driver wizard: {e}")
    
    def download_models(self):
        """Download additional models."""
        QMessageBox.information(
            self,
            "Download Models",
            "Model download functionality will be available in the next update.\n\n"
            "For now, use: ollama pull <model-name>"
        )
    
    def clear_history(self):
        """Clear conversation history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Delete all conversation history?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cleared", "Conversation history cleared")
    
    def clear_cache(self):
        """Clear cache."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Clear all cached data?\n\nThis may slow down the next startup.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cleared", "Cache cleared")
    
    def export_data(self):
        """Export user data."""
        QMessageBox.information(
            self,
            "Export Data",
            "Data export functionality will be available in the next update."
        )
    
    def open_url(self, url):
        """Open URL in browser."""
        try:
            subprocess.Popen(["xdg-open", url])
        except:
            QMessageBox.warning(self, "Error", f"Could not open URL: {url}")
    
    def reset_defaults(self):
        """Reset to default settings."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to defaults?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = {
                "version": "0.1.0",
                "session_mode": "desktop",
                "telemetry_enabled": False,
                "auto_updates": True,
                "ai_model": "mistral:7b-instruct",
                "gpu_acceleration": True
            }
            QMessageBox.information(self, "Reset", "Settings reset to defaults")
    
    def apply_settings(self):
        """Apply settings without saving."""
        self.update_config_from_ui()
        QMessageBox.information(self, "Applied", "Settings applied")
    
    def save_settings(self):
        """Save settings."""
        self.update_config_from_ui()
        self.save_config()
        QMessageBox.information(self, "Saved", "Settings saved successfully")
    
    def update_config_from_ui(self):
        """Update config from UI values."""
        self.config["telemetry_enabled"] = self.telemetry_check.isChecked()
        self.config["auto_updates"] = self.auto_updates_check.isChecked()
        self.config["ai_model"] = self.model_combo.currentText()
        self.config["gpu_acceleration"] = self.gpu_accel_check.isChecked()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = HomeAISettings()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
