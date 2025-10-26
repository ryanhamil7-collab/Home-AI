"""D-Bus service implementation for Home AI."""

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from loguru import logger
from typing import Dict, Any

from home_ai.security.audit_logger import get_audit_logger
from home_ai.security.policy_engine import get_policy_engine


class HomeAIDBusService(dbus.service.Object):
    """D-Bus service for Home AI system integration."""
    
    INTERFACE_NAME = "org.homeai.Control"
    OBJECT_PATH = "/org/homeai/Control"
    
    def __init__(self, bus_name):
        """Initialize D-Bus service."""
        super().__init__(bus_name, self.OBJECT_PATH)
        self.audit_logger = get_audit_logger()
        self.policy_engine = get_policy_engine()
        logger.info("Home AI D-Bus service initialized")
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def InstallPackage(self, package_name: str) -> bool:
        """
        Install a package via apt.
        
        Args:
            package_name: Name of package to install
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"D-Bus: InstallPackage requested for {package_name}")
        
        if not self.policy_engine.check_permission("system", "install_package"):
            logger.warning(f"Permission denied to install package: {package_name}")
            self.audit_logger.log_action(
                action_type="system",
                action="install_package",
                status="denied",
                details={"package": package_name, "reason": "policy"}
            )
            return False
        
        try:
            import subprocess
            
            self.audit_logger.log_action(
                action_type="system",
                action="install_package",
                status="started",
                details={"package": package_name}
            )
            
            result = subprocess.run(
                ["apt", "install", "-y", package_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.audit_logger.log_action(
                action_type="system",
                action="install_package",
                status="completed",
                details={"package": package_name}
            )
            
            logger.info(f"Package {package_name} installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install package {package_name}: {e}")
            self.audit_logger.log_action(
                action_type="system",
                action="install_package",
                status="failed",
                details={"package": package_name, "error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False
    
    @dbus.service.method(INTERFACE_NAME, in_signature='', out_signature='b')
    def UpdateSystem(self) -> bool:
        """
        Update the system via apt.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("D-Bus: UpdateSystem requested")
        
        if not self.policy_engine.check_permission("system", "update_system"):
            logger.warning("Permission denied to update system")
            self.audit_logger.log_action(
                action_type="system",
                action="update_system",
                status="denied",
                details={"reason": "policy"}
            )
            return False
        
        try:
            import subprocess
            
            self.audit_logger.log_action(
                action_type="system",
                action="update_system",
                status="started",
                details={}
            )
            
            subprocess.run(
                ["apt", "update"],
                capture_output=True,
                check=True
            )
            
            subprocess.run(
                ["apt", "upgrade", "-y"],
                capture_output=True,
                check=True
            )
            
            self.audit_logger.log_action(
                action_type="system",
                action="update_system",
                status="completed",
                details={}
            )
            
            logger.info("System updated successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update system: {e}")
            self.audit_logger.log_action(
                action_type="system",
                action="update_system",
                status="failed",
                details={"error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(f"Error updating system: {e}")
            return False
    
    @dbus.service.method(INTERFACE_NAME, in_signature='s', out_signature='b')
    def RestartService(self, service_name: str) -> bool:
        """
        Restart a systemd service.
        
        Args:
            service_name: Name of service to restart
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"D-Bus: RestartService requested for {service_name}")
        
        if not self.policy_engine.check_permission("system", "restart_service"):
            logger.warning(f"Permission denied to restart service: {service_name}")
            self.audit_logger.log_action(
                action_type="system",
                action="restart_service",
                status="denied",
                details={"service": service_name, "reason": "policy"}
            )
            return False
        
        try:
            import subprocess
            
            self.audit_logger.log_action(
                action_type="system",
                action="restart_service",
                status="started",
                details={"service": service_name}
            )
            
            subprocess.run(
                ["systemctl", "restart", service_name],
                capture_output=True,
                check=True
            )
            
            self.audit_logger.log_action(
                action_type="system",
                action="restart_service",
                status="completed",
                details={"service": service_name}
            )
            
            logger.info(f"Service {service_name} restarted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            self.audit_logger.log_action(
                action_type="system",
                action="restart_service",
                status="failed",
                details={"service": service_name, "error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False
    
    @dbus.service.method(INTERFACE_NAME, in_signature='', out_signature='a{sv}')
    def GetSystemInfo(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dictionary of system information
        """
        logger.info("D-Bus: GetSystemInfo requested")
        
        try:
            from home_ai.platform import get_platform
            platform = get_platform()
            info = platform.get_system_info()
            
            dbus_info = {}
            for key, value in info.items():
                if isinstance(value, (str, int, float, bool)):
                    dbus_info[key] = value
                else:
                    dbus_info[key] = str(value)
            
            return dbus_info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    @dbus.service.method(INTERFACE_NAME, in_signature='sas', out_signature='a{sv}')
    def ExecuteCommand(self, command: str, args: list) -> Dict[str, Any]:
        """
        Execute a system command.
        
        Args:
            command: Command to execute
            args: Command arguments
            
        Returns:
            Dictionary with result
        """
        logger.info(f"D-Bus: ExecuteCommand requested: {command} {args}")
        
        if not self.policy_engine.check_permission("system", "execute_command"):
            logger.warning(f"Permission denied to execute command: {command}")
            self.audit_logger.log_action(
                action_type="system",
                action="execute_command",
                status="denied",
                details={"command": command, "args": args, "reason": "policy"}
            )
            return {"success": False, "error": "Permission denied"}
        
        try:
            import subprocess
            
            self.audit_logger.log_action(
                action_type="system",
                action="execute_command",
                status="started",
                details={"command": command, "args": args}
            )
            
            result = subprocess.run(
                [command] + list(args),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.audit_logger.log_action(
                action_type="system",
                action="execute_command",
                status="completed",
                details={
                    "command": command,
                    "args": args,
                    "return_code": result.returncode
                }
            )
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}
    
    @dbus.service.signal(INTERFACE_NAME, signature='ss')
    def SystemUpdateAvailable(self, version: str, description: str):
        """Signal that a system update is available."""
        logger.info(f"Emitting SystemUpdateAvailable signal: {version}")
    
    @dbus.service.signal(INTERFACE_NAME, signature='ss')
    def SecurityAlert(self, level: str, message: str):
        """Signal a security alert."""
        logger.warning(f"Emitting SecurityAlert signal: {level} - {message}")
    
    @dbus.service.signal(INTERFACE_NAME, signature='sa{sv}')
    def TaskCompleted(self, task_id: str, result: Dict[str, Any]):
        """Signal that a task has completed."""
        logger.info(f"Emitting TaskCompleted signal: {task_id}")


def main():
    """Main entry point for D-Bus service."""
    logger.info("Starting Home AI D-Bus service")
    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    bus = dbus.SystemBus()
    
    bus_name = dbus.service.BusName(
        HomeAIDBusService.INTERFACE_NAME,
        bus
    )
    
    service = HomeAIDBusService(bus_name)
    
    logger.info("Home AI D-Bus service running")
    
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        logger.info("D-Bus service interrupted")
    finally:
        logger.info("D-Bus service stopped")


if __name__ == "__main__":
    main()
