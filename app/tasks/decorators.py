from functools import wraps
from typing import Callable, Optional
from datetime import datetime, timedelta

from app.tasks.queue import task_queue
from app.tasks.models import TaskPriority


def background_task(
    name: str = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_attempts: int = 3,
):
    def decorator(func: Callable) -> Callable:
        task_name = name or f"{func.__module__}.{func.__name__}"
        
        task_queue.register_handler(task_name, func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            payload = {
                "args": args,
                "kwargs": kwargs,
            }
            
            return task_queue.enqueue(
                name=task_name,
                payload=payload,
                priority=priority,
                max_attempts=max_attempts,
            )
        
        wrapper.delay = wrapper
        
        def apply_async(
            args: tuple = None,
            kwargs: dict = None,
            priority: TaskPriority = TaskPriority.NORMAL,
            scheduled_at: datetime = None,
        ):
            payload = {
                "args": args or (),
                "kwargs": kwargs or {},
            }
            return task_queue.enqueue(
                name=task_name,
                payload=payload,
                priority=priority,
                scheduled_at=scheduled_at,
                max_attempts=max_attempts,
            )
        
        wrapper.apply_async = apply_async
        wrapper.task_name = task_name
        
        return wrapper
    
    return decorator


def scheduled_task(
    name: str = None,
    interval_seconds: int = None,
    cron: str = None,
):
    def decorator(func: Callable) -> Callable:
        task_name = name or f"{func.__module__}.{func.__name__}"
        
        task_queue.register_handler(task_name, func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            scheduled_at = None
            if interval_seconds:
                scheduled_at = datetime.utcnow() + timedelta(seconds=interval_seconds)
            
            payload = {
                "args": args,
                "kwargs": kwargs,
                "interval_seconds": interval_seconds,
                "cron": cron,
            }
            
            return task_queue.enqueue(
                name=task_name,
                payload=payload,
                scheduled_at=scheduled_at,
            )
        
        wrapper.schedule = wrapper
        wrapper.task_name = task_name
        wrapper.interval_seconds = interval_seconds
        wrapper.cron = cron
        
        return wrapper
    
    return decorator
