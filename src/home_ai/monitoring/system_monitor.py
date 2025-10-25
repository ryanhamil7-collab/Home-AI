"""System monitoring for CPU, memory, disk, network, and processes."""

import psutil
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger
import threading


@dataclass
class SystemStats:
    """System statistics snapshot."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProcessInfo:
    """Process information."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    username: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SystemMonitor:
    """
    Read-only system monitoring.
    Tracks CPU, memory, disk, network, and processes.
    """
    
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize system monitor.
        
        Args:
            update_interval: Update interval in seconds
        """
        self.update_interval = update_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_stats: Optional[SystemStats] = None
        self._stats_history: List[SystemStats] = []
        self._max_history = 3600  # Keep 1 hour of history at 1s intervals
        
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()
        
        logger.info("SystemMonitor initialized")
    
    def get_current_stats(self) -> SystemStats:
        """
        Get current system statistics.
        
        Returns:
            SystemStats object
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        net_io = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self._last_net_time
        
        if time_delta > 0:
            sent_delta = net_io.bytes_sent - self._last_net_io.bytes_sent
            recv_delta = net_io.bytes_recv - self._last_net_io.bytes_recv
            network_sent_mb = (sent_delta / time_delta) / (1024 ** 2)
            network_recv_mb = (recv_delta / time_delta) / (1024 ** 2)
        else:
            network_sent_mb = 0.0
            network_recv_mb = 0.0
        
        self._last_net_io = net_io
        self._last_net_time = current_time
        
        process_count = len(psutil.pids())
        
        stats = SystemStats(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=disk_percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            network_sent_mb=round(network_sent_mb, 2),
            network_recv_mb=round(network_recv_mb, 2),
            process_count=process_count
        )
        
        return stats
    
    def get_process_list(self, sort_by: str = "cpu", limit: int = 20) -> List[ProcessInfo]:
        """
        Get list of running processes.
        
        Args:
            sort_by: Sort by "cpu", "memory", or "name"
            limit: Maximum number of processes to return
        
        Returns:
            List of ProcessInfo objects
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'username']):
            try:
                info = proc.info
                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_percent=info['memory_percent'] or 0.0,
                    memory_mb=round((info['memory_info'].rss / (1024 ** 2)), 2) if info['memory_info'] else 0.0,
                    status=info['status'],
                    username=info['username'] or "unknown"
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if sort_by == "cpu":
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda p: p.memory_percent, reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda p: p.name.lower())
        
        return processes[:limit]
    
    def get_disk_usage(self) -> Dict[str, Dict[str, Any]]:
        """
        Get disk usage for all partitions.
        
        Returns:
            Dictionary of partition info
        """
        disk_info = {}
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.device] = {
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent
                }
            except PermissionError:
                continue
        
        return disk_info
    
    def get_network_connections(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get active network connections.
        
        Args:
            limit: Maximum number of connections to return
        
        Returns:
            List of connection info
        """
        connections = []
        
        for conn in psutil.net_connections(kind='inet')[:limit]:
            try:
                connections.append({
                    "fd": conn.fd,
                    "family": str(conn.family),
                    "type": str(conn.type),
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    "status": conn.status,
                    "pid": conn.pid
                })
            except Exception:
                continue
        
        return connections
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """
        Get CPU information.
        
        Returns:
            CPU info dictionary
        """
        cpu_freq = psutil.cpu_freq()
        
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else 0,
            "min_freq_mhz": round(cpu_freq.min, 2) if cpu_freq else 0,
            "max_freq_mhz": round(cpu_freq.max, 2) if cpu_freq else 0,
            "per_cpu_percent": psutil.cpu_percent(interval=0.1, percpu=True)
        }
    
    def start_monitoring(self) -> None:
        """Start continuous monitoring in background thread."""
        if self._running:
            logger.warning("Monitoring already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                stats = self.get_current_stats()
                self._current_stats = stats
                
                self._stats_history.append(stats)
                if len(self._stats_history) > self._max_history:
                    self._stats_history.pop(0)
                
                self._check_thresholds(stats)
                
                time.sleep(self.update_interval)
            
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.update_interval)
    
    def _check_thresholds(self, stats: SystemStats) -> None:
        """Check if stats exceed alert thresholds."""
        from home_ai.core.config import get_settings
        settings = get_settings()
        
        if stats.cpu_percent > 80:
            logger.warning(f"High CPU usage: {stats.cpu_percent}%")
        
        if stats.memory_percent > 90:
            logger.warning(f"High memory usage: {stats.memory_percent}%")
        
        if stats.disk_percent > 95:
            logger.warning(f"High disk usage: {stats.disk_percent}%")
    
    def get_stats_history(self, minutes: int = 5) -> List[SystemStats]:
        """
        Get stats history for the last N minutes.
        
        Args:
            minutes: Number of minutes of history
        
        Returns:
            List of SystemStats
        """
        count = int(minutes * 60 / self.update_interval)
        return self._stats_history[-count:]
    
    def get_latest_stats(self) -> Optional[SystemStats]:
        """Get the most recent stats."""
        return self._current_stats


_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor
