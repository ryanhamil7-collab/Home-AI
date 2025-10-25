"""Comprehensive settings dialog for Home AI."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QGroupBox, QGridLayout, QSlider, QLineEdit,
    QMessageBox, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import json
from loguru import logger

from home_ai.core.config import get_config
from home_ai.security.policy_engine import get_policy_engine, ActionScope
from home_ai.safety.spending_caps import get_spending_tracker, SpendingLimits


class SettingsDialog(QDialog):
    """
    Comprehensive settings dialog with wide control over safety and AI settings.
    
    Features:
    - Safety settings (spending limits, permissions, confirmations)
    - AI settings (model selection, parameters, vision)
    - General settings (logging, monitoring, UI)
    - Import/export configurations
    - Reset to defaults
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        
        self.config = get_config()
        self.policy_engine = get_policy_engine()
        self.spending_tracker = get_spending_tracker()
        
        self.init_ui()
        self.load_current_settings()
        
        logger.info("SettingsDialog initialized")
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Home AI - Settings")
        self.setGeometry(100, 100, 900, 700)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("⚙️ Settings")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_safety_tab(), "🔒 Safety")
        self.tabs.addTab(self.create_ai_tab(), "🤖 AI Settings")
        self.tabs.addTab(self.create_permissions_tab(), "🔑 Permissions")
        self.tabs.addTab(self.create_general_tab(), "⚙️ General")
        layout.addWidget(self.tabs)
        
        button_layout = QHBoxLayout()
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_settings)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_settings)
        button_layout.addWidget(export_btn)
        
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def create_safety_tab(self) -> QWidget:
        """Create safety settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        spending_group = QGroupBox("💰 Spending Limits")
        spending_layout = QGridLayout()
        
        spending_layout.addWidget(QLabel("Daily Limit ($):"), 0, 0)
        self.daily_limit = QDoubleSpinBox()
        self.daily_limit.setRange(0, 10000)
        self.daily_limit.setSingleStep(10)
        self.daily_limit.setDecimals(2)
        spending_layout.addWidget(self.daily_limit, 0, 1)
        
        spending_layout.addWidget(QLabel("Weekly Limit ($):"), 1, 0)
        self.weekly_limit = QDoubleSpinBox()
        self.weekly_limit.setRange(0, 50000)
        self.weekly_limit.setSingleStep(50)
        self.weekly_limit.setDecimals(2)
        spending_layout.addWidget(self.weekly_limit, 1, 1)
        
        spending_layout.addWidget(QLabel("Monthly Limit ($):"), 2, 0)
        self.monthly_limit = QDoubleSpinBox()
        self.monthly_limit.setRange(0, 200000)
        self.monthly_limit.setSingleStep(100)
        self.monthly_limit.setDecimals(2)
        spending_layout.addWidget(self.monthly_limit, 2, 1)
        
        spending_layout.addWidget(QLabel("Per-Transaction Limit ($):"), 3, 0)
        self.per_transaction_limit = QDoubleSpinBox()
        self.per_transaction_limit.setRange(0, 10000)
        self.per_transaction_limit.setSingleStep(10)
        self.per_transaction_limit.setDecimals(2)
        spending_layout.addWidget(self.per_transaction_limit, 3, 1)
        
        spending_layout.addWidget(QLabel("Circuit Breaker Multiplier:"), 4, 0)
        self.circuit_breaker_multiplier = QDoubleSpinBox()
        self.circuit_breaker_multiplier.setRange(1.0, 10.0)
        self.circuit_breaker_multiplier.setSingleStep(0.5)
        self.circuit_breaker_multiplier.setDecimals(1)
        spending_layout.addWidget(self.circuit_breaker_multiplier, 4, 1)
        
        spending_group.setLayout(spending_layout)
        scroll_layout.addWidget(spending_group)
        
        confirm_group = QGroupBox("✅ Confirmation Requirements")
        confirm_layout = QVBoxLayout()
        
        self.require_confirmation_financial = QCheckBox("Require confirmation for financial operations")
        self.require_confirmation_financial.setChecked(True)
        confirm_layout.addWidget(self.require_confirmation_financial)
        
        self.require_confirmation_destructive = QCheckBox("Require confirmation for destructive operations")
        self.require_confirmation_destructive.setChecked(True)
        confirm_layout.addWidget(self.require_confirmation_destructive)
        
        self.require_confirmation_network = QCheckBox("Require confirmation for network operations")
        confirm_layout.addWidget(self.require_confirmation_network)
        
        self.require_2fa = QCheckBox("Require 2FA for high-risk operations")
        confirm_layout.addWidget(self.require_2fa)
        
        confirm_group.setLayout(confirm_layout)
        scroll_layout.addWidget(confirm_group)
        
        audit_group = QGroupBox("📝 Audit & Monitoring")
        audit_layout = QVBoxLayout()
        
        self.enable_audit_logging = QCheckBox("Enable audit logging")
        self.enable_audit_logging.setChecked(True)
        audit_layout.addWidget(self.enable_audit_logging)
        
        self.screenshot_sensitive_actions = QCheckBox("Screenshot sensitive actions")
        audit_layout.addWidget(self.screenshot_sensitive_actions)
        
        self.alert_suspicious_patterns = QCheckBox("Alert on suspicious patterns")
        audit_layout.addWidget(self.alert_suspicious_patterns)
        
        audit_group.setLayout(audit_layout)
        scroll_layout.addWidget(audit_group)
        
        emergency_group = QGroupBox("🚨 Emergency Controls")
        emergency_layout = QVBoxLayout()
        
        emergency_layout.addWidget(QLabel("Killswitch Hotkey: Ctrl+Alt+Shift+K (cannot be changed)"))
        
        self.auto_pause_on_error = QCheckBox("Auto-pause on critical errors")
        self.auto_pause_on_error.setChecked(True)
        emergency_layout.addWidget(self.auto_pause_on_error)
        
        emergency_group.setLayout(emergency_layout)
        scroll_layout.addWidget(emergency_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_ai_tab(self) -> QWidget:
        """Create AI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        model_group = QGroupBox("🤖 Model Selection")
        model_layout = QGridLayout()
        
        model_layout.addWidget(QLabel("Primary LLM Model:"), 0, 0)
        self.llm_model = QComboBox()
        self.llm_model.addItems([
            "mistral:7b-instruct",
            "llama3.2:3b",
            "llama3.2:1b",
            "phi3:mini",
            "codellama:13b",
            "deepseek-coder:6.7b"
        ])
        model_layout.addWidget(self.llm_model, 0, 1)
        
        model_layout.addWidget(QLabel("Vision Model:"), 1, 0)
        self.vision_model = QComboBox()
        self.vision_model.addItems([
            "llava:7b",
            "llava:13b",
            "bakllava:7b"
        ])
        model_layout.addWidget(self.vision_model, 1, 1)
        
        model_layout.addWidget(QLabel("Code Model:"), 2, 0)
        self.code_model = QComboBox()
        self.code_model.addItems([
            "codellama:13b",
            "deepseek-coder:6.7b",
            "mistral:7b-instruct"
        ])
        model_layout.addWidget(self.code_model, 2, 1)
        
        model_group.setLayout(model_layout)
        scroll_layout.addWidget(model_group)
        
        params_group = QGroupBox("⚙️ Generation Parameters")
        params_layout = QGridLayout()
        
        params_layout.addWidget(QLabel("Temperature:"), 0, 0)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setDecimals(1)
        self.temperature.setValue(0.7)
        params_layout.addWidget(self.temperature, 0, 1)
        params_layout.addWidget(QLabel("(0.0 = deterministic, 2.0 = creative)"), 0, 2)
        
        params_layout.addWidget(QLabel("Top P:"), 1, 0)
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0.0, 1.0)
        self.top_p.setSingleStep(0.05)
        self.top_p.setDecimals(2)
        self.top_p.setValue(0.9)
        params_layout.addWidget(self.top_p, 1, 1)
        params_layout.addWidget(QLabel("(nucleus sampling)"), 1, 2)
        
        params_layout.addWidget(QLabel("Top K:"), 2, 0)
        self.top_k = QSpinBox()
        self.top_k.setRange(1, 100)
        self.top_k.setValue(40)
        params_layout.addWidget(self.top_k, 2, 1)
        params_layout.addWidget(QLabel("(top-k sampling)"), 2, 2)
        
        params_layout.addWidget(QLabel("Context Window:"), 3, 0)
        self.context_window = QComboBox()
        self.context_window.addItems(["2048", "4096", "8192", "16384", "32768"])
        self.context_window.setCurrentText("4096")
        params_layout.addWidget(self.context_window, 3, 1)
        params_layout.addWidget(QLabel("(tokens)"), 3, 2)
        
        params_layout.addWidget(QLabel("Max Tokens:"), 4, 0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 8192)
        self.max_tokens.setSingleStep(100)
        self.max_tokens.setValue(2048)
        params_layout.addWidget(self.max_tokens, 4, 1)
        
        params_group.setLayout(params_layout)
        scroll_layout.addWidget(params_group)
        
        perf_group = QGroupBox("⚡ Performance")
        perf_layout = QVBoxLayout()
        
        self.enable_streaming = QCheckBox("Enable streaming responses")
        self.enable_streaming.setChecked(True)
        perf_layout.addWidget(self.enable_streaming)
        
        self.enable_gpu = QCheckBox("Enable GPU acceleration (if available)")
        self.enable_gpu.setChecked(True)
        perf_layout.addWidget(self.enable_gpu)
        
        self.parallel_requests = QCheckBox("Allow parallel LLM requests")
        perf_layout.addWidget(self.parallel_requests)
        
        perf_group.setLayout(perf_layout)
        scroll_layout.addWidget(perf_group)
        
        vision_group = QGroupBox("👁️ Vision Settings")
        vision_layout = QGridLayout()
        
        vision_layout.addWidget(QLabel("Screen Capture FPS:"), 0, 0)
        self.vision_fps = QSpinBox()
        self.vision_fps.setRange(1, 30)
        self.vision_fps.setValue(2)
        vision_layout.addWidget(self.vision_fps, 0, 1)
        
        vision_layout.addWidget(QLabel("Vision Analysis Interval (s):"), 1, 0)
        self.vision_interval = QSpinBox()
        self.vision_interval.setRange(1, 60)
        self.vision_interval.setValue(5)
        vision_layout.addWidget(self.vision_interval, 1, 1)
        
        self.enable_ocr = QCheckBox("Enable OCR text extraction")
        vision_layout.addWidget(self.enable_ocr, 2, 0, 1, 2)
        
        vision_group.setLayout(vision_layout)
        scroll_layout.addWidget(vision_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_permissions_tab(self) -> QWidget:
        """Create permissions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        file_group = QGroupBox("📁 File System")
        file_layout = QVBoxLayout()
        
        self.allow_file_read = QCheckBox("Allow file reading")
        self.allow_file_read.setChecked(True)
        file_layout.addWidget(self.allow_file_read)
        
        self.allow_file_write = QCheckBox("Allow file writing")
        file_layout.addWidget(self.allow_file_write)
        
        self.allow_file_delete = QCheckBox("Allow file deletion")
        file_layout.addWidget(self.allow_file_delete)
        
        self.allow_file_execute = QCheckBox("Allow file execution")
        file_layout.addWidget(self.allow_file_execute)
        
        file_group.setLayout(file_layout)
        scroll_layout.addWidget(file_group)
        
        network_group = QGroupBox("🌐 Network")
        network_layout = QVBoxLayout()
        
        self.allow_internet_access = QCheckBox("Allow internet access")
        network_layout.addWidget(self.allow_internet_access)
        
        self.allow_api_calls = QCheckBox("Allow API calls")
        network_layout.addWidget(self.allow_api_calls)
        
        self.allow_web_scraping = QCheckBox("Allow web scraping")
        network_layout.addWidget(self.allow_web_scraping)
        
        network_group.setLayout(network_layout)
        scroll_layout.addWidget(network_group)
        
        system_group = QGroupBox("💻 System")
        system_layout = QVBoxLayout()
        
        self.allow_process_control = QCheckBox("Allow process control")
        system_layout.addWidget(self.allow_process_control)
        
        self.allow_window_management = QCheckBox("Allow window management")
        self.allow_window_management.setChecked(True)
        system_layout.addWidget(self.allow_window_management)
        
        self.allow_keyboard_mouse = QCheckBox("Allow keyboard/mouse control")
        system_layout.addWidget(self.allow_keyboard_mouse)
        
        system_group.setLayout(system_layout)
        scroll_layout.addWidget(system_group)
        
        financial_group = QGroupBox("💳 Financial")
        financial_layout = QVBoxLayout()
        
        self.allow_financial_read = QCheckBox("Allow reading financial data")
        financial_layout.addWidget(self.allow_financial_read)
        
        self.allow_financial_transactions = QCheckBox("Allow financial transactions (DANGEROUS)")
        financial_layout.addWidget(self.allow_financial_transactions)
        
        self.paper_trading_only = QCheckBox("Paper trading only (simulation)")
        self.paper_trading_only.setChecked(True)
        financial_layout.addWidget(self.paper_trading_only)
        
        financial_group.setLayout(financial_layout)
        scroll_layout.addWidget(financial_group)
        
        social_group = QGroupBox("📱 Social Media")
        social_layout = QVBoxLayout()
        
        self.allow_social_read = QCheckBox("Allow reading social media")
        social_layout.addWidget(self.allow_social_read)
        
        self.allow_social_post = QCheckBox("Allow posting to social media")
        social_layout.addWidget(self.allow_social_post)
        
        social_group.setLayout(social_layout)
        scroll_layout.addWidget(social_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        ui_group = QGroupBox("🎨 User Interface")
        ui_layout = QVBoxLayout()
        
        self.dark_theme = QCheckBox("Dark theme")
        self.dark_theme.setChecked(True)
        ui_layout.addWidget(self.dark_theme)
        
        self.show_system_tray = QCheckBox("Show system tray icon")
        self.show_system_tray.setChecked(True)
        ui_layout.addWidget(self.show_system_tray)
        
        self.minimize_to_tray = QCheckBox("Minimize to tray")
        ui_layout.addWidget(self.minimize_to_tray)
        
        ui_group.setLayout(ui_layout)
        scroll_layout.addWidget(ui_group)
        
        log_group = QGroupBox("📋 Logging")
        log_layout = QGridLayout()
        
        log_layout.addWidget(QLabel("Log Level:"), 0, 0)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setCurrentText("INFO")
        log_layout.addWidget(self.log_level, 0, 1)
        
        log_layout.addWidget(QLabel("Max Log Size (MB):"), 1, 0)
        self.max_log_size = QSpinBox()
        self.max_log_size.setRange(1, 1000)
        self.max_log_size.setValue(100)
        log_layout.addWidget(self.max_log_size, 1, 1)
        
        log_layout.addWidget(QLabel("Log Retention (days):"), 2, 0)
        self.log_retention = QSpinBox()
        self.log_retention.setRange(1, 365)
        self.log_retention.setValue(30)
        log_layout.addWidget(self.log_retention, 2, 1)
        
        log_group.setLayout(log_layout)
        scroll_layout.addWidget(log_group)
        
        startup_group = QGroupBox("🚀 Startup")
        startup_layout = QVBoxLayout()
        
        self.start_with_windows = QCheckBox("Start with Windows")
        startup_layout.addWidget(self.start_with_windows)
        
        self.start_minimized = QCheckBox("Start minimized")
        startup_layout.addWidget(self.start_minimized)
        
        self.auto_connect_hive = QCheckBox("Auto-connect to hive mind")
        startup_layout.addWidget(self.auto_connect_hive)
        
        startup_group.setLayout(startup_layout)
        scroll_layout.addWidget(startup_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def load_current_settings(self):
        """Load current settings into UI."""
        try:
            limits = self.spending_tracker.limits
            self.daily_limit.setValue(limits.daily_limit)
            self.weekly_limit.setValue(limits.weekly_limit)
            self.monthly_limit.setValue(limits.monthly_limit)
            self.per_transaction_limit.setValue(limits.per_transaction_limit)
            self.circuit_breaker_multiplier.setValue(limits.circuit_breaker_multiplier)
            
            self.llm_model.setCurrentText(self.config.llm_model)
            self.temperature.setValue(self.config.temperature)
            self.top_p.setValue(self.config.top_p)
            self.top_k.setValue(self.config.top_k)
            
            logger.info("Loaded current settings into UI")
        
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save settings and apply changes."""
        try:
            new_limits = SpendingLimits(
                daily_limit=self.daily_limit.value(),
                weekly_limit=self.weekly_limit.value(),
                monthly_limit=self.monthly_limit.value(),
                per_transaction_limit=self.per_transaction_limit.value(),
                circuit_breaker_multiplier=self.circuit_breaker_multiplier.value()
            )
            self.spending_tracker.update_limits(new_limits)
            
            self.config.llm_model = self.llm_model.currentText()
            self.config.temperature = self.temperature.value()
            self.config.top_p = self.top_p.value()
            self.config.top_k = self.top_k.value()
            self.config.save()
            
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            logger.info("Settings saved successfully")
            
            self.accept()
        
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def import_settings(self):
        """Import settings from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    settings = json.load(f)
                
                if "spending" in settings:
                    self.daily_limit.setValue(settings["spending"].get("daily_limit", 10.0))
                    self.weekly_limit.setValue(settings["spending"].get("weekly_limit", 50.0))
                    self.monthly_limit.setValue(settings["spending"].get("monthly_limit", 200.0))
                
                if "ai" in settings:
                    if "model" in settings["ai"]:
                        self.llm_model.setCurrentText(settings["ai"]["model"])
                    if "temperature" in settings["ai"]:
                        self.temperature.setValue(settings["ai"]["temperature"])
                
                QMessageBox.information(self, "Success", "Settings imported successfully!")
                logger.info(f"Imported settings from: {filepath}")
            
            except Exception as e:
                logger.error(f"Failed to import settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")
    
    def export_settings(self):
        """Export settings to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            str(Path.home() / "home_ai_settings.json"),
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                settings = {
                    "spending": {
                        "daily_limit": self.daily_limit.value(),
                        "weekly_limit": self.weekly_limit.value(),
                        "monthly_limit": self.monthly_limit.value(),
                        "per_transaction_limit": self.per_transaction_limit.value(),
                        "circuit_breaker_multiplier": self.circuit_breaker_multiplier.value()
                    },
                    "ai": {
                        "model": self.llm_model.currentText(),
                        "vision_model": self.vision_model.currentText(),
                        "code_model": self.code_model.currentText(),
                        "temperature": self.temperature.value(),
                        "top_p": self.top_p.value(),
                        "top_k": self.top_k.value(),
                        "context_window": int(self.context_window.currentText()),
                        "max_tokens": self.max_tokens.value()
                    },
                    "permissions": {
                        "file_read": self.allow_file_read.isChecked(),
                        "file_write": self.allow_file_write.isChecked(),
                        "file_delete": self.allow_file_delete.isChecked(),
                        "internet_access": self.allow_internet_access.isChecked(),
                        "financial_transactions": self.allow_financial_transactions.isChecked()
                    }
                }
                
                with open(filepath, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                QMessageBox.information(self, "Success", f"Settings exported to:\n{filepath}")
                logger.info(f"Exported settings to: {filepath}")
            
            except Exception as e:
                logger.error(f"Failed to export settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.daily_limit.setValue(10.0)
            self.weekly_limit.setValue(50.0)
            self.monthly_limit.setValue(200.0)
            self.per_transaction_limit.setValue(50.0)
            self.circuit_breaker_multiplier.setValue(2.0)
            
            self.llm_model.setCurrentText("mistral:7b-instruct")
            self.temperature.setValue(0.7)
            self.top_p.setValue(0.9)
            self.top_k.setValue(40)
            self.context_window.setCurrentText("4096")
            
            self.allow_file_read.setChecked(True)
            self.allow_file_write.setChecked(False)
            self.allow_file_delete.setChecked(False)
            self.allow_internet_access.setChecked(False)
            self.allow_financial_transactions.setChecked(False)
            self.paper_trading_only.setChecked(True)
            
            QMessageBox.information(self, "Success", "Settings reset to defaults!")
            logger.info("Settings reset to defaults")
