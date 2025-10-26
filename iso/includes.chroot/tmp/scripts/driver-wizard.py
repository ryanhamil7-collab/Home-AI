#!/usr/bin/env python3
"""GPU Driver Installation Wizard for Home AI OS."""

import sys
import subprocess
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QRadioButton,
    QButtonGroup, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class GPUDetectionThread(QThread):
    """Thread for GPU detection."""
    
    detection_complete = pyqtSignal(dict)
    
    def run(self):
        """Detect GPU hardware."""
        result = {
            "gpu_found": False,
            "gpu_type": "unknown",
            "gpu_info": "",
            "driver_installed": False,
            "driver_info": ""
        }
        
        try:
            lspci_result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            gpu_lines = [
                line for line in lspci_result.stdout.split('\n')
                if 'VGA' in line or '3D' in line
            ]
            
            if gpu_lines:
                result["gpu_found"] = True
                result["gpu_info"] = '\n'.join(gpu_lines)
                
                gpu_text = ' '.join(gpu_lines).upper()
                if 'NVIDIA' in gpu_text or 'GEFORCE' in gpu_text:
                    result["gpu_type"] = "nvidia"
                elif 'AMD' in gpu_text or 'RADEON' in gpu_text:
                    result["gpu_type"] = "amd"
                elif 'INTEL' in gpu_text:
                    result["gpu_type"] = "intel"
            
            if result["gpu_type"] == "nvidia":
                try:
                    nvidia_smi = subprocess.run(
                        ["nvidia-smi"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if nvidia_smi.returncode == 0:
                        result["driver_installed"] = True
                        result["driver_info"] = nvidia_smi.stdout
                except:
                    pass
            
            try:
                glxinfo = subprocess.run(
                    ["glxinfo"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if glxinfo.returncode == 0:
                    for line in glxinfo.stdout.split('\n'):
                        if 'OpenGL renderer' in line:
                            result["driver_info"] += line + '\n'
            except:
                pass
                
        except Exception as e:
            result["gpu_info"] = f"Error detecting GPU: {e}"
        
        self.detection_complete.emit(result)


class DriverInstallThread(QThread):
    """Thread for driver installation."""
    
    progress_update = pyqtSignal(str)
    install_complete = pyqtSignal(bool, str)
    
    def __init__(self, driver_type, secure_boot_disabled=False):
        super().__init__()
        self.driver_type = driver_type
        self.secure_boot_disabled = secure_boot_disabled
    
    def run(self):
        """Install driver."""
        try:
            if self.driver_type == "nvidia":
                self.install_nvidia_driver()
            elif self.driver_type == "amd":
                self.install_amd_driver()
            else:
                self.install_complete.emit(False, "Unknown driver type")
        except Exception as e:
            self.install_complete.emit(False, str(e))
    
    def install_nvidia_driver(self):
        """Install NVIDIA proprietary driver."""
        self.progress_update.emit("Updating package cache...")
        
        result = subprocess.run(
            ["pkcon", "refresh"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            self.install_complete.emit(False, "Failed to update package cache")
            return
        
        self.progress_update.emit("Installing NVIDIA driver...")
        
        result = subprocess.run(
            ["pkcon", "install", "-y", "nvidia-driver-535"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            self.install_complete.emit(False, f"Driver installation failed:\n{result.stderr}")
            return
        
        self.progress_update.emit("Configuring X11...")
        
        try:
            subprocess.run(
                ["nvidia-xconfig"],
                capture_output=True,
                timeout=30
            )
        except:
            pass  # Non-critical
        
        self.progress_update.emit("Installation complete!")
        self.install_complete.emit(True, "NVIDIA driver installed successfully. Reboot required.")
    
    def install_amd_driver(self):
        """Install AMD open-source driver."""
        self.progress_update.emit("Updating package cache...")
        
        result = subprocess.run(
            ["pkcon", "refresh"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            self.install_complete.emit(False, "Failed to update package cache")
            return
        
        self.progress_update.emit("Installing AMD drivers...")
        
        packages = [
            "mesa-vulkan-drivers",
            "libvulkan1",
            "vulkan-tools",
            "mesa-utils"
        ]
        
        for package in packages:
            self.progress_update.emit(f"Installing {package}...")
            result = subprocess.run(
                ["pkcon", "install", "-y", package],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self.install_complete.emit(False, f"Failed to install {package}")
                return
        
        self.progress_update.emit("Installation complete!")
        self.install_complete.emit(True, "AMD drivers installed successfully.")


class WelcomePage(QWizardPage):
    """Welcome page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("GPU Driver Installation Wizard")
        self.setSubTitle("Install graphics drivers for optimal performance")
        
        layout = QVBoxLayout()
        
        welcome = QLabel(
            "This wizard will help you install graphics drivers for your GPU.\n\n"
            "Proper drivers are essential for:\n"
            "• Smooth desktop performance\n"
            "• AI model acceleration (CUDA/ROCm)\n"
            "• Video playback and encoding\n"
            "• Gaming and 3D applications\n\n"
            "Click Next to detect your GPU."
        )
        welcome.setWordWrap(True)
        layout.addWidget(welcome)
        
        layout.addStretch()
        self.setLayout(layout)


class DetectionPage(QWizardPage):
    """GPU detection page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("GPU Detection")
        self.setSubTitle("Detecting graphics hardware...")
        
        self.gpu_data = {}
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Detecting GPU...")
        layout.addWidget(self.status_label)
        
        self.gpu_info = QTextEdit()
        self.gpu_info.setReadOnly(True)
        self.gpu_info.setMaximumHeight(200)
        layout.addWidget(self.gpu_info)
        
        self.driver_info = QTextEdit()
        self.driver_info.setReadOnly(True)
        self.driver_info.setMaximumHeight(100)
        layout.addWidget(QLabel("Current Driver:"))
        layout.addWidget(self.driver_info)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.detection_thread = None
    
    def initializePage(self):
        """Start detection on page load."""
        self.detect_gpu()
    
    def detect_gpu(self):
        """Start GPU detection thread."""
        self.status_label.setText("Detecting GPU...")
        self.gpu_info.setText("Please wait...")
        
        self.detection_thread = GPUDetectionThread()
        self.detection_thread.detection_complete.connect(self.on_detection_complete)
        self.detection_thread.start()
    
    def on_detection_complete(self, result):
        """Handle detection completion."""
        self.gpu_data = result
        
        if result["gpu_found"]:
            self.status_label.setText(f"✓ {result['gpu_type'].upper()} GPU detected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.gpu_info.setText(result["gpu_info"])
            
            if result["driver_installed"]:
                self.driver_info.setText(f"✓ Driver installed\n{result['driver_info']}")
            else:
                self.driver_info.setText("⚠ No driver installed or driver not working")
        else:
            self.status_label.setText("⚠ No GPU detected")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.gpu_info.setText("No discrete GPU found. Using integrated graphics.")
        
        self.wizard().gpu_data = self.gpu_data


class DriverSelectionPage(QWizardPage):
    """Driver selection page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Driver Selection")
        self.setSubTitle("Choose which driver to install")
        
        layout = QVBoxLayout()
        
        self.recommendation = QLabel()
        self.recommendation.setWordWrap(True)
        layout.addWidget(self.recommendation)
        
        layout.addSpacing(20)
        
        self.driver_group = QButtonGroup()
        
        self.nvidia_radio = QRadioButton("Install NVIDIA proprietary driver (nvidia-driver-535)")
        self.nvidia_info = QLabel(
            "  • Best performance for NVIDIA GPUs\n"
            "  • CUDA support for AI acceleration\n"
            "  • May require Secure Boot to be disabled\n"
            "  • Requires reboot after installation"
        )
        self.nvidia_info.setStyleSheet("color: gray; margin-left: 20px;")
        
        self.amd_radio = QRadioButton("Install AMD open-source drivers (Mesa + Vulkan)")
        self.amd_info = QLabel(
            "  • Good performance for AMD GPUs\n"
            "  • Open-source, included in kernel\n"
            "  • ROCm support available separately\n"
            "  • No reboot required"
        )
        self.amd_info.setStyleSheet("color: gray; margin-left: 20px;")
        
        self.opensource_radio = QRadioButton("Use open-source drivers (Mesa)")
        self.opensource_info = QLabel(
            "  • Works with most GPUs\n"
            "  • Already installed\n"
            "  • Good for Intel integrated graphics\n"
            "  • No installation needed"
        )
        self.opensource_info.setStyleSheet("color: gray; margin-left: 20px;")
        
        self.skip_radio = QRadioButton("Skip driver installation")
        self.skip_info = QLabel(
            "  • Keep current configuration\n"
            "  • Install drivers manually later"
        )
        self.skip_info.setStyleSheet("color: gray; margin-left: 20px;")
        
        self.driver_group.addButton(self.nvidia_radio)
        self.driver_group.addButton(self.amd_radio)
        self.driver_group.addButton(self.opensource_radio)
        self.driver_group.addButton(self.skip_radio)
        
        layout.addWidget(self.nvidia_radio)
        layout.addWidget(self.nvidia_info)
        layout.addSpacing(10)
        layout.addWidget(self.amd_radio)
        layout.addWidget(self.amd_info)
        layout.addSpacing(10)
        layout.addWidget(self.opensource_radio)
        layout.addWidget(self.opensource_info)
        layout.addSpacing(10)
        layout.addWidget(self.skip_radio)
        layout.addWidget(self.skip_info)
        
        layout.addSpacing(20)
        self.secure_boot_check = QCheckBox("I have disabled Secure Boot (required for NVIDIA)")
        self.secure_boot_check.setVisible(False)
        layout.addWidget(self.secure_boot_check)
        
        self.nvidia_radio.toggled.connect(self.on_nvidia_selected)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Set recommendations based on detected GPU."""
        gpu_data = self.wizard().gpu_data
        gpu_type = gpu_data.get("gpu_type", "unknown")
        driver_installed = gpu_data.get("driver_installed", False)
        
        if gpu_type == "nvidia":
            self.recommendation.setText(
                "✓ NVIDIA GPU detected\n\n"
                "Recommendation: Install NVIDIA proprietary driver for best performance and CUDA support."
            )
            self.nvidia_radio.setChecked(True)
            self.nvidia_radio.setEnabled(True)
            self.amd_radio.setEnabled(False)
            
            if driver_installed:
                self.recommendation.setText(
                    "✓ NVIDIA GPU detected\n"
                    "✓ NVIDIA driver already installed\n\n"
                    "You can skip installation or reinstall if experiencing issues."
                )
                self.skip_radio.setChecked(True)
        
        elif gpu_type == "amd":
            self.recommendation.setText(
                "✓ AMD GPU detected\n\n"
                "Recommendation: Install AMD open-source drivers (Mesa + Vulkan) for best performance."
            )
            self.amd_radio.setChecked(True)
            self.nvidia_radio.setEnabled(False)
            self.amd_radio.setEnabled(True)
        
        elif gpu_type == "intel":
            self.recommendation.setText(
                "✓ Intel GPU detected\n\n"
                "Intel integrated graphics work well with open-source Mesa drivers (already installed)."
            )
            self.opensource_radio.setChecked(True)
            self.nvidia_radio.setEnabled(False)
            self.amd_radio.setEnabled(False)
        
        else:
            self.recommendation.setText(
                "⚠ Could not detect GPU type\n\n"
                "You can skip installation and configure drivers manually later."
            )
            self.skip_radio.setChecked(True)
            self.nvidia_radio.setEnabled(False)
            self.amd_radio.setEnabled(False)
    
    def on_nvidia_selected(self, checked):
        """Show Secure Boot warning for NVIDIA."""
        self.secure_boot_check.setVisible(checked)
    
    def validatePage(self):
        """Validate selection."""
        if self.nvidia_radio.isChecked() and not self.secure_boot_check.isChecked():
            reply = QMessageBox.question(
                self,
                "Secure Boot Warning",
                "NVIDIA proprietary drivers may not work with Secure Boot enabled.\n\n"
                "Have you disabled Secure Boot in your BIOS/UEFI settings?\n\n"
                "Click Yes to continue anyway, or No to go back.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            return reply == QMessageBox.StandardButton.Yes
        
        return True


class InstallationPage(QWizardPage):
    """Driver installation page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Installing Driver")
        self.setSubTitle("Please wait while the driver is installed...")
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Preparing installation...")
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.install_thread = None
        self.install_success = False
    
    def initializePage(self):
        """Start installation."""
        prev_page = self.wizard().page(self.wizard().currentId() - 1)
        
        if prev_page.skip_radio.isChecked():
            self.status_label.setText("Installation skipped")
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            self.log_text.setText("Driver installation skipped by user.")
            self.install_success = True
            return
        
        if prev_page.opensource_radio.isChecked():
            self.status_label.setText("Using existing drivers")
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
            self.log_text.setText("Open-source Mesa drivers are already installed.")
            self.install_success = True
            return
        
        driver_type = None
        if prev_page.nvidia_radio.isChecked():
            driver_type = "nvidia"
        elif prev_page.amd_radio.isChecked():
            driver_type = "amd"
        
        if driver_type:
            self.start_installation(driver_type)
    
    def start_installation(self, driver_type):
        """Start driver installation thread."""
        self.status_label.setText(f"Installing {driver_type.upper()} driver...")
        self.log_text.append(f"Starting {driver_type} driver installation...\n")
        
        self.install_thread = DriverInstallThread(driver_type)
        self.install_thread.progress_update.connect(self.on_progress_update)
        self.install_thread.install_complete.connect(self.on_install_complete)
        self.install_thread.start()
    
    def on_progress_update(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
        self.log_text.append(message)
    
    def on_install_complete(self, success, message):
        """Handle installation completion."""
        self.install_success = success
        
        if success:
            self.status_label.setText("✓ Installation complete!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.progress.setRange(0, 1)
            self.progress.setValue(1)
        else:
            self.status_label.setText("✗ Installation failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
        
        self.log_text.append(f"\n{message}")
        
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)
    
    def isComplete(self):
        """Page is complete when installation finishes."""
        return self.install_thread is None or not self.install_thread.isRunning()


class CompletionPage(QWizardPage):
    """Completion page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Complete")
        self.setSubTitle("Driver installation finished")
        
        layout = QVBoxLayout()
        
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        font = self.message_label.font()
        font.setPointSize(12)
        self.message_label.setFont(font)
        layout.addWidget(self.message_label)
        
        self.reboot_check = QCheckBox("Reboot now (recommended)")
        self.reboot_check.setChecked(True)
        layout.addWidget(self.reboot_check)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Set completion message."""
        prev_page = self.wizard().page(self.wizard().currentId() - 1)
        
        if prev_page.install_success:
            self.message_label.setText(
                "✓ Driver installation complete!\n\n"
                "Your graphics drivers have been installed successfully.\n\n"
                "A reboot is recommended to ensure drivers are loaded properly."
            )
        else:
            self.message_label.setText(
                "⚠ Driver installation encountered issues.\n\n"
                "You can try installing drivers manually or check the logs for errors.\n\n"
                "The system will continue to use existing drivers."
            )
            self.reboot_check.setVisible(False)


class DriverWizard(QWizard):
    """Main driver installation wizard."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Home AI OS - Driver Installation")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(700, 500)
        
        self.gpu_data = {}
        
        self.addPage(WelcomePage())
        self.addPage(DetectionPage())
        self.addPage(DriverSelectionPage())
        self.addPage(InstallationPage())
        self.addPage(CompletionPage())
    
    def accept(self):
        """Handle wizard completion."""
        completion_page = self.page(self.currentId())
        
        if hasattr(completion_page, 'reboot_check') and completion_page.reboot_check.isChecked():
            reply = QMessageBox.question(
                self,
                "Reboot Now?",
                "Do you want to reboot now?\n\n"
                "Click Yes to reboot immediately, or No to reboot later.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                subprocess.run(["systemctl", "reboot"])
        
        super().accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    wizard = DriverWizard()
    wizard.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
