from enum import Enum
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class Task(BaseModel):
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    
    class Config:
        use_enum_values = True
