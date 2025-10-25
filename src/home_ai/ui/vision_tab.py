"""Vision tab with live screen capture and AI analysis."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QComboBox, QGroupBox, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QFont
from loguru import logger
import numpy as np

from home_ai.vision.screen_capture import get_screen_capture
from home_ai.vision.vision_analysis import get_vision_analyzer


class CaptureWorker(QThread):
    """Worker thread for screen capture."""
    frame_captured = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)
    
    def __init__(self, monitor: int = 1, fps: int = 2):
        super().__init__()
        self.monitor = monitor
        self.fps = fps
        self.running = False
        self.capture = None
    
    def run(self):
        """Run capture loop."""
        try:
            self.capture = get_screen_capture(self.monitor)
            self.running = True
            
            import time
            frame_delay = 1.0 / self.fps
            
            while self.running:
                frame = self.capture.capture_frame()
                if frame is not None:
                    self.frame_captured.emit(frame)
                
                time.sleep(frame_delay)
        
        except Exception as e:
            logger.error(f"Capture worker error: {e}")
            self.error.emit(str(e))
    
    def stop(self):
        """Stop capture loop."""
        self.running = False


class AnalysisWorker(QThread):
    """Worker thread for vision analysis."""
    analysis_complete = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, frame: np.ndarray, prompt: str = "Describe what you see"):
        super().__init__()
        self.frame = frame
        self.prompt = prompt
    
    def run(self):
        """Run analysis."""
        try:
            analyzer = get_vision_analyzer()
            result = analyzer.analyze_frame(self.frame, self.prompt)
            self.analysis_complete.emit(result)
        
        except Exception as e:
            logger.error(f"Analysis worker error: {e}")
            self.error.emit(str(e))


class VisionTab(QWidget):
    """
    Vision tab with live screen capture and AI analysis.
    
    Features:
    - Live screen capture display
    - AI analysis with annotations
    - Monitor selection
    - FPS control
    - Start/pause controls
    """
    
    def __init__(self):
        super().__init__()
        
        self.capture_worker = None
        self.analysis_worker = None
        self.current_frame = None
        self.last_analysis = None
        
        self.init_ui()
        
        logger.info("VisionTab initialized")
    
    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        controls_group = QGroupBox("Vision Controls")
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start Capture")
        self.start_button.clicked.connect(self.toggle_capture)
        controls_layout.addWidget(self.start_button)
        
        self.analyze_button = QPushButton("🔍 Analyze Now")
        self.analyze_button.clicked.connect(self.analyze_current_frame)
        self.analyze_button.setEnabled(False)
        controls_layout.addWidget(self.analyze_button)
        
        controls_layout.addWidget(QLabel("Monitor:"))
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItems(["Primary (1)", "All Monitors (0)"])
        self.monitor_combo.currentIndexChanged.connect(self.on_monitor_changed)
        controls_layout.addWidget(self.monitor_combo)
        
        controls_layout.addWidget(QLabel("FPS:"))
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setMinimum(1)
        self.fps_slider.setMaximum(10)
        self.fps_slider.setValue(2)
        self.fps_slider.setMaximumWidth(150)
        self.fps_slider.valueChanged.connect(self.on_fps_changed)
        controls_layout.addWidget(self.fps_slider)
        
        self.fps_label = QLabel("2 FPS")
        controls_layout.addWidget(self.fps_label)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints())
        layout.addWidget(self.view)
        
        self.pixmap_item = None
        
        analysis_group = QGroupBox("AI Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_label = QLabel("No analysis yet. Click 'Analyze Now' to analyze the current frame.")
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setStyleSheet("padding: 10px; background-color: #2d2d2d;")
        analysis_layout.addWidget(self.analysis_label)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        self.status_label = QLabel("Status: Stopped")
        layout.addWidget(self.status_label)
    
    def toggle_capture(self):
        """Toggle capture on/off."""
        if self.capture_worker is None or not self.capture_worker.running:
            self.start_capture()
        else:
            self.stop_capture()
    
    def start_capture(self):
        """Start screen capture."""
        try:
            monitor = 1 if self.monitor_combo.currentIndex() == 0 else 0
            fps = self.fps_slider.value()
            
            self.capture_worker = CaptureWorker(monitor, fps)
            self.capture_worker.frame_captured.connect(self.on_frame_captured)
            self.capture_worker.error.connect(self.on_capture_error)
            self.capture_worker.start()
            
            self.start_button.setText("⏸ Stop Capture")
            self.analyze_button.setEnabled(True)
            self.status_label.setText(f"Status: Capturing at {fps} FPS")
            
            logger.info("Screen capture started")
        
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            self.status_label.setText(f"Status: Error - {e}")
    
    def stop_capture(self):
        """Stop screen capture."""
        if self.capture_worker:
            self.capture_worker.stop()
            self.capture_worker.wait()
            self.capture_worker = None
        
        self.start_button.setText("▶ Start Capture")
        self.analyze_button.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        
        logger.info("Screen capture stopped")
    
    def on_frame_captured(self, frame: np.ndarray):
        """Handle captured frame."""
        try:
            self.current_frame = frame
            
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            pixmap = QPixmap.fromImage(q_image)
            
            view_size = self.view.size()
            scaled_pixmap = pixmap.scaled(
                view_size.width() - 20,
                view_size.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            if self.pixmap_item is None:
                self.pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
                self.scene.addItem(self.pixmap_item)
            else:
                self.pixmap_item.setPixmap(scaled_pixmap)
            
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
        
        except Exception as e:
            logger.error(f"Failed to display frame: {e}")
    
    def on_capture_error(self, error: str):
        """Handle capture error."""
        self.status_label.setText(f"Status: Error - {error}")
        self.stop_capture()
    
    def analyze_current_frame(self):
        """Analyze current frame with AI."""
        if self.current_frame is None:
            self.analysis_label.setText("No frame to analyze. Start capture first.")
            return
        
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_label.setText("Analysis in progress...")
            return
        
        self.analysis_label.setText("Analyzing frame with AI...")
        self.analyze_button.setEnabled(False)
        
        self.analysis_worker = AnalysisWorker(self.current_frame)
        self.analysis_worker.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()
        
        logger.info("Started frame analysis")
    
    def on_analysis_complete(self, result: dict):
        """Handle analysis complete."""
        self.last_analysis = result
        
        if result.get("success"):
            description = result.get("description", "No description")
            self.analysis_label.setText(f"<b>AI Analysis:</b><br>{description}")
            
            annotations = result.get("annotations", [])
            if annotations:
                self.draw_annotations(annotations)
        else:
            error = result.get("error", "Unknown error")
            self.analysis_label.setText(f"<b>Analysis failed:</b> {error}")
        
        self.analyze_button.setEnabled(True)
        logger.info("Analysis complete")
    
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.analysis_label.setText(f"<b>Analysis error:</b> {error}")
        self.analyze_button.setEnabled(True)
    
    def draw_annotations(self, annotations: list):
        """Draw annotation overlays on the scene."""
        for item in self.scene.items():
            if isinstance(item, (QGraphicsRectItem, QGraphicsTextItem)):
                self.scene.removeItem(item)
        
        for annotation in annotations:
            if "bbox" in annotation:
                x, y, w, h = annotation["bbox"]
                rect = QGraphicsRectItem(x, y, w, h)
                rect.setPen(QPen(QColor(0, 255, 0), 2))
                self.scene.addItem(rect)
                
                if "label" in annotation:
                    text = QGraphicsTextItem(annotation["label"])
                    text.setPos(x, y - 20)
                    text.setDefaultTextColor(QColor(0, 255, 0))
                    font = QFont()
                    font.setBold(True)
                    text.setFont(font)
                    self.scene.addItem(text)
    
    def on_monitor_changed(self, index: int):
        """Handle monitor selection change."""
        if self.capture_worker and self.capture_worker.running:
            self.stop_capture()
            QTimer.singleShot(100, self.start_capture)
    
    def on_fps_changed(self, value: int):
        """Handle FPS slider change."""
        self.fps_label.setText(f"{value} FPS")
        
        if self.capture_worker and self.capture_worker.running:
            self.stop_capture()
            QTimer.singleShot(100, self.start_capture)
    
    def closeEvent(self, event):
        """Handle widget close."""
        self.stop_capture()
        event.accept()
