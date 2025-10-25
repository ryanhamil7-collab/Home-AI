"""Task scheduler with cron-like syntax for automated workflow execution."""

import threading
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta
from loguru import logger

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
except ImportError:
    BackgroundScheduler = None

from home_ai.workflows.workflow_engine import get_workflow_engine
from home_ai.security.audit_logger import get_audit_logger


class TaskScheduler:
    """
    Task scheduler for automated workflow execution.
    Supports cron-like scheduling and interval-based execution.
    """
    
    def __init__(self):
        """Initialize task scheduler."""
        if BackgroundScheduler is None:
            raise ImportError("APScheduler required: pip install APScheduler")
        
        self.scheduler = BackgroundScheduler()
        self.workflow_engine = get_workflow_engine()
        self.audit_logger = get_audit_logger()
        
        self.scheduled_tasks: Dict[str, Dict] = {}
        
        logger.info("TaskScheduler initialized")
    
    def start(self) -> bool:
        """Start the scheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Task scheduler started")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Task scheduler stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            return False
    
    def schedule_workflow_cron(self, workflow_name: str, cron_expression: str, 
                               task_id: Optional[str] = None) -> Optional[str]:
        """
        Schedule workflow with cron expression.
        
        Args:
            workflow_name: Name of workflow to execute
            cron_expression: Cron expression (e.g., "0 9 * * *" for 9 AM daily)
            task_id: Optional custom task ID
        
        Returns:
            Task ID if successful, None otherwise
        """
        if task_id is None:
            task_id = f"{workflow_name}_cron_{int(datetime.now().timestamp())}"
        
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            
            job = self.scheduler.add_job(
                func=self._execute_scheduled_workflow,
                trigger=trigger,
                args=[workflow_name],
                id=task_id,
                name=f"Workflow: {workflow_name}",
                replace_existing=True
            )
            
            self.scheduled_tasks[task_id] = {
                "workflow_name": workflow_name,
                "type": "cron",
                "expression": cron_expression,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            
            self.audit_logger.log_action(
                action_type="scheduler",
                action="schedule_cron",
                status="executed",
                details={
                    "task_id": task_id,
                    "workflow": workflow_name,
                    "cron": cron_expression
                }
            )
            
            logger.info(f"Scheduled workflow '{workflow_name}' with cron: {cron_expression}")
            return task_id
        
        except Exception as e:
            logger.error(f"Failed to schedule workflow: {e}")
            return None
    
    def schedule_workflow_interval(self, workflow_name: str, interval_seconds: int,
                                   task_id: Optional[str] = None) -> Optional[str]:
        """
        Schedule workflow at regular intervals.
        
        Args:
            workflow_name: Name of workflow to execute
            interval_seconds: Interval in seconds
            task_id: Optional custom task ID
        
        Returns:
            Task ID if successful, None otherwise
        """
        if task_id is None:
            task_id = f"{workflow_name}_interval_{int(datetime.now().timestamp())}"
        
        try:
            trigger = IntervalTrigger(seconds=interval_seconds)
            
            job = self.scheduler.add_job(
                func=self._execute_scheduled_workflow,
                trigger=trigger,
                args=[workflow_name],
                id=task_id,
                name=f"Workflow: {workflow_name}",
                replace_existing=True
            )
            
            self.scheduled_tasks[task_id] = {
                "workflow_name": workflow_name,
                "type": "interval",
                "interval_seconds": interval_seconds,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            
            self.audit_logger.log_action(
                action_type="scheduler",
                action="schedule_interval",
                status="executed",
                details={
                    "task_id": task_id,
                    "workflow": workflow_name,
                    "interval": interval_seconds
                }
            )
            
            logger.info(f"Scheduled workflow '{workflow_name}' every {interval_seconds}s")
            return task_id
        
        except Exception as e:
            logger.error(f"Failed to schedule workflow: {e}")
            return None
    
    def schedule_workflow_once(self, workflow_name: str, run_date: datetime,
                              task_id: Optional[str] = None) -> Optional[str]:
        """
        Schedule workflow to run once at specific time.
        
        Args:
            workflow_name: Name of workflow to execute
            run_date: When to run the workflow
            task_id: Optional custom task ID
        
        Returns:
            Task ID if successful, None otherwise
        """
        if task_id is None:
            task_id = f"{workflow_name}_once_{int(datetime.now().timestamp())}"
        
        try:
            trigger = DateTrigger(run_date=run_date)
            
            job = self.scheduler.add_job(
                func=self._execute_scheduled_workflow,
                trigger=trigger,
                args=[workflow_name],
                id=task_id,
                name=f"Workflow: {workflow_name}",
                replace_existing=True
            )
            
            self.scheduled_tasks[task_id] = {
                "workflow_name": workflow_name,
                "type": "once",
                "run_date": run_date.isoformat(),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            
            self.audit_logger.log_action(
                action_type="scheduler",
                action="schedule_once",
                status="executed",
                details={
                    "task_id": task_id,
                    "workflow": workflow_name,
                    "run_date": run_date.isoformat()
                }
            )
            
            logger.info(f"Scheduled workflow '{workflow_name}' for {run_date}")
            return task_id
        
        except Exception as e:
            logger.error(f"Failed to schedule workflow: {e}")
            return None
    
    def _execute_scheduled_workflow(self, workflow_name: str):
        """Execute a scheduled workflow."""
        try:
            logger.info(f"Executing scheduled workflow: {workflow_name}")
            
            workflow = self.workflow_engine.load_workflow(workflow_name)
            if workflow:
                execution = self.workflow_engine.execute_workflow(workflow)
                
                logger.info(f"Scheduled workflow completed: {execution.status.value}")
            else:
                logger.error(f"Workflow not found: {workflow_name}")
        
        except Exception as e:
            logger.error(f"Scheduled workflow execution failed: {e}")
    
    def unschedule_task(self, task_id: str) -> bool:
        """
        Unschedule a task.
        
        Args:
            task_id: Task ID to unschedule
        
        Returns:
            True if successful
        """
        try:
            self.scheduler.remove_job(task_id)
            
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
            
            self.audit_logger.log_action(
                action_type="scheduler",
                action="unschedule",
                status="executed",
                details={"task_id": task_id}
            )
            
            logger.info(f"Unscheduled task: {task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to unschedule task: {e}")
            return False
    
    def list_scheduled_tasks(self) -> List[Dict]:
        """List all scheduled tasks."""
        tasks = []
        
        for job in self.scheduler.get_jobs():
            task_info = self.scheduled_tasks.get(job.id, {})
            tasks.append({
                "task_id": job.id,
                "workflow_name": task_info.get("workflow_name", "Unknown"),
                "type": task_info.get("type", "Unknown"),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "enabled": True
            })
        
        return tasks
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task."""
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"Paused task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause task: {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"Resumed task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume task: {e}")
            return False
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Get information about a scheduled task."""
        return self.scheduled_tasks.get(task_id)


_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """Get or create global task scheduler instance."""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
        _task_scheduler.start()
    return _task_scheduler
