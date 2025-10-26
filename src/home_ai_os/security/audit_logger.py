"""Audit logging system with immutable append-only logs."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from loguru import logger
import threading


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    action_type: str
    action: str
    user: str
    status: str  # "attempted", "confirmed", "executed", "failed", "blocked"
    details: Dict[str, Any]
    previous_hash: str
    entry_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Immutable audit logger with hash chain for tamper detection.
    All actions are logged with full context for forensics.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize audit logger."""
        if log_dir is None:
            log_dir = Path.home() / ".home_ai" / "logs" / "audit"
        
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_log_file = self._get_log_file()
        
        self.last_hash = self._get_last_hash()
        
        self._lock = threading.Lock()
        
        logger.info(f"AuditLogger initialized: {self.log_dir}")
    
    def _get_log_file(self) -> Path:
        """Get current log file path (daily rotation)."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    def _get_last_hash(self) -> str:
        """Get the last hash from the current log file."""
        if not self.current_log_file.exists():
            return "0" * 64  # Genesis hash
        
        try:
            with open(self.current_log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("entry_hash", "0" * 64)
        except Exception as e:
            logger.error(f"Failed to read last hash: {e}")
        
        return "0" * 64
    
    def _compute_hash(self, entry_data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of entry data."""
        data_str = json.dumps(entry_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def log_action(
        self,
        action_type: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        user: str = "system"
    ) -> AuditEntry:
        """
        Log an action to the audit trail.
        
        Args:
            action_type: Type of action (e.g., "file", "process", "network", "financial")
            action: Specific action (e.g., "read_file", "terminate_process")
            status: Status of action ("attempted", "confirmed", "executed", "failed", "blocked")
            details: Additional details about the action
            user: User who initiated the action
        
        Returns:
            AuditEntry object
        """
        with self._lock:
            current_file = self._get_log_file()
            if current_file != self.current_log_file:
                self.current_log_file = current_file
                self.last_hash = "0" * 64  # Reset for new file
            
            timestamp = datetime.now().isoformat()
            details = details or {}
            
            details = self._redact_sensitive(details)
            
            entry_data = {
                "timestamp": timestamp,
                "action_type": action_type,
                "action": action,
                "user": user,
                "status": status,
                "details": details,
                "previous_hash": self.last_hash
            }
            
            entry_hash = self._compute_hash(entry_data)
            entry_data["entry_hash"] = entry_hash
            
            entry = AuditEntry(**entry_data)
            
            try:
                with open(self.current_log_file, 'a') as f:
                    f.write(json.dumps(entry.to_dict()) + '\n')
                
                self.last_hash = entry_hash
                
                logger.debug(f"Audit log: {action_type}.{action} - {status}")
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
            
            return entry
    
    def _redact_sensitive(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from details."""
        sensitive_keys = [
            "password", "token", "api_key", "secret", "credential",
            "ssn", "credit_card", "cvv", "pin", "private_key"
        ]
        
        redacted = details.copy()
        for key in redacted:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "[REDACTED]"
        
        return redacted
    
    def verify_chain(self, log_file: Optional[Path] = None) -> bool:
        """
        Verify the integrity of the audit log chain.
        
        Returns:
            True if chain is valid, False if tampered
        """
        if log_file is None:
            log_file = self.current_log_file
        
        if not log_file.exists():
            return True  # Empty log is valid
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            previous_hash = "0" * 64
            for i, line in enumerate(lines):
                entry = json.loads(line)
                
                if entry["previous_hash"] != previous_hash:
                    logger.error(f"Chain broken at entry {i}: previous hash mismatch")
                    return False
                
                entry_data = {k: v for k, v in entry.items() if k != "entry_hash"}
                computed_hash = self._compute_hash(entry_data)
                
                if computed_hash != entry["entry_hash"]:
                    logger.error(f"Chain broken at entry {i}: hash mismatch")
                    return False
                
                previous_hash = entry["entry_hash"]
            
            logger.info(f"Audit log chain verified: {len(lines)} entries")
            return True
        
        except Exception as e:
            logger.error(f"Failed to verify chain: {e}")
            return False
    
    def get_recent_entries(self, count: int = 100) -> List[AuditEntry]:
        """Get recent audit entries."""
        if not self.current_log_file.exists():
            return []
        
        try:
            with open(self.current_log_file, 'r') as f:
                lines = f.readlines()
            
            entries = []
            for line in lines[-count:]:
                entry_dict = json.loads(line)
                entries.append(AuditEntry(**entry_dict))
            
            return entries
        
        except Exception as e:
            logger.error(f"Failed to read entries: {e}")
            return []
    
    def search_entries(
        self,
        action_type: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditEntry]:
        """Search audit entries with filters."""
        if not self.current_log_file.exists():
            return []
        
        try:
            with open(self.current_log_file, 'r') as f:
                lines = f.readlines()
            
            entries = []
            for line in lines:
                entry_dict = json.loads(line)
                entry = AuditEntry(**entry_dict)
                
                if action_type and entry.action_type != action_type:
                    continue
                if action and entry.action != action:
                    continue
                if status and entry.status != status:
                    continue
                
                entry_time = datetime.fromisoformat(entry.timestamp)
                if start_time and entry_time < start_time:
                    continue
                if end_time and entry_time > end_time:
                    continue
                
                entries.append(entry)
            
            return entries
        
        except Exception as e:
            logger.error(f"Failed to search entries: {e}")
            return []


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
