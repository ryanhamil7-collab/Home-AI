"""Policy engine for permission checking and action gating."""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from home_ai.core.config import get_settings
from home_ai.security.audit_logger import get_audit_logger


class ActionScope(Enum):
    """Action scope categories."""
    SYSTEM = "system"
    FILE = "file"
    PROCESS = "process"
    NETWORK = "network"
    REGISTRY = "registry"
    HARDWARE = "hardware"
    APPLICATION = "application"
    FINANCIAL = "financial"
    BROWSER = "browser"


class ActionRisk(Enum):
    """Risk level of actions."""
    SAFE = "safe"  # Read-only, no side effects
    LOW = "low"  # Minor modifications, easily reversible
    MEDIUM = "medium"  # Significant modifications, reversible with effort
    HIGH = "high"  # Destructive or financial operations
    CRITICAL = "critical"  # System-level or irreversible operations


@dataclass
class Action:
    """Typed action with explicit scope and parameters."""
    scope: ActionScope
    operation: str
    risk: ActionRisk
    params: Dict[str, Any]
    description: str
    requires_confirmation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scope": self.scope.value,
            "operation": self.operation,
            "risk": self.risk.value,
            "params": self.params,
            "description": self.description,
            "requires_confirmation": self.requires_confirmation
        }


class PolicyEngine:
    """
    Central policy engine that gates all system operations.
    Implements deny-by-default security model.
    """
    
    def __init__(self):
        """Initialize policy engine."""
        self.settings = get_settings()
        self.audit_logger = get_audit_logger()
        self._paused = False  # For emergency killswitch
        logger.info("PolicyEngine initialized with SAFE MODE defaults")
    
    def check_permission(self, action: Action) -> tuple[bool, str]:
        """
        Check if an action is permitted by current policy.
        
        Returns:
            (allowed: bool, reason: str)
        """
        if self._paused:
            return False, "System paused by emergency killswitch"
        
        self.audit_logger.log_action(
            action_type=action.scope.value,
            action=action.operation,
            status="attempted",
            details=action.to_dict()
        )
        
        allowed, reason = self._check_scope_permission(action)
        
        if not allowed:
            self.audit_logger.log_action(
                action_type=action.scope.value,
                action=action.operation,
                status="blocked",
                details={"reason": reason, **action.to_dict()}
            )
        
        return allowed, reason
    
    def _check_scope_permission(self, action: Action) -> tuple[bool, str]:
        """Check permission based on action scope."""
        toggles = self.settings.system_toggles
        
        if action.scope == ActionScope.FILE:
            return self._check_file_permission(action)
        
        elif action.scope == ActionScope.PROCESS:
            if action.operation == "terminate" and not toggles.allow_process_termination:
                return False, "Process termination disabled"
            if action.operation == "create" and not toggles.allow_process_creation:
                return False, "Process creation disabled"
            return True, "Process operation allowed"
        
        elif action.scope == ActionScope.NETWORK:
            if not toggles.allow_internet_access and not toggles.allow_local_network:
                return False, "Network access disabled"
            return True, "Network operation allowed"
        
        elif action.scope == ActionScope.REGISTRY:
            if action.operation == "read" and not toggles.allow_registry_read:
                return False, "Registry read disabled"
            if action.operation in ["write", "delete"] and not toggles.allow_registry_write:
                return False, "Registry write disabled"
            return True, "Registry operation allowed"
        
        elif action.scope == ActionScope.HARDWARE:
            return self._check_hardware_permission(action)
        
        elif action.scope == ActionScope.FINANCIAL:
            return self._check_financial_permission(action)
        
        elif action.scope == ActionScope.SYSTEM:
            return True, "System operation allowed"
        
        elif action.scope == ActionScope.APPLICATION:
            return True, "Application operation allowed"
        
        elif action.scope == ActionScope.BROWSER:
            return True, "Browser operation allowed"
        
        return False, f"Unknown scope: {action.scope}"
    
    def _check_file_permission(self, action: Action) -> tuple[bool, str]:
        """Check file operation permissions."""
        toggles = self.settings.system_toggles
        path = action.params.get("path", "")
        
        if self._is_restricted_path(path):
            return False, f"Path is restricted: {path}"
        
        if action.operation == "read" and not toggles.allow_file_read:
            return False, "File read disabled"
        
        if action.operation in ["write", "create"] and not toggles.allow_file_write:
            return False, "File write disabled"
        
        if action.operation == "delete" and not toggles.allow_file_delete:
            return False, "File delete disabled"
        
        if action.operation == "execute" and not toggles.allow_file_execution:
            return False, "File execution disabled"
        
        if not self._is_whitelisted_path(path):
            return False, f"Path not in whitelist: {path}"
        
        return True, "File operation allowed"
    
    def _check_hardware_permission(self, action: Action) -> tuple[bool, str]:
        """Check hardware access permissions."""
        toggles = self.settings.system_toggles
        device = action.params.get("device", "")
        
        if device == "camera" and not toggles.allow_camera_access:
            return False, "Camera access disabled"
        
        if device == "microphone" and not toggles.allow_microphone_access:
            return False, "Microphone access disabled"
        
        if device == "speaker" and not toggles.allow_speaker_control:
            return False, "Speaker control disabled"
        
        if device == "usb" and not toggles.allow_usb_access:
            return False, "USB access disabled"
        
        if device == "bluetooth" and not toggles.allow_bluetooth_control:
            return False, "Bluetooth control disabled"
        
        return True, "Hardware operation allowed"
    
    def _check_financial_permission(self, action: Action) -> tuple[bool, str]:
        """Check financial operation permissions."""
        fin_toggles = self.settings.financial_toggles
        
        if not fin_toggles.master_financial_toggle:
            return False, "Financial operations disabled (master toggle off)"
        
        if not fin_toggles.paper_trading_only and action.operation in ["transfer", "trade", "buy", "sell"]:
            return False, "Real financial transactions not allowed in v1"
        
        if action.operation in ["transfer", "buy", "sell"] and not fin_toggles.allow_transfers:
            return False, "Financial transfers disabled"
        
        if action.operation == "bill_pay" and not fin_toggles.allow_bill_pay:
            return False, "Bill payment disabled"
        
        amount = action.params.get("amount", 0)
        if amount > fin_toggles.max_single_transaction:
            return False, f"Amount exceeds single transaction limit: ${amount} > ${fin_toggles.max_single_transaction}"
        
        return True, "Financial operation allowed (paper trading)"
    
    def _is_restricted_path(self, path: str) -> bool:
        """Check if path is in restricted list."""
        restricted = self.settings.paths.restricted_paths
        path_lower = path.lower()
        
        for restricted_path in restricted:
            if path_lower.startswith(restricted_path.lower()):
                return True
        
        return False
    
    def _is_whitelisted_path(self, path: str) -> bool:
        """Check if path is in whitelist."""
        whitelisted = self.settings.paths.whitelisted_paths
        
        if not whitelisted:
            return True
        
        path_lower = path.lower()
        for whitelisted_path in whitelisted:
            expanded = whitelisted_path.replace("{username}", "")
            if path_lower.startswith(expanded.lower()):
                return True
        
        return False
    
    def pause_all(self) -> None:
        """Emergency pause - stops all actions (killswitch)."""
        self._paused = True
        self.audit_logger.log_action(
            action_type="system",
            action="emergency_pause",
            status="executed",
            details={"reason": "Emergency killswitch activated"}
        )
        logger.critical("EMERGENCY PAUSE ACTIVATED - All actions blocked")
    
    def resume(self) -> None:
        """Resume operations after pause."""
        self._paused = False
        self.audit_logger.log_action(
            action_type="system",
            action="resume",
            status="executed",
            details={"reason": "System resumed"}
        )
        logger.info("System resumed")
    
    def is_paused(self) -> bool:
        """Check if system is paused."""
        return self._paused


_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get or create global policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
