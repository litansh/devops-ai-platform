"""
Task scheduler for DevOps AI Platform.

This module manages periodic agent execution, task queuing, and scheduling
of various platform operations.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger, LoggerMixin
from core.config import Settings

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    schedule: str  # cron-like schedule or interval
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    next_run: datetime
    last_run: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class TaskScheduler(LoggerMixin):
    """Task scheduler for managing periodic and scheduled tasks."""
    
    def __init__(self, agent_registry, bot_gateway, settings: Settings):
        self.agent_registry = agent_registry
        self.bot_gateway = bot_gateway
        self.settings = settings
        
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.active_tasks = 0
        
        # Task queues by priority
        self.task_queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        
        # Worker tasks
        self.workers: List[asyncio.Task] = []
        
        self.logger.info("TaskScheduler initialized")
    
    async def start(self) -> None:
        """Start the task scheduler."""
        if self.running:
            self.logger.warning("TaskScheduler is already running")
            return
        
        self.running = True
        
        # Start the main scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Start worker tasks
        for i in range(self.settings.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        # Schedule default tasks
        await self._schedule_default_tasks()
        
        self.logger.info(f"✅ TaskScheduler started with {self.settings.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the task scheduler."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel scheduler task
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel worker tasks
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.logger.info("✅ TaskScheduler stopped")
    
    async def schedule_task(
        self,
        name: str,
        func: Callable,
        schedule: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        *args,
        **kwargs
    ) -> str:
        """
        Schedule a new task.
        
        Args:
            name: Task name
            func: Function to execute
            schedule: Cron-like schedule or interval (e.g., "*/5 * * * *" or "300s")
            priority: Task priority
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task_id = f"{name}_{int(time.time())}"
        
        # Parse schedule
        next_run = self._parse_schedule(schedule)
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            schedule=schedule,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            next_run=next_run
        )
        
        self.tasks[task_id] = task
        self.logger.info(f"Scheduled task: {name} (ID: {task_id}) for {next_run}")
        
        return task_id
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        
        self.logger.info(f"Cancelled task: {task.name} (ID: {task_id})")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and information."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "next_run": task.next_run.isoformat(),
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "retry_count": task.retry_count,
            "result": task.result,
            "error": task.error
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check for tasks that need to run
                for task in self.tasks.values():
                    if (task.status == TaskStatus.PENDING and 
                        task.next_run <= current_time):
                        
                        # Add task to appropriate queue
                        await self.task_queues[task.priority].put(task)
                        task.status = TaskStatus.RUNNING
                        self.active_tasks += 1
                
                # Sleep for a short interval
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)
    
    async def _worker_loop(self, worker_name: str) -> None:
        """Worker loop for executing tasks."""
        while self.running:
            try:
                # Get task from highest priority queue
                task = None
                for priority in reversed(list(TaskPriority)):
                    try:
                        task = await asyncio.wait_for(
                            self.task_queues[priority].get(),
                            timeout=1.0
                        )
                        break
                    except asyncio.TimeoutError:
                        continue
                
                if task is None:
                    continue
                
                # Execute task
                await self._execute_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in worker {worker_name}: {e}")
    
    async def _execute_task(self, task: ScheduledTask, worker_name: str) -> None:
        """Execute a single task."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing task: {task.name} (Worker: {worker_name})")
            
            # Execute the task
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.last_run = datetime.utcnow()
            
            # Calculate next run time
            task.next_run = self._parse_schedule(task.schedule)
            
            # Reset retry count on success
            task.retry_count = 0
            
            execution_time = time.time() - start_time
            self.logger.info(f"Task completed: {task.name} in {execution_time:.2f}s")
            
        except Exception as e:
            # Handle task failure
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.FAILED
                self.logger.error(f"Task failed permanently: {task.name} - {e}")
            else:
                # Reschedule for retry
                task.status = TaskStatus.PENDING
                task.next_run = datetime.utcnow() + timedelta(minutes=task.retry_count * 5)
                self.logger.warning(f"Task failed, retrying: {task.name} (attempt {task.retry_count})")
        
        finally:
            self.active_tasks -= 1
    
    def _parse_schedule(self, schedule: str) -> datetime:
        """Parse schedule string and return next run time."""
        current_time = datetime.utcnow()
        
        # Handle interval format (e.g., "300s", "5m", "1h")
        if schedule.endswith(('s', 'm', 'h', 'd')):
            value = int(schedule[:-1])
            unit = schedule[-1]
            
            if unit == 's':
                delta = timedelta(seconds=value)
            elif unit == 'm':
                delta = timedelta(minutes=value)
            elif unit == 'h':
                delta = timedelta(hours=value)
            elif unit == 'd':
                delta = timedelta(days=value)
            
            return current_time + delta
        
        # Handle cron-like format (simplified)
        # Format: "minute hour day month weekday"
        # For now, just add 5 minutes as default
        return current_time + timedelta(minutes=5)
    
    async def _schedule_default_tasks(self) -> None:
        """Schedule default platform tasks."""
        # Schedule agent health checks
        await self.schedule_task(
            "agent_health_check",
            self._agent_health_check,
            "300s",  # Every 5 minutes
            TaskPriority.NORMAL
        )
        
        # Schedule cost monitoring
        await self.schedule_task(
            "cost_monitoring",
            self._cost_monitoring,
            "3600s",  # Every hour
            TaskPriority.LOW
        )
        
        # Schedule infrastructure health check
        await self.schedule_task(
            "infrastructure_health_check",
            self._infrastructure_health_check,
            "600s",  # Every 10 minutes
            TaskPriority.HIGH
        )
        
        self.logger.info("Default tasks scheduled")
    
    async def _agent_health_check(self) -> None:
        """Check health of all agents."""
        try:
            agents = self.agent_registry.list_agents()
            healthy_count = sum(1 for agent in agents if agent.get("status") == "healthy")
            
            if healthy_count < len(agents):
                await self.bot_gateway.send_alert(
                    f"⚠️ Agent Health Alert: {healthy_count}/{len(agents)} agents healthy"
                )
            
            self.logger.info(f"Agent health check: {healthy_count}/{len(agents)} healthy")
            
        except Exception as e:
            self.logger.error(f"Agent health check failed: {e}")
    
    async def _cost_monitoring(self) -> None:
        """Monitor cloud costs."""
        try:
            # This would integrate with AWS Cost Explorer or similar
            # For now, just log the action
            self.logger.info("Cost monitoring check completed")
            
        except Exception as e:
            self.logger.error(f"Cost monitoring failed: {e}")
    
    async def _infrastructure_health_check(self) -> None:
        """Check infrastructure health."""
        try:
            # This would check Kubernetes cluster, databases, etc.
            # For now, just log the action
            self.logger.info("Infrastructure health check completed")
            
        except Exception as e:
            self.logger.error(f"Infrastructure health check failed: {e}")
