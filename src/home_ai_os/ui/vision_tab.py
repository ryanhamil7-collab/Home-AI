"""Vision tab for live computer vision."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QSlider, QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from loguru import logger
import numpy as np

try:
    from home_ai_os.vision.screen_capture import get_screen_capture
    from home_ai_os.vision.vision_analysis import get_vision_analyzer
except ImportError as e:
    logger.warning(f"Vision modules not available: {e}")
    get_screen_capture = None
    get_vision_analyzer = None


class VisionTab(QWidget):
    """Live computer vision tab."""
    
    def __init__(self):
        super().__init__()
        
        self.screen_capture = None
        self.vision_analyzer = None
        self.capturing = False
        
        self.setup_ui()
        
        if get_screen_capture:
            try:
                self.screen_capture = get_screen_capture()
            except Exception as e:
                logger.error(f"Could not initialize screen capture: {e}")
        
        if get_vision_analyzer:
            try:
                self.vision_analyzer = get_vision_analyzer()
            except Exception as e:
                logger.error(f"Could not initialize vision analyzer: {e}")
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        header = QLabel("Live Computer Vision")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        controls = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start Capture")
        self.start_btn.clicked.connect(self.toggle_capture)
        controls.addWidget(self.start_btn)
        
        self.fps_label = QLabel("FPS:")
        controls.addWidget(self.fps_label)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 10)
        self.fps_spin.setValue(1)
        self.fps_spin.valueChanged.connect(self.update_fps)
        controls.addWidget(self.fps_spin)
        
        controls.addStretch()
        
        self.analyze_btn = QPushButton("🔍 Analyze Current Frame")
        self.analyze_btn.clicked.connect(self.analyze_frame)
        self.analyze_btn.setEnabled(False)
        controls.addWidget(self.analyze_btn)
        
        layout.addLayout(controls)
        
        preview_group = QGroupBox("Screen Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("No capture active")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color: #2a2a3e;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        analysis_group = QGroupBox("Vision Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("Analysis results will appear here...")
        analysis_layout.addWidget(self.analysis_text)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        self.setLayout(layout)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_preview)
    
    def toggle_capture(self):
        """Toggle screen capture."""
        if not self.screen_capture:
            self.analysis_text.append("❌ Screen capture not available")
            return
        
        if self.capturing:
            self.screen_capture.stop_capture()
            self.capturing = False
            self.start_btn.setText("▶️ Start Capture")
            self.analyze_btn.setEnabled(False)
            self.update_timer.stop()
            self.preview_label.setText("Capture stopped")
        else:
            self.screen_capture.start_capture()
            self.capturing = True
            self.start_btn.setText("⏸️ Stop Capture")
            self.analyze_btn.setEnabled(True)
            self.update_timer.start(1000 // self.fps_spin.value())
            self.analysis_text.append("✓ Screen capture started")
    
    def update_fps(self, fps):
        """Update capture FPS."""
        if self.screen_capture:
            self.screen_capture.set_fps(fps)
        
        if self.capturing:
            self.update_timer.setInterval(1000 // fps)
    
    def update_preview(self):
        """Update preview image."""
        if not self.screen_capture or not self.capturing:
            return
        
        frame = self.screen_capture.get_current_frame()
        if frame and frame.image:
            img = frame.image
            img.thumbnail((800, 600))  # Resize for preview
            
            img_rgb = img.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimg = QImage(data, img_rgb.width, img_rgb.height, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
    
    def analyze_frame(self):
        """Analyze current frame with vision LLM."""
        if not self.screen_capture or not self.vision_analyzer:
            self.analysis_text.append("❌ Vision analysis not available")
            return
        
        frame = self.screen_capture.get_current_frame()
        if not frame or not frame.image:
            self.analysis_text.append("❌ No frame to analyze")
            return
        
        self.analysis_text.append("\n🔍 Analyzing frame...")
        self.analyze_btn.setEnabled(False)
        
        try:
            img_array = np.array(frame.image)
            
            result = self.vision_analyzer.analyze_frame(
                img_array,
                prompt="Describe what you see on this screen. Identify UI elements, text, and any notable features."
            )
            
            if result.get("success"):
                self.analysis_text.append(f"\n✓ Analysis complete:")
                self.analysis_text.append(f"{result.get('description', 'No description')}")
            else:
                self.analysis_text.append(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.analysis_text.append(f"\n❌ Error: {e}")
            logger.error(f"Vision analysis error: {e}")
        
        finally:
            self.analyze_btn.setEnabled(True)
