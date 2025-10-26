"""Linux platform implementation."""

import os
import subprocess
from typing import Optional
import psutil
from loguru import logger


class LinuxPlatform:
    """Linux-specific platform implementation."""
    
    def __init__(self):
        """Initialize Linux platform."""
        self.display = os.environ.get("DISPLAY", ":0")
        self._check_tools()
    
    def _check_tools(self):
        """Check if required tools are available."""
        self.has_wmctrl = self._command_exists("wmctrl")
        self.has_xdotool = self._command_exists("xdotool")
        self.has_xprop = self._command_exists("xprop")
        
        if not self.has_wmctrl:
            logger.warning("wmctrl not found. Window management will be limited.")
        if not self.has_xdotool:
            logger.warning("xdotool not found. Some features will be limited.")
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists."""
        try:
            subprocess.run(
                ["which", command],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_system_info(self) -> dict:
        """Get system information."""
        try:
            with open("/etc/os-release") as f:
                os_info = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"')
            
            uname = os.uname()
            
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            mem = psutil.virtual_memory()
            
            return {
                "platform": "Linux",
                "os_name": os_info.get("NAME", "Linux"),
                "os_version": os_info.get("VERSION", "Unknown"),
                "kernel": uname.release,
                "architecture": uname.machine,
                "hostname": uname.nodename,
                "cpu_count": cpu_count,
                "cpu_count_logical": cpu_count_logical,
                "memory_total": mem.total,
                "memory_available": mem.available,
                "display": self.display,
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"platform": "Linux", "error": str(e)}
    
    def list_processes(self) -> list:
        """List running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    processes.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "username": info["username"],
                        "memory_percent": info["memory_percent"],
                        "cpu_percent": info["cpu_percent"],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return processes
        except Exception as e:
            logger.error(f"Failed to list processes: {e}")
            return []
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            return True
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} does not exist")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied to kill process {pid}")
            return False
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            return False
    
    def list_windows(self) -> list:
        """List open windows using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot list windows")
            return []
        
        try:
            result = subprocess.run(
                ["wmctrl", "-l", "-p"],
                capture_output=True,
                text=True,
                check=True
            )
            
            windows = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    window_id = parts[0]
                    desktop = parts[1]
                    pid = parts[2]
                    hostname = parts[3]
                    title = parts[4]
                    
                    windows.append({
                        "id": window_id,
                        "desktop": desktop,
                        "pid": int(pid),
                        "hostname": hostname,
                        "title": title,
                    })
            
            return windows
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list windows: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return []
    
    def focus_window(self, window_id: str) -> bool:
        """Focus a window using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot focus window")
            return False
        
        try:
            subprocess.run(
                ["wmctrl", "-i", "-a", window_id],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to focus window {window_id}: {e}")
            return False
    
    def resize_window(self, window_id: str, width: int, height: int) -> bool:
        """Resize a window using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot resize window")
            return False
        
        try:
            subprocess.run(
                ["wmctrl", "-i", "-r", window_id, "-e", f"0,-1,-1,{width},{height}"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to resize window {window_id}: {e}")
            return False
    
    def move_window(self, window_id: str, x: int, y: int) -> bool:
        """Move a window using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot move window")
            return False
        
        try:
            subprocess.run(
                ["wmctrl", "-i", "-r", window_id, "-e", f"0,{x},{y},-1,-1"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to move window {window_id}: {e}")
            return False
    
    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window using xdotool."""
        if not self.has_xdotool:
            logger.warning("xdotool not available, cannot minimize window")
            return False
        
        try:
            subprocess.run(
                ["xdotool", "windowminimize", window_id],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to minimize window {window_id}: {e}")
            return False
    
    def maximize_window(self, window_id: str) -> bool:
        """Maximize a window using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot maximize window")
            return False
        
        try:
            subprocess.run(
                ["wmctrl", "-i", "-r", window_id, "-b", "add,maximized_vert,maximized_horz"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to maximize window {window_id}: {e}")
            return False
    
    def close_window(self, window_id: str) -> bool:
        """Close a window using wmctrl."""
        if not self.has_wmctrl:
            logger.warning("wmctrl not available, cannot close window")
            return False
        
        try:
            subprocess.run(
                ["wmctrl", "-i", "-c", window_id],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to close window {window_id}: {e}")
            return False
    
    def get_active_window(self) -> Optional[str]:
        """Get the currently active window ID."""
        if not self.has_xdotool:
            logger.warning("xdotool not available, cannot get active window")
            return None
        
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get active window: {e}")
            return None
    
    def get_window_geometry(self, window_id: str) -> Optional[dict]:
        """Get window geometry using xdotool."""
        if not self.has_xdotool:
            logger.warning("xdotool not available, cannot get window geometry")
            return None
        
        try:
            result = subprocess.run(
                ["xdotool", "getwindowgeometry", window_id],
                capture_output=True,
                text=True,
                check=True
            )
            
            geometry = {}
            for line in result.stdout.split("\n"):
                if "Position:" in line:
                    pos = line.split(":")[1].strip().split(",")
                    geometry["x"] = int(pos[0])
                    geometry["y"] = int(pos[1].split()[0])
                elif "Geometry:" in line:
                    size = line.split(":")[1].strip().split("x")
                    geometry["width"] = int(size[0])
                    geometry["height"] = int(size[1])
            
            return geometry
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get window geometry: {e}")
            return None
    
    def launch_application(self, command: str) -> Optional[int]:
        """Launch an application."""
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return proc.pid
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return None
