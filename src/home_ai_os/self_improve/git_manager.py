"""Git manager for version control of self-improvements."""

import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
from loguru import logger

from home_ai_os.security.audit_logger import get_audit_logger


class GitManager:
    """
    Manages git operations for self-improvement proposals.
    
    Creates branches, commits, and tags for tracking changes.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize git manager.
        
        Args:
            repo_path: Path to git repository
        """
        if repo_path is None:
            repo_path = Path(__file__).parent.parent.parent.parent
        
        self.repo_path = repo_path
        self.audit_logger = get_audit_logger()
        
        if not self._is_git_available():
            logger.warning("Git not available - version control disabled")
        
        logger.info(f"GitManager initialized: {repo_path}")
    
    def _is_git_available(self) -> bool:
        """Check if git is available."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str]:
        """
        Run git command.
        
        Args:
            args: Git command arguments
            check: Raise exception on error
        
        Returns:
            (success, output)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if check and result.returncode != 0:
                logger.error(f"Git command failed: {' '.join(args)}\n{result.stderr}")
                return False, result.stderr
            
            return True, result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return False, str(e)
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch."""
        success, output = self._run_git(["branch", "--show-current"], check=False)
        return output if success else None
    
    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        success, output = self._run_git(["rev-parse", "HEAD"], check=False)
        return output if success else None
    
    def create_proposal_branch(self, proposal_id: str) -> bool:
        """
        Create a new branch for a proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            True if successful
        """
        try:
            branch_name = f"self/{proposal_id}"
            
            success, output = self._run_git(["checkout", "-b", branch_name])
            
            if success:
                self.audit_logger.log_action(
                    action_type="self_improve",
                    action="create_branch",
                    details={"branch": branch_name},
                    status="success"
                )
                logger.info(f"Created proposal branch: {branch_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """
        Commit changes to current branch.
        
        Args:
            message: Commit message
            files: Specific files to commit (None for all)
        
        Returns:
            True if successful
        """
        try:
            if files:
                for file in files:
                    self._run_git(["add", file])
            else:
                self._run_git(["add", "-A"])
            
            success, output = self._run_git(["commit", "-m", message])
            
            if success:
                commit_hash = self.get_current_commit()
                self.audit_logger.log_action(
                    action_type="self_improve",
                    action="commit_changes",
                    details={"commit": commit_hash, "message": message},
                    status="success"
                )
                logger.info(f"Committed changes: {commit_hash}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return False
    
    def create_backup_tag(self, tag_name: Optional[str] = None) -> bool:
        """
        Create a backup tag at current commit.
        
        Args:
            tag_name: Tag name (auto-generated if None)
        
        Returns:
            True if successful
        """
        try:
            if tag_name is None:
                tag_name = f"backup/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            success, output = self._run_git(["tag", tag_name])
            
            if success:
                logger.info(f"Created backup tag: {tag_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to create tag: {e}")
            return False
    
    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout a branch.
        
        Args:
            branch_name: Branch to checkout
        
        Returns:
            True if successful
        """
        try:
            success, output = self._run_git(["checkout", branch_name])
            
            if success:
                logger.info(f"Checked out branch: {branch_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to checkout branch: {e}")
            return False
    
    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """
        Delete a branch.
        
        Args:
            branch_name: Branch to delete
            force: Force delete even if not merged
        
        Returns:
            True if successful
        """
        try:
            flag = "-D" if force else "-d"
            success, output = self._run_git(["branch", flag, branch_name])
            
            if success:
                logger.info(f"Deleted branch: {branch_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete branch: {e}")
            return False
    
    def get_diff(self, file_path: Optional[str] = None) -> str:
        """
        Get diff of changes.
        
        Args:
            file_path: Specific file (None for all)
        
        Returns:
            Diff output
        """
        try:
            args = ["diff"]
            if file_path:
                args.append(file_path)
            
            success, output = self._run_git(args, check=False)
            return output if success else ""
        
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return ""
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            success, output = self._run_git(["status", "--porcelain"], check=False)
            return bool(output.strip()) if success else False
        
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            return False


_git_manager: Optional[GitManager] = None


def get_git_manager() -> GitManager:
    """Get or create git manager instance."""
    global _git_manager
    if _git_manager is None:
        _git_manager = GitManager()
    return _git_manager
