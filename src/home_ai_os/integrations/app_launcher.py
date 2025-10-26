"""Application launcher with whitelist and process management."""

import subprocess
import time
from typing import Optional, List, Dict
from pathlib import Path
from loguru import logger

import psutil

from home_ai_os.security.policy_engine import (
    get_policy_engine, Action, ActionScope, ActionRisk
)
from home_ai_os.security.audit_logger import get_audit_logger
from home_ai_os.core.config import get_settings


class ApplicationLauncher:
    """
    Application launcher with whitelist and process management.
    Safely launches and manages applications.
    """
    
    def __init__(self):
        """Initialize application launcher."""
        self.policy_engine = get_policy_engine()
        self.audit_logger = get_audit_logger()
        self.settings = get_settings()
        
        self.whitelist = {
            "chrome": {
                "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "args": [],
                "risk": ActionRisk.LOW
            },
            "firefox": {
                "path": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "args": [],
                "risk": ActionRisk.LOW
            },
            "vscode": {
                "path": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
                "args": [],
                "risk": ActionRisk.LOW
            },
            "notepad": {
                "path": "C:\\Windows\\System32\\notepad.exe",
                "args": [],
                "risk": ActionRisk.SAFE
            },
            "calculator": {
                "path": "C:\\Windows\\System32\\calc.exe",
                "args": [],
                "risk": ActionRisk.SAFE
            },
            "terminal": {
                "path": "C:\\Windows\\System32\\cmd.exe",
                "args": [],
                "risk": ActionRisk.MEDIUM
            },
            "powershell": {
                "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "args": [],
                "risk": ActionRisk.MEDIUM
            }
        }
        
        self.launched_processes: Dict[int, Dict] = {}
        
        logger.info("ApplicationLauncher initialized")
    
    def launch_application(self, app_name: str, args: Optional[List[str]] = None) -> Optional[int]:
        """
        Launch an application.
        
        Args:
            app_name: Application name from whitelist
            args: Optional command-line arguments
        
        Returns:
            Process ID if successful, None otherwise
        """
        if app_name not in self.whitelist:
            logger.warning(f"Application not in whitelist: {app_name}")
            return None
        
        app_config = self.whitelist[app_name]
        
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="launch_application",
            risk=app_config["risk"],
            params={"app": app_name},
            description=f"Launch application: {app_name}",
            requires_confirmation=app_config["risk"] != ActionRisk.SAFE
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Application launch blocked: {reason}")
            return None
        
        try:
            app_path = Path(app_config["path"])
            
            if not app_path.exists():
                logger.error(f"Application not found: {app_path}")
                return None
            
            cmd = [str(app_path)]
            if args:
                cmd.extend(args)
            elif app_config["args"]:
                cmd.extend(app_config["args"])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.launched_processes[process.pid] = {
                "app_name": app_name,
                "pid": process.pid,
                "started_at": time.time(),
                "process": process
            }
            
            self.audit_logger.log_action(
                action_type="application",
                action="launch",
                status="executed",
                details={"app": app_name, "pid": process.pid}
            )
            
            logger.info(f"Launched application: {app_name} (PID: {process.pid})")
            return process.pid
        
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return None
    
    def terminate_application(self, pid: int) -> bool:
        """
        Terminate a launched application.
        
        Args:
            pid: Process ID
        
        Returns:
            True if successful
        """
        action = Action(
            scope=ActionScope.SYSTEM,
            operation="terminate_process",
            risk=ActionRisk.MEDIUM,
            params={"pid": pid},
            description=f"Terminate process: {pid}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Process termination blocked: {reason}")
            return False
        
        try:
            if pid in self.launched_processes:
                process_info = self.launched_processes[pid]
                process = process_info["process"]
                
                process.terminate()
                process.wait(timeout=5)
                
                del self.launched_processes[pid]
                
                self.audit_logger.log_action(
                    action_type="application",
                    action="terminate",
                    status="executed",
                    details={"app": process_info["app_name"], "pid": pid}
                )
                
                logger.info(f"Terminated application: {process_info['app_name']} (PID: {pid})")
                return True
            else:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                
                logger.info(f"Terminated process: {pid}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to terminate process: {e}")
            return False
    
    def is_application_running(self, app_name: str) -> bool:
        """Check if application is running."""
        for proc_info in self.launched_processes.values():
            if proc_info["app_name"] == app_name:
                return True
        return False
    
    def get_launched_applications(self) -> List[Dict]:
        """Get list of launched applications."""
        apps = []
        
        for pid, info in list(self.launched_processes.items()):
            try:
                process = psutil.Process(pid)
                apps.append({
                    "app_name": info["app_name"],
                    "pid": pid,
                    "status": process.status(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "started_at": info["started_at"]
                })
            except psutil.NoSuchProcess:
                del self.launched_processes[pid]
        
        return apps
    
    def add_to_whitelist(self, app_name: str, path: str, risk: ActionRisk = ActionRisk.LOW) -> bool:
        """Add application to whitelist."""
        try:
            self.whitelist[app_name] = {
                "path": path,
                "args": [],
                "risk": risk
            }
            
            logger.info(f"Added to whitelist: {app_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add to whitelist: {e}")
            return False
    
    def remove_from_whitelist(self, app_name: str) -> bool:
        """Remove application from whitelist."""
        if app_name in self.whitelist:
            del self.whitelist[app_name]
            logger.info(f"Removed from whitelist: {app_name}")
            return True
        return False
    
    def get_whitelist(self) -> Dict:
        """Get application whitelist."""
        return self.whitelist.copy()


_app_launcher: Optional[ApplicationLauncher] = None


def get_app_launcher() -> ApplicationLauncher:
    """Get or create global application launcher instance."""
    global _app_launcher
    if _app_launcher is None:
        _app_launcher = ApplicationLauncher()
    return _app_launcher
