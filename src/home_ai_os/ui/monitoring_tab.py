"""System monitoring tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from loguru import logger

try:
    from home_ai_os.monitoring.system_monitor import get_system_monitor
except ImportError as e:
    logger.warning(f"Monitoring module not available: {e}")
    get_system_monitor = None


class MonitoringTab(QWidget):
    """System monitoring tab."""
    
    def __init__(self):
        super().__init__()
        
        self.monitor = None
        if get_system_monitor:
            try:
                self.monitor = get_system_monitor()
            except Exception as e:
                logger.error(f"Could not initialize system monitor: {e}")
        
        self.setup_ui()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        header = QLabel("System Monitoring")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)
        
        stats_group = QGroupBox("System Statistics")
        stats_layout = QVBoxLayout()
        
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        cpu_layout.addWidget(self.cpu_bar)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_label)
        stats_layout.addLayout(cpu_layout)
        
        mem_layout = QHBoxLayout()
        mem_layout.addWidget(QLabel("Memory:"))
        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        mem_layout.addWidget(self.mem_bar)
        self.mem_label = QLabel("0%")
        mem_layout.addWidget(self.mem_label)
        stats_layout.addLayout(mem_layout)
        
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("Disk:"))
        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        disk_layout.addWidget(self.disk_bar)
        self.disk_label = QLabel("0%")
        disk_layout.addWidget(self.disk_label)
        stats_layout.addLayout(disk_layout)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        process_group = QGroupBox("Top Processes")
        process_layout = QVBoxLayout()
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Memory %"])
        process_layout.addWidget(self.process_table)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        self.setLayout(layout)
        
        self.update_stats()
    
    def update_stats(self):
        """Update system statistics."""
        if not self.monitor:
            return
        
        try:
            stats = self.monitor.get_stats()
            
            cpu_percent = stats.get("cpu_percent", 0)
            self.cpu_bar.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            mem_percent = stats.get("memory_percent", 0)
            self.mem_bar.setValue(int(mem_percent))
            self.mem_label.setText(f"{mem_percent:.1f}%")
            
            disk_percent = stats.get("disk_percent", 0)
            self.disk_bar.setValue(int(disk_percent))
            self.disk_label.setText(f"{disk_percent:.1f}%")
            
            processes = stats.get("top_processes", [])
            self.process_table.setRowCount(len(processes))
            
            for i, proc in enumerate(processes[:20]):  # Top 20
                self.process_table.setItem(i, 0, QTableWidgetItem(str(proc.get("pid", ""))))
                self.process_table.setItem(i, 1, QTableWidgetItem(proc.get("name", "")))
                self.process_table.setItem(i, 2, QTableWidgetItem(f"{proc.get('cpu_percent', 0):.1f}"))
                self.process_table.setItem(i, 3, QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}"))
            
            self.process_table.resizeColumnsToContents()
        
        except Exception as e:
            logger.error(f"Stats update error: {e}")
