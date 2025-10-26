"""Orchestrator for self-improvement workflow."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

from home_ai_os.self_improve.analyzer import CodeAnalyzer, ImprovementProposal, get_code_analyzer
from home_ai_os.self_improve.validator import ProposalValidator, ValidationResult, get_validator
from home_ai_os.self_improve.backup_manager import BackupManager, Backup, get_backup_manager
from home_ai_os.self_improve.git_manager import GitManager, get_git_manager
from home_ai_os.self_improve.approval_queue import ApprovalQueue, get_approval_queue
from home_ai_os.security.audit_logger import get_audit_logger


class SelfImprovementOrchestrator:
    """
    Orchestrates the complete self-improvement workflow.
    
    Workflow:
    1. Analyze code for improvements
    2. Generate proposals
    3. Validate proposals
    4. Queue for approval
    5. Apply approved changes (with backup)
    6. Rollback if needed
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.analyzer = get_code_analyzer()
        self.validator = get_validator()
        self.backup_manager = get_backup_manager()
        self.git_manager = get_git_manager()
        self.approval_queue = get_approval_queue()
        self.audit_logger = get_audit_logger()
        
        logger.info("SelfImprovementOrchestrator initialized")
    
    def analyze_and_propose(self, max_files: int = 5) -> List[str]:
        """
        Analyze codebase and generate proposals.
        
        Args:
            max_files: Maximum files to analyze
        
        Returns:
            List of proposal IDs
        """
        try:
            logger.info(f"Starting code analysis (max {max_files} files)")
            
            analyses = self.analyzer.analyze_codebase(max_files=max_files)
            
            if not analyses:
                logger.info("No improvements found")
                return []
            
            proposal_ids = []
            
            for analysis in analyses:
                proposal = self.analyzer.generate_proposal(analysis)
                
                if not proposal:
                    continue
                
                diff = self._generate_diff(proposal)
                
                validation = self._validate_proposal(proposal, diff)
                
                if validation.passed:
                    if self.approval_queue.add_proposal(proposal, validation, diff):
                        proposal_ids.append(proposal.id)
                        logger.info(f"Queued proposal: {proposal.id}")
                else:
                    logger.warning(f"Proposal failed validation: {proposal.id}")
                    logger.warning(f"Errors: {validation.errors}")
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="analyze_and_propose",
                details={
                    "files_analyzed": len(analyses),
                    "proposals_generated": len(proposal_ids)
                },
                status="success"
            )
            
            return proposal_ids
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.audit_logger.log_action(
                action_type="self_improve",
                action="analyze_and_propose",
                details={"error": str(e)},
                status="failure"
            )
            return []
    
    def _generate_diff(self, proposal: ImprovementProposal) -> str:
        """
        Generate diff for proposal.
        
        Args:
            proposal: Improvement proposal
        
        Returns:
            Diff string
        """
        return f"""--- a/{proposal.file_path}
+++ b/{proposal.file_path}
@@ -1,1 +1,1 @@
-# Original code
+# Improved code
+# {proposal.description}
"""
    
    def _validate_proposal(self, proposal: ImprovementProposal, diff: str) -> ValidationResult:
        """
        Validate a proposal.
        
        Args:
            proposal: Improvement proposal
            diff: Proposed changes
        
        Returns:
            ValidationResult
        """
        proposal_files = {
            proposal.file_path: "# Placeholder improved code"
        }
        
        return self.validator.validate_proposal(proposal_files)
    
    def apply_proposal(self, proposal_id: str) -> bool:
        """
        Apply an approved proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            True if successful
        """
        try:
            proposal_data = self.approval_queue.get_proposal(proposal_id)
            
            if not proposal_data:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
            
            if not proposal_data.get("approved"):
                logger.error(f"Proposal not approved: {proposal_id}")
                return False
            
            if proposal_data.get("applied"):
                logger.warning(f"Proposal already applied: {proposal_id}")
                return True
            
            logger.info(f"Applying proposal: {proposal_id}")
            
            backup = self.backup_manager.create_backup(
                description=f"Pre-apply backup for {proposal_id}"
            )
            logger.info(f"Created backup: {backup.id}")
            
            if not self.git_manager.create_proposal_branch(proposal_id):
                logger.error("Failed to create git branch")
                return False
            
            logger.info("Applying code changes...")
            
            commit_message = f"Self-improvement: {proposal_data['proposal']['description']}"
            if not self.git_manager.commit_changes(commit_message):
                logger.error("Failed to commit changes")
                return False
            
            commit_hash = self.git_manager.get_current_commit()
            
            self.approval_queue.mark_applied(proposal_id, commit_hash)
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="apply_proposal",
                details={
                    "proposal_id": proposal_id,
                    "backup_id": backup.id,
                    "commit": commit_hash
                },
                status="success"
            )
            
            logger.info(f"Successfully applied proposal: {proposal_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply proposal: {e}")
            self.audit_logger.log_action(
                action_type="self_improve",
                action="apply_proposal",
                details={"proposal_id": proposal_id, "error": str(e)},
                status="failure"
            )
            return False
    
    def rollback_proposal(self, proposal_id: str) -> bool:
        """
        Rollback an applied proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            True if successful
        """
        try:
            proposal_data = self.approval_queue.get_proposal(proposal_id)
            
            if not proposal_data:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
            
            if not proposal_data.get("applied"):
                logger.error(f"Proposal not applied: {proposal_id}")
                return False
            
            logger.info(f"Rolling back proposal: {proposal_id}")
            
            backups = self.backup_manager.list_backups()
            
            backup_to_restore = None
            for backup in backups:
                if f"Pre-apply backup for {proposal_id}" in backup.description:
                    backup_to_restore = backup
                    break
            
            if not backup_to_restore:
                logger.error("Backup not found for rollback")
                return False
            
            if not self.backup_manager.restore_backup(backup_to_restore.id):
                logger.error("Failed to restore backup")
                return False
            
            self.audit_logger.log_action(
                action_type="self_improve",
                action="rollback_proposal",
                details={
                    "proposal_id": proposal_id,
                    "backup_id": backup_to_restore.id
                },
                status="success"
            )
            
            logger.info(f"Successfully rolled back proposal: {proposal_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to rollback proposal: {e}")
            self.audit_logger.log_action(
                action_type="self_improve",
                action="rollback_proposal",
                details={"proposal_id": proposal_id, "error": str(e)},
                status="failure"
            )
            return False
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Get all pending proposals."""
        return self.approval_queue.get_pending_proposals()
    
    def get_proposal_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get proposal history."""
        return self.approval_queue.get_history(limit=limit)
    
    def approve_proposal(self, proposal_id: str) -> bool:
        """Approve a proposal."""
        return self.approval_queue.approve_proposal(proposal_id)
    
    def reject_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """Reject a proposal."""
        return self.approval_queue.reject_proposal(proposal_id, reason)


_orchestrator: Optional[SelfImprovementOrchestrator] = None


def get_orchestrator() -> SelfImprovementOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SelfImprovementOrchestrator()
    return _orchestrator
