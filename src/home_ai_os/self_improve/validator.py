"""Validator for testing proposed code changes before approval."""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger

from home_ai_os.security.audit_logger import get_audit_logger


@dataclass
class ValidationResult:
    """Results from validating a proposal."""
    passed: bool
    risk_score: float  # 0.0 (safe) to 1.0 (dangerous)
    checks: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class ProposalValidator:
    """
    Validates code proposals before presenting to user.
    
    Runs static checks, tests, and safety analysis to ensure
    proposals are safe and functional.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.audit_logger = get_audit_logger()
        logger.info("ProposalValidator initialized")
    
    def validate_proposal(self, proposal_files: Dict[str, str]) -> ValidationResult:
        """
        Validate a code proposal.
        
        Args:
            proposal_files: Dict of {file_path: new_content}
        
        Returns:
            ValidationResult
        """
        checks = {}
        errors = []
        warnings = []
        
        checks["syntax"] = self._check_syntax(proposal_files, errors)
        checks["imports"] = self._check_imports(proposal_files, errors, warnings)
        checks["security"] = self._check_security(proposal_files, errors, warnings)
        checks["complexity"] = self._check_complexity(proposal_files, warnings)
        
        checks["ruff"] = self._run_ruff(proposal_files, errors, warnings)
        checks["mypy"] = self._run_mypy(proposal_files, warnings)
        checks["tests"] = self._run_tests(errors, warnings)
        
        risk_score = self._calculate_risk_score(checks, errors, warnings)
        
        passed = len(errors) == 0 and risk_score < 0.7
        
        result = ValidationResult(
            passed=passed,
            risk_score=risk_score,
            checks=checks,
            errors=errors,
            warnings=warnings
        )
        
        self.audit_logger.log_action(
            action_type="self_improve",
            action="validate_proposal",
            details={
                "passed": passed,
                "risk_score": risk_score,
                "errors": len(errors),
                "warnings": len(warnings)
            },
            status="success" if passed else "failure"
        )
        
        return result
    
    def _check_syntax(self, proposal_files: Dict[str, str], errors: List[str]) -> bool:
        """Check Python syntax."""
        import ast
        
        all_valid = True
        
        for file_path, content in proposal_files.items():
            if not file_path.endswith(".py"):
                continue
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"Syntax error in {file_path}: {e}")
                all_valid = False
        
        return all_valid
    
    def _check_imports(self, proposal_files: Dict[str, str], errors: List[str], warnings: List[str]) -> bool:
        """Check for dangerous or missing imports."""
        import ast
        
        dangerous_imports = ["os.system", "subprocess.call", "eval", "exec", "__import__"]
        
        all_safe = True
        
        for file_path, content in proposal_files.items():
            if not file_path.endswith(".py"):
                continue
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in ["eval", "exec"]:
                                warnings.append(f"Dangerous function in {file_path}: {node.func.id}")
                    
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if any(danger in alias.name for danger in ["subprocess", "os"]):
                                warnings.append(f"Potentially dangerous import in {file_path}: {alias.name}")
            
            except Exception as e:
                errors.append(f"Failed to analyze imports in {file_path}: {e}")
                all_safe = False
        
        return all_safe
    
    def _check_security(self, proposal_files: Dict[str, str], errors: List[str], warnings: List[str]) -> bool:
        """Check for security issues."""
        
        dangerous_patterns = [
            "password",
            "secret",
            "api_key",
            "token",
            "credential"
        ]
        
        for file_path, content in proposal_files.items():
            content_lower = content.lower()
            
            for pattern in dangerous_patterns:
                if f'{pattern} = "' in content_lower or f"{pattern} = '" in content_lower:
                    warnings.append(f"Possible hardcoded secret in {file_path}: {pattern}")
            
            if "execute(" in content and "%" in content:
                warnings.append(f"Possible SQL injection risk in {file_path}")
            
            if "subprocess" in content and "shell=True" in content:
                warnings.append(f"Command injection risk in {file_path}: shell=True")
        
        return True
    
    def _check_complexity(self, proposal_files: Dict[str, str], warnings: List[str]) -> bool:
        """Check code complexity."""
        import ast
        
        for file_path, content in proposal_files.items():
            if not file_path.endswith(".py"):
                continue
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_complexity(node)
                        
                        if complexity > 10:
                            warnings.append(
                                f"High complexity in {file_path}::{node.name} (complexity={complexity})"
                            )
            
            except Exception:
                pass
        
        return True
    
    def _calculate_complexity(self, node: Any) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _run_ruff(self, proposal_files: Dict[str, str], errors: List[str], warnings: List[str]) -> bool:
        """Run ruff linter."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                
                for file_path, content in proposal_files.items():
                    if not file_path.endswith(".py"):
                        continue
                    
                    temp_file = tmppath / Path(file_path).name
                    temp_file.write_text(content)
                
                result = subprocess.run(
                    ["ruff", "check", str(tmppath)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            warnings.append(f"Ruff: {line}")
                
                return result.returncode == 0
        
        except FileNotFoundError:
            logger.debug("Ruff not available")
            return True
        except Exception as e:
            logger.warning(f"Ruff check failed: {e}")
            return True
    
    def _run_mypy(self, proposal_files: Dict[str, str], warnings: List[str]) -> bool:
        """Run mypy type checker."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                
                for file_path, content in proposal_files.items():
                    if not file_path.endswith(".py"):
                        continue
                    
                    temp_file = tmppath / Path(file_path).name
                    temp_file.write_text(content)
                
                result = subprocess.run(
                    ["mypy", str(tmppath), "--ignore-missing-imports"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    for line in result.stdout.split("\n"):
                        if "error:" in line:
                            warnings.append(f"Mypy: {line}")
                
                return result.returncode == 0
        
        except FileNotFoundError:
            logger.debug("Mypy not available")
            return True
        except Exception as e:
            logger.warning(f"Mypy check failed: {e}")
            return True
    
    def _run_tests(self, errors: List[str], warnings: List[str]) -> bool:
        """Run unit tests."""
        try:
            result = subprocess.run(
                ["pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            if result.returncode != 0:
                warnings.append(f"Tests failed: {result.returncode} failures")
                return False
            
            return True
        
        except FileNotFoundError:
            logger.debug("Pytest not available")
            return True
        except Exception as e:
            logger.warning(f"Test run failed: {e}")
            return True
    
    def _calculate_risk_score(self, checks: Dict[str, Any], errors: List[str], warnings: List[str]) -> float:
        """
        Calculate risk score from validation results.
        
        Returns:
            Risk score from 0.0 (safe) to 1.0 (dangerous)
        """
        risk = 0.0
        
        risk += len(errors) * 0.2
        
        risk += len(warnings) * 0.05
        
        if not checks.get("syntax", True):
            risk += 0.3
        
        if not checks.get("security", True):
            risk += 0.2
        
        if not checks.get("tests", True):
            risk += 0.1
        
        return min(risk, 1.0)


_validator: Optional[ProposalValidator] = None


def get_validator() -> ProposalValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = ProposalValidator()
    return _validator
