"""Approval queue for managing self-improvement proposals."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from home_ai.core.config import get_settings
from home_ai.security.audit_logger import get_audit_logger
from home_ai.self_improve.analyzer import ImprovementProposal
from home_ai.self_improve.validator import ValidationResult


class ApprovalQueue:
    """
    Manages queue of improvement proposals awaiting approval.
    
    Stores proposals, validation results, and approval status.
    """
    
    def __init__(self):
        """Initialize approval queue."""
        self.settings = get_settings()
        self.queue_dir = self.settings.config_dir / "self_improve" / "queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_logger = get_audit_logger()
        
        logger.info(f"ApprovalQueue initialized: {self.queue_dir}")
    
    def add_proposal(
        self,
        proposal: ImprovementProposal,
        validation: ValidationResult,
        diff: str
    ) -> bool:
        """
        Add a proposal to the queue.
        
        Args:
            proposal: Improvement proposal
            validation: Validation results
            diff: Git diff of changes
        
        Returns:
            True if successful
        """
        try:
            proposal_file = self.queue_dir / f"{proposal.id}.json"
            
            data = {
                "proposal": {
                    "id": proposal.id,
                    "timestamp": proposal.timestamp,
                    "file_path": proposal.file_path,
                    "description": proposal.description,
                    "rationale": proposal.rationale,
                    "risk_level": proposal.risk_level,
                    "scope_files": proposal.scope_files,
                    "scope_lines": proposal.scope_lines,
                    "expected_benefits": proposal.expected_benefits,
                },
                "validation": {
                    "passed": validation.passed,
                    "risk_score": validation.risk_score,
                    "checks": validation.checks,
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                },
                "diff": diff,
                "status": "pending",
                "approved": False,
                "applied": False,
                "created_at": datetime.now().isoformat(),
            }
            
            proposal_file.write_text(json.dumps(data, indent=2))
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="add_proposal",
                details={
                    "proposal_id": proposal.id,
                    "risk_level": proposal.risk_level,
                    "validation_passed": validation.passed
                },
                status="success"
            )
            
            logger.info(f"Added proposal to queue: {proposal.id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to add proposal: {e}")
            return False
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """
        Get all pending proposals.
        
        Returns:
            List of proposal data
        """
        proposals = []
        
        for proposal_file in sorted(self.queue_dir.glob("*.json")):
            try:
                data = json.loads(proposal_file.read_text())
                
                if data.get("status") == "pending":
                    proposals.append(data)
            
            except Exception as e:
                logger.warning(f"Failed to load proposal {proposal_file}: {e}")
        
        return proposals
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            Proposal data or None
        """
        proposal_file = self.queue_dir / f"{proposal_id}.json"
        
        if not proposal_file.exists():
            return None
        
        try:
            return json.loads(proposal_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load proposal {proposal_id}: {e}")
            return None
    
    def approve_proposal(self, proposal_id: str, approved_by: str = "user") -> bool:
        """
        Approve a proposal.
        
        Args:
            proposal_id: Proposal ID
            approved_by: Who approved it
        
        Returns:
            True if successful
        """
        try:
            proposal_file = self.queue_dir / f"{proposal_id}.json"
            
            if not proposal_file.exists():
                logger.error(f"Proposal not found: {proposal_id}")
                return False
            
            data = json.loads(proposal_file.read_text())
            
            data["status"] = "approved"
            data["approved"] = True
            data["approved_by"] = approved_by
            data["approved_at"] = datetime.now().isoformat()
            
            proposal_file.write_text(json.dumps(data, indent=2))
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="approve_proposal",
                details={"proposal_id": proposal_id, "approved_by": approved_by},
                status="success"
            )
            
            logger.info(f"Approved proposal: {proposal_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to approve proposal: {e}")
            return False
    
    def reject_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """
        Reject a proposal.
        
        Args:
            proposal_id: Proposal ID
            reason: Rejection reason
        
        Returns:
            True if successful
        """
        try:
            proposal_file = self.queue_dir / f"{proposal_id}.json"
            
            if not proposal_file.exists():
                logger.error(f"Proposal not found: {proposal_id}")
                return False
            
            data = json.loads(proposal_file.read_text())
            
            data["status"] = "rejected"
            data["approved"] = False
            data["rejection_reason"] = reason
            data["rejected_at"] = datetime.now().isoformat()
            
            proposal_file.write_text(json.dumps(data, indent=2))
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="reject_proposal",
                details={"proposal_id": proposal_id, "reason": reason},
                status="success"
            )
            
            logger.info(f"Rejected proposal: {proposal_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to reject proposal: {e}")
            return False
    
    def mark_applied(self, proposal_id: str, commit_hash: Optional[str] = None) -> bool:
        """
        Mark a proposal as applied.
        
        Args:
            proposal_id: Proposal ID
            commit_hash: Git commit hash
        
        Returns:
            True if successful
        """
        try:
            proposal_file = self.queue_dir / f"{proposal_id}.json"
            
            if not proposal_file.exists():
                logger.error(f"Proposal not found: {proposal_id}")
                return False
            
            data = json.loads(proposal_file.read_text())
            
            data["status"] = "applied"
            data["applied"] = True
            data["applied_at"] = datetime.now().isoformat()
            
            if commit_hash:
                data["commit_hash"] = commit_hash
            
            proposal_file.write_text(json.dumps(data, indent=2))
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="apply_proposal",
                details={"proposal_id": proposal_id, "commit": commit_hash},
                status="success"
            )
            
            logger.info(f"Marked proposal as applied: {proposal_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to mark proposal as applied: {e}")
            return False
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get proposal history.
        
        Args:
            limit: Maximum number of proposals
        
        Returns:
            List of proposal data
        """
        proposals = []
        
        for proposal_file in sorted(self.queue_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(proposal_file.read_text())
                proposals.append(data)
                
                if len(proposals) >= limit:
                    break
            
            except Exception as e:
                logger.warning(f"Failed to load proposal {proposal_file}: {e}")
        
        return proposals
    
    def cleanup_old_proposals(self, keep_count: int = 100) -> int:
        """
        Clean up old proposals.
        
        Args:
            keep_count: Number of proposals to keep
        
        Returns:
            Number of proposals deleted
        """
        proposals = sorted(self.queue_dir.glob("*.json"), reverse=True)
        
        if len(proposals) <= keep_count:
            return 0
        
        deleted = 0
        for proposal_file in proposals[keep_count:]:
            try:
                proposal_file.unlink()
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {proposal_file}: {e}")
        
        logger.info(f"Cleaned up {deleted} old proposals")
        
        return deleted


_approval_queue: Optional[ApprovalQueue] = None


def get_approval_queue() -> ApprovalQueue:
    """Get or create approval queue instance."""
    global _approval_queue
    if _approval_queue is None:
        _approval_queue = ApprovalQueue()
    return _approval_queue
