"""Workflow automation engine for task chains and automation."""

import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from loguru import logger

from home_ai_os.security.audit_logger import get_audit_logger
from home_ai_os.security.policy_engine import get_policy_engine, Action, ActionScope, ActionRisk


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Workflow step types."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXECUTE_SCRIPT = "execute_script"
    FILE_OPERATION = "file_operation"
    WINDOW_OPERATION = "window_operation"
    CONDITION = "condition"
    LOOP = "loop"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    step_type: StepType
    params: Dict[str, Any]
    description: str
    timeout: int = 30
    retry_count: int = 0
    on_error: str = "stop"


@dataclass
class Workflow:
    """Workflow definition."""
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: str
    modified_at: str
    tags: List[str]
    enabled: bool = True


@dataclass
class WorkflowExecution:
    """Workflow execution record."""
    workflow_name: str
    execution_id: str
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str]
    current_step: int
    total_steps: int
    error_message: Optional[str]
    results: Dict[str, Any]


class WorkflowEngine:
    """
    Workflow automation engine.
    Executes multi-step automation workflows with error handling.
    """
    
    def __init__(self):
        """Initialize workflow engine."""
        self.audit_logger = get_audit_logger()
        self.policy_engine = get_policy_engine()
        
        self.workflows_dir = Path.home() / ".home_ai" / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_execution: Optional[WorkflowExecution] = None
        self.paused = False
        
        self.step_handlers: Dict[StepType, Callable] = {}
        self._register_default_handlers()
        
        logger.info("WorkflowEngine initialized")
    
    def _register_default_handlers(self):
        """Register default step handlers."""
        self.step_handlers[StepType.WAIT] = self._handle_wait
        self.step_handlers[StepType.SCREENSHOT] = self._handle_screenshot
        self.step_handlers[StepType.CONDITION] = self._handle_condition
    
    def create_workflow(self, name: str, description: str, steps: List[WorkflowStep], 
                       tags: Optional[List[str]] = None) -> Workflow:
        """Create a new workflow."""
        now = datetime.now().isoformat()
        
        workflow = Workflow(
            name=name,
            description=description,
            steps=steps,
            created_at=now,
            modified_at=now,
            tags=tags or [],
            enabled=True
        )
        
        self.save_workflow(workflow)
        
        logger.info(f"Workflow created: {name} with {len(steps)} steps")
        return workflow
    
    def save_workflow(self, workflow: Workflow) -> bool:
        """Save workflow to disk."""
        try:
            filepath = self.workflows_dir / f"{workflow.name}.json"
            
            workflow_dict = {
                "name": workflow.name,
                "description": workflow.description,
                "steps": [
                    {
                        "step_type": step.step_type.value,
                        "params": step.params,
                        "description": step.description,
                        "timeout": step.timeout,
                        "retry_count": step.retry_count,
                        "on_error": step.on_error
                    }
                    for step in workflow.steps
                ],
                "created_at": workflow.created_at,
                "modified_at": workflow.modified_at,
                "tags": workflow.tags,
                "enabled": workflow.enabled
            }
            
            with open(filepath, 'w') as f:
                json.dump(workflow_dict, f, indent=2)
            
            logger.info(f"Workflow saved: {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False
    
    def load_workflow(self, name: str) -> Optional[Workflow]:
        """Load workflow from disk."""
        try:
            filepath = self.workflows_dir / f"{name}.json"
            
            if not filepath.exists():
                logger.warning(f"Workflow not found: {name}")
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            steps = [
                WorkflowStep(
                    step_type=StepType(step["step_type"]),
                    params=step["params"],
                    description=step["description"],
                    timeout=step.get("timeout", 30),
                    retry_count=step.get("retry_count", 0),
                    on_error=step.get("on_error", "stop")
                )
                for step in data["steps"]
            ]
            
            workflow = Workflow(
                name=data["name"],
                description=data["description"],
                steps=steps,
                created_at=data["created_at"],
                modified_at=data["modified_at"],
                tags=data.get("tags", []),
                enabled=data.get("enabled", True)
            )
            
            logger.info(f"Workflow loaded: {name}")
            return workflow
        
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            return None
    
    def list_workflows(self) -> List[str]:
        """List all available workflows."""
        try:
            workflows = [f.stem for f in self.workflows_dir.glob("*.json")]
            return sorted(workflows)
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    def execute_workflow(self, workflow: Workflow) -> WorkflowExecution:
        """Execute a workflow."""
        execution_id = f"{workflow.name}_{int(time.time())}"
        
        execution = WorkflowExecution(
            workflow_name=workflow.name,
            execution_id=execution_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now().isoformat(),
            completed_at=None,
            current_step=0,
            total_steps=len(workflow.steps),
            error_message=None,
            results={}
        )
        
        self.current_execution = execution
        
        self.audit_logger.log_action(
            action_type="workflow",
            action="start",
            status="executed",
            details={"workflow": workflow.name, "execution_id": execution_id}
        )
        
        logger.info(f"Starting workflow execution: {execution_id}")
        
        try:
            for i, step in enumerate(workflow.steps):
                if self.paused:
                    execution.status = WorkflowStatus.PAUSED
                    logger.info("Workflow paused")
                    break
                
                execution.current_step = i + 1
                
                logger.info(f"Executing step {i+1}/{len(workflow.steps)}: {step.description}")
                
                success = self._execute_step(step, execution)
                
                if not success:
                    if step.on_error == "stop":
                        execution.status = WorkflowStatus.FAILED
                        execution.error_message = f"Step {i+1} failed: {step.description}"
                        break
                    elif step.on_error == "retry" and step.retry_count > 0:
                        for retry in range(step.retry_count):
                            logger.info(f"Retrying step {i+1}, attempt {retry+1}")
                            time.sleep(2)
                            success = self._execute_step(step, execution)
                            if success:
                                break
                        
                        if not success and step.on_error == "stop":
                            execution.status = WorkflowStatus.FAILED
                            execution.error_message = f"Step {i+1} failed after retries"
                            break
            
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
            
            execution.completed_at = datetime.now().isoformat()
            
            self.audit_logger.log_action(
                action_type="workflow",
                action="complete",
                status=execution.status.value,
                details={
                    "workflow": workflow.name,
                    "execution_id": execution_id,
                    "steps_completed": execution.current_step
                }
            )
            
            logger.info(f"Workflow execution completed: {execution.status.value}")
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now().isoformat()
            logger.error(f"Workflow execution failed: {e}")
        
        self.current_execution = None
        return execution
    
    def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Execute a single workflow step."""
        try:
            handler = self.step_handlers.get(step.step_type)
            
            if handler:
                result = handler(step, execution)
                return result
            else:
                logger.warning(f"No handler for step type: {step.step_type}")
                return False
        
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return False
    
    def _handle_wait(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Handle wait step."""
        duration = step.params.get("duration", 1.0)
        time.sleep(duration)
        return True
    
    def _handle_screenshot(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Handle screenshot step."""
        try:
            from home_ai_os.vision.screen_capture import get_screen_capture
            
            screen_capture = get_screen_capture()
            frame = screen_capture.capture_frame()
            
            filepath = step.params.get("filepath")
            if filepath:
                frame.save(Path(filepath))
            
            execution.results[f"screenshot_{execution.current_step}"] = str(filepath)
            return True
        
        except Exception as e:
            logger.error(f"Screenshot step failed: {e}")
            return False
    
    def _handle_condition(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Handle conditional step."""
        condition = step.params.get("condition")
        return True
    
    def register_step_handler(self, step_type: StepType, handler: Callable) -> None:
        """Register a custom step handler."""
        self.step_handlers[step_type] = handler
        logger.info(f"Registered handler for step type: {step_type}")
    
    def pause_execution(self) -> bool:
        """Pause current workflow execution."""
        if self.current_execution:
            self.paused = True
            logger.info("Workflow execution paused")
            return True
        return False
    
    def resume_execution(self) -> bool:
        """Resume paused workflow execution."""
        if self.current_execution and self.paused:
            self.paused = False
            logger.info("Workflow execution resumed")
            return True
        return False
    
    def cancel_execution(self) -> bool:
        """Cancel current workflow execution."""
        if self.current_execution:
            self.current_execution.status = WorkflowStatus.CANCELLED
            self.current_execution.completed_at = datetime.now().isoformat()
            logger.info("Workflow execution cancelled")
            return True
        return False
    
    def get_execution_status(self) -> Optional[WorkflowExecution]:
        """Get current execution status."""
        return self.current_execution
    
    def delete_workflow(self, name: str) -> bool:
        """Delete a workflow."""
        try:
            filepath = self.workflows_dir / f"{name}.json"
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Workflow deleted: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False


_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get or create global workflow engine instance."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
