"""Safe file operations with confirmations and backups."""

import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger

from home_ai.security.policy_engine import (
    get_policy_engine, Action, ActionScope, ActionRisk
)
from home_ai.security.audit_logger import get_audit_logger
from home_ai.core.config import get_settings


class FileOperations:
    """
    Safe file operations with permission checks and backups.
    All destructive operations create backups first.
    """
    
    def __init__(self):
        """Initialize file operations."""
        self.policy_engine = get_policy_engine()
        self.audit_logger = get_audit_logger()
        self.settings = get_settings()
        
        self.backup_dir = Path.home() / ".home_ai" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileOperations initialized, backup dir: {self.backup_dir}")
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is in allowed locations."""
        path_str = str(path.resolve())
        
        for restricted in self.settings.system_toggles.restricted_paths:
            if path_str.startswith(restricted):
                return False
        
        if self.settings.system_toggles.whitelisted_paths:
            for whitelisted in self.settings.system_toggles.whitelisted_paths:
                if path_str.startswith(whitelisted):
                    return True
            return False  # Not in whitelist
        
        return True  # No whitelist, allow if not restricted
    
    def _create_backup(self, filepath: Path) -> Optional[Path]:
        """
        Create backup of file before modification.
        
        Args:
            filepath: File to backup
        
        Returns:
            Path to backup file, or None if failed
        """
        if not filepath.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(filepath, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            return backup_path
        
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read file contents.
        
        Args:
            filepath: Path to file
        
        Returns:
            File contents as string, or None if failed
        """
        path = Path(filepath)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="read",
            risk=ActionRisk.SAFE,
            params={"path": str(path)},
            description=f"Read file: {path.name}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"File read blocked: {reason}")
            return None
        
        if not self._is_path_allowed(path):
            logger.warning(f"Path not allowed: {path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="read",
                status="executed",
                details={"path": str(path), "size": len(content)}
            )
            
            return content
        
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return None
    
    def write_file(self, filepath: str, content: str, create_backup: bool = True) -> bool:
        """
        Write content to file.
        
        Args:
            filepath: Path to file
            content: Content to write
            create_backup: Create backup if file exists
        
        Returns:
            True if successful
        """
        path = Path(filepath)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="write",
            risk=ActionRisk.MEDIUM,
            params={"path": str(path), "size": len(content)},
            description=f"Write file: {path.name}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"File write blocked: {reason}")
            return False
        
        if not self._is_path_allowed(path):
            logger.warning(f"Path not allowed: {path}")
            return False
        
        try:
            if create_backup and path.exists():
                self._create_backup(path)
            
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="write",
                status="executed",
                details={"path": str(path), "size": len(content)}
            )
            
            logger.info(f"File written: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return False
    
    def delete_file(self, filepath: str, create_backup: bool = True) -> bool:
        """
        Delete a file.
        
        Args:
            filepath: Path to file
            create_backup: Create backup before deletion
        
        Returns:
            True if successful
        """
        path = Path(filepath)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="delete",
            risk=ActionRisk.HIGH,
            params={"path": str(path)},
            description=f"Delete file: {path.name}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"File delete blocked: {reason}")
            return False
        
        if not self._is_path_allowed(path):
            logger.warning(f"Path not allowed: {path}")
            return False
        
        try:
            if not path.exists():
                logger.warning(f"File does not exist: {path}")
                return False
            
            if create_backup:
                backup_path = self._create_backup(path)
                if backup_path is None:
                    logger.error("Failed to create backup, aborting delete")
                    return False
            
            path.unlink()
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="delete",
                status="executed",
                details={"path": str(path)}
            )
            
            logger.info(f"File deleted: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy a file.
        
        Args:
            source: Source file path
            destination: Destination file path
        
        Returns:
            True if successful
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="copy",
            risk=ActionRisk.LOW,
            params={"source": str(src_path), "destination": str(dst_path)},
            description=f"Copy file: {src_path.name} to {dst_path.name}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"File copy blocked: {reason}")
            return False
        
        if not self._is_path_allowed(src_path) or not self._is_path_allowed(dst_path):
            logger.warning("Path not allowed")
            return False
        
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dst_path)
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="copy",
                status="executed",
                details={"source": str(src_path), "destination": str(dst_path)}
            )
            
            logger.info(f"File copied: {src_path} -> {dst_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
    
    def move_file(self, source: str, destination: str, create_backup: bool = True) -> bool:
        """
        Move a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            create_backup: Create backup of source
        
        Returns:
            True if successful
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="move",
            risk=ActionRisk.MEDIUM,
            params={"source": str(src_path), "destination": str(dst_path)},
            description=f"Move file: {src_path.name} to {dst_path.name}",
            requires_confirmation=True
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"File move blocked: {reason}")
            return False
        
        if not self._is_path_allowed(src_path) or not self._is_path_allowed(dst_path):
            logger.warning("Path not allowed")
            return False
        
        try:
            if create_backup:
                self._create_backup(src_path)
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="move",
                status="executed",
                details={"source": str(src_path), "destination": str(dst_path)}
            )
            
            logger.info(f"File moved: {src_path} -> {dst_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False
    
    def list_directory(self, dirpath: str) -> Optional[List[str]]:
        """
        List directory contents.
        
        Args:
            dirpath: Directory path
        
        Returns:
            List of file/directory names, or None if failed
        """
        path = Path(dirpath)
        
        if not self._is_path_allowed(path):
            logger.warning(f"Path not allowed: {path}")
            return None
        
        try:
            items = [item.name for item in path.iterdir()]
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="list_directory",
                status="executed",
                details={"path": str(path), "count": len(items)}
            )
            
            return items
        
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            return None
    
    def create_directory(self, dirpath: str) -> bool:
        """
        Create a directory.
        
        Args:
            dirpath: Directory path
        
        Returns:
            True if successful
        """
        path = Path(dirpath)
        
        action = Action(
            scope=ActionScope.FILE,
            operation="create_directory",
            risk=ActionRisk.LOW,
            params={"path": str(path)},
            description=f"Create directory: {path.name}",
            requires_confirmation=False
        )
        
        allowed, reason = self.policy_engine.check_permission(action)
        if not allowed:
            logger.warning(f"Directory creation blocked: {reason}")
            return False
        
        if not self._is_path_allowed(path):
            logger.warning(f"Path not allowed: {path}")
            return False
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            
            self.audit_logger.log_action(
                action_type="file_operation",
                action="create_directory",
                status="executed",
                details={"path": str(path)}
            )
            
            logger.info(f"Directory created: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            return False


_file_operations: Optional[FileOperations] = None


def get_file_operations() -> FileOperations:
    """Get or create global file operations instance."""
    global _file_operations
    if _file_operations is None:
        _file_operations = FileOperations()
    return _file_operations
