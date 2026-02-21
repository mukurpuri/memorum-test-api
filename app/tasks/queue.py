import uuid
import heapq
import threading
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from collections import defaultdict

from app.tasks.models import Task, TaskStatus, TaskPriority, TaskResult


class TaskQueue:
    def __init__(self, max_size: int = 10000):
        self._queue: List[tuple] = []
        self._tasks: Dict[str, Task] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._stats = {
            "enqueued": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
    
    def register_handler(self, task_name: str, handler: Callable) -> None:
        self._handlers[task_name] = handler
    
    def enqueue(
        self,
        name: str,
        payload: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: datetime = None,
        max_attempts: int = 3,
    ) -> Task:
        with self._lock:
            if len(self._queue) >= self._max_size:
                raise RuntimeError("Task queue is full")
            
            task = Task(
                id=str(uuid.uuid4()),
                name=name,
                payload=payload or {},
                priority=priority,
                scheduled_at=scheduled_at,
                max_attempts=max_attempts,
                created_at=datetime.utcnow(),
            )
            
            self._tasks[task.id] = task
            
            priority_score = -priority.value if isinstance(priority, TaskPriority) else -priority
            scheduled_time = (scheduled_at or datetime.utcnow()).timestamp()
            heapq.heappush(self._queue, (priority_score, scheduled_time, task.id))
            
            self._stats["enqueued"] += 1
            
            return task
    
    def dequeue(self) -> Optional[Task]:
        with self._lock:
            now = datetime.utcnow()
            
            while self._queue:
                priority_score, scheduled_time, task_id = self._queue[0]
                
                task = self._tasks.get(task_id)
                if not task:
                    heapq.heappop(self._queue)
                    continue
                
                if task.status == TaskStatus.CANCELLED:
                    heapq.heappop(self._queue)
                    continue
                
                if task.scheduled_at and task.scheduled_at > now:
                    return None
                
                heapq.heappop(self._queue)
                task.status = TaskStatus.RUNNING
                task.started_at = now
                task.attempts += 1
                
                return task
            
            return None
    
    def complete(self, task_id: str, result: Dict[str, Any] = None) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.utcnow()
                self._stats["completed"] += 1
            return task
    
    def fail(self, task_id: str, error: str) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.error = error
                
                if task.attempts < task.max_attempts:
                    task.status = TaskStatus.RETRYING
                    priority_score = -task.priority if isinstance(task.priority, int) else -task.priority.value
                    heapq.heappush(
                        self._queue,
                        (priority_score, datetime.utcnow().timestamp(), task.id)
                    )
                else:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.utcnow()
                    self._stats["failed"] += 1
            
            return task
    
    def cancel(self, task_id: str) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                self._stats["cancelled"] += 1
            return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    def get_tasks(
        self,
        status: TaskStatus = None,
        name: str = None,
        limit: int = 100,
    ) -> List[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
            
            if status:
                tasks = [t for t in tasks if t.status == status]
            if name:
                tasks = [t for t in tasks if t.name == name]
            
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]
    
    def size(self) -> int:
        with self._lock:
            return len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING])
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            status_counts = defaultdict(int)
            for task in self._tasks.values():
                status_counts[task.status] += 1
            
            return {
                "queue_size": self.size(),
                "total_tasks": len(self._tasks),
                "status_counts": dict(status_counts),
                "handlers_registered": len(self._handlers),
                **self._stats,
            }
    
    def clear(self) -> None:
        with self._lock:
            self._queue.clear()
            self._tasks.clear()


task_queue = TaskQueue()
