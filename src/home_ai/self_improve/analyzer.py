"""Code analyzer for identifying improvement opportunities."""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from home_ai.llm.ollama_client import get_ollama_client
from home_ai.security.audit_logger import get_audit_logger


@dataclass
class ImprovementProposal:
    """Proposed code improvement."""
    id: str
    timestamp: str
    file_path: str
    description: str
    rationale: str
    risk_level: str  # "low", "medium", "high"
    scope_files: int
    scope_lines: int
    proposed_diff: str
    expected_benefits: List[str]
    validation_status: Optional[str] = None
    approved: bool = False
    applied: bool = False


class CodeAnalyzer:
    """
    Analyzes codebase for improvement opportunities.
    
    Uses LLM to review code and suggest improvements while
    respecting safety constraints.
    """
    
    RESTRICTED_DIRS = [
        "security",
        "safety",
        "policy",
    ]
    
    RESTRICTED_FILES = [
        "policy_engine.py",
        "audit_logger.py",
        "spending_caps.py",
        "rate_limiter.py",
    ]
    
    MAX_FILES_PER_PROPOSAL = 10
    MAX_LINES_PER_PROPOSAL = 500
    
    def __init__(self, src_dir: Path):
        """
        Initialize code analyzer.
        
        Args:
            src_dir: Source directory to analyze
        """
        self.src_dir = src_dir
        self.ollama = get_ollama_client()
        self.audit_logger = get_audit_logger()
        
        logger.info(f"CodeAnalyzer initialized for: {src_dir}")
    
    def is_restricted(self, file_path: Path) -> bool:
        """
        Check if file is in restricted area.
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file is restricted
        """
        for restricted_dir in self.RESTRICTED_DIRS:
            if restricted_dir in file_path.parts:
                return True
        
        if file_path.name in self.RESTRICTED_FILES:
            return True
        
        return False
    
    def get_analyzable_files(self) -> List[Path]:
        """
        Get list of Python files that can be analyzed.
        
        Returns:
            List of file paths
        """
        files = []
        
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            
            if self.is_restricted(py_file):
                logger.debug(f"Skipping restricted file: {py_file}")
                continue
            
            files.append(py_file)
        
        return files
    
    def analyze_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a single file for improvements.
        
        Args:
            file_path: Path to file
        
        Returns:
            Analysis results or None
        """
        try:
            code = file_path.read_text()
            
            try:
                tree = ast.parse(code)
                complexity = self._calculate_complexity(tree)
            except SyntaxError:
                logger.warning(f"Syntax error in {file_path}, skipping")
                return None
            
            prompt = f"""Analyze this Python code for potential improvements.
Focus on:
1. Code quality and readability
2. Performance optimizations
3. Bug risks or error handling gaps
4. Documentation improvements
5. Best practices

File: {file_path.name}
Lines: {len(code.splitlines())}

Code:
```python
{code}
```

Provide a brief analysis with specific, actionable suggestions.
Format: [CATEGORY] Description of improvement"""
            
            response = self.ollama.generate(
                model="mistral:7b-instruct",
                prompt=prompt,
                stream=False
            )
            
            analysis = response.get("response", "")
            
            return {
                "file_path": str(file_path),
                "lines": len(code.splitlines()),
                "complexity": complexity,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def analyze_codebase(self, max_files: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze multiple files in the codebase.
        
        Args:
            max_files: Maximum number of files to analyze
        
        Returns:
            List of analysis results
        """
        files = self.get_analyzable_files()
        
        files_to_analyze = files[:max_files]
        
        results = []
        for file_path in files_to_analyze:
            logger.info(f"Analyzing: {file_path}")
            result = self.analyze_file(file_path)
            if result:
                results.append(result)
        
        self.audit_logger.log_action(
            action_type="self_improve",
            action="analyze_codebase",
            details={"files_analyzed": len(results)},
            status="success"
        )
        
        return results
    
    def generate_proposal(self, analysis: Dict[str, Any]) -> Optional[ImprovementProposal]:
        """
        Generate improvement proposal from analysis.
        
        Args:
            analysis: Analysis results
        
        Returns:
            ImprovementProposal or None
        """
        try:
            file_path = analysis["file_path"]
            
            proposal_id = f"proposal-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            improvements = self._extract_improvements(analysis["analysis"])
            
            if not improvements:
                return None
            
            risk_level = self._assess_risk(file_path, improvements)
            
            proposal = ImprovementProposal(
                id=proposal_id,
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                description=improvements[0] if improvements else "Code improvements",
                rationale=analysis["analysis"][:500],  # Truncate
                risk_level=risk_level,
                scope_files=1,
                scope_lines=analysis["lines"],
                proposed_diff="",  # Will be generated by proposer
                expected_benefits=improvements
            )
            
            return proposal
        
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            return None
    
    def _extract_improvements(self, analysis: str) -> List[str]:
        """Extract improvement suggestions from analysis."""
        improvements = []
        
        for line in analysis.split("\n"):
            line = line.strip()
            if line.startswith("[") and "]" in line:
                improvements.append(line)
        
        return improvements[:5]  # Top 5
    
    def _assess_risk(self, file_path: str, improvements: List[str]) -> str:
        """Assess risk level of proposed changes."""
        if any(restricted in file_path for restricted in ["security", "safety", "financial"]):
            return "high"
        
        if len(improvements) > 3:
            return "medium"
        
        return "low"


def get_code_analyzer(src_dir: Optional[Path] = None) -> CodeAnalyzer:
    """Get or create code analyzer instance."""
    if src_dir is None:
        src_dir = Path(__file__).parent.parent
    
    return CodeAnalyzer(src_dir)
