"""Backup manager for creating and restoring code snapshots."""

import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger

from home_ai.core.config import get_settings
from home_ai.security.audit_logger import get_audit_logger


@dataclass
class Backup:
    """Backup metadata."""
    id: str
    timestamp: str
    description: str
    git_commit: Optional[str]
    backup_path: Path
    files_count: int
    size_bytes: int
    manifest: Dict[str, Any]


class BackupManager:
    """
    Manages backups before applying code changes.
    
    Creates snapshots of source code, config, and git state
    to enable rollback if changes cause issues.
    """
    
    def __init__(self):
        """Initialize backup manager."""
        self.settings = get_settings()
        self.backup_dir = self.settings.backup_dir / "self_improve"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_logger = get_audit_logger()
        
        logger.info(f"BackupManager initialized: {self.backup_dir}")
    
    def create_backup(self, description: str = "Pre-update backup") -> Backup:
        """
        Create a full backup of the codebase.
        
        Args:
            description: Backup description
        
        Returns:
            Backup metadata
        """
        try:
            backup_id = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            git_commit = self._get_git_commit()
            
            src_dir = Path(__file__).parent.parent
            src_backup = backup_path / "src"
            shutil.copytree(src_dir, src_backup, ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", "*.pyo", ".pytest_cache"
            ))
            
            config_backup = backup_path / "config"
            config_backup.mkdir(exist_ok=True)
            
            settings_file = self.settings.config_dir / "settings.json"
            if settings_file.exists():
                shutil.copy2(settings_file, config_backup / "settings.json")
            
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "git_commit": git_commit,
                "python_version": self._get_python_version(),
                "src_dir": str(src_dir),
                "files_backed_up": self._count_files(src_backup)
            }
            
            manifest_file = backup_path / "manifest.json"
            manifest_file.write_text(json.dumps(manifest, indent=2))
            
            size_bytes = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
            
            backup = Backup(
                id=backup_id,
                timestamp=manifest["timestamp"],
                description=description,
                git_commit=git_commit,
                backup_path=backup_path,
                files_count=manifest["files_backed_up"],
                size_bytes=size_bytes
            )
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="create_backup",
                details={"backup_id": backup_id, "size_mb": size_bytes / 1024 / 1024},
                status="success"
            )
            
            logger.info(f"Backup created: {backup_id} ({size_bytes / 1024 / 1024:.2f} MB)")
            
            return backup
        
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            self.audit_logger.log_action(
                action_type="self_improve",
                action="create_backup",
                details={"error": str(e)},
                status="failure"
            )
            raise
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_id: Backup ID to restore
        
        Returns:
            True if successful
        """
        try:
            backup_path = self.backup_dir / backup_id
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            manifest_file = backup_path / "manifest.json"
            manifest = json.loads(manifest_file.read_text())
            
            src_backup = backup_path / "src"
            src_dir = Path(manifest["src_dir"])
            
            safety_backup = self.create_backup("Pre-restore safety backup")
            
            for item in src_dir.iterdir():
                if item.name != "__pycache__":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            for item in src_backup.iterdir():
                if item.is_dir():
                    shutil.copytree(item, src_dir / item.name)
                else:
                    shutil.copy2(item, src_dir / item.name)
            
            config_backup = backup_path / "config" / "settings.json"
            if config_backup.exists():
                shutil.copy2(config_backup, self.settings.config_dir / "settings.json")
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="restore_backup",
                details={"backup_id": backup_id, "safety_backup": safety_backup.id},
                status="success"
            )
            
            logger.info(f"Backup restored: {backup_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            self.audit_logger.log_action(
                action_type="self_improve",
                action="restore_backup",
                details={"backup_id": backup_id, "error": str(e)},
                status="failure"
            )
            return False
    
    def list_backups(self) -> list[Backup]:
        """
        List all available backups.
        
        Returns:
            List of Backup objects
        """
        backups = []
        
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if not backup_path.is_dir():
                continue
            
            manifest_file = backup_path / "manifest.json"
            if not manifest_file.exists():
                continue
            
            try:
                manifest = json.loads(manifest_file.read_text())
                
                size_bytes = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
                
                backup = Backup(
                    id=manifest["backup_id"],
                    timestamp=manifest["timestamp"],
                    description=manifest["description"],
                    git_commit=manifest.get("git_commit"),
                    backup_path=backup_path,
                    files_count=manifest["files_backed_up"],
                    size_bytes=size_bytes,
                    manifest=manifest
                )
                
                backups.append(backup)
            
            except Exception as e:
                logger.warning(f"Failed to load backup {backup_path}: {e}")
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: Backup ID to delete
        
        Returns:
            True if successful
        """
        try:
            backup_path = self.backup_dir / backup_id
            
            if not backup_path.exists():
                logger.warning(f"Backup not found: {backup_id}")
                return False
            
            shutil.rmtree(backup_path)
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="delete_backup",
                details={"backup_id": backup_id},
                status="success"
            )
            
            logger.info(f"Backup deleted: {backup_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Clean up old backups, keeping only the most recent.
        
        Args:
            keep_count: Number of backups to keep
        
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        deleted = 0
        for backup in backups[keep_count:]:
            if self.delete_backup(backup.id):
                deleted += 1
        
        logger.info(f"Cleaned up {deleted} old backups")
        
        return deleted
    
    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    def _get_python_version(self) -> str:
        """Get Python version."""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _count_files(self, directory: Path) -> int:
        """Count files in directory."""
        return sum(1 for _ in directory.rglob("*") if _.is_file())


_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Get or create backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
