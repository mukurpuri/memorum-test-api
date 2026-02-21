import asyncio
import logging
import threading
import time
from typing import Optional
from datetime import datetime

from app.tasks.queue import TaskQueue, task_queue
from app.tasks.models import TaskStatus

logger = logging.getLogger(__name__)


class TaskWorker:
    def __init__(
        self,
        queue: TaskQueue = None,
        poll_interval: float = 1.0,
        max_concurrent: int = 5,
    ):
        self._queue = queue or task_queue
        self._poll_interval = poll_interval
        self._max_concurrent = max_concurrent
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._active_tasks = 0
        self._lock = threading.Lock()
        self._stats = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_processing_time_ms": 0,
        }
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Task worker started")
    
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Task worker stopped")
    
    def _run_loop(self) -> None:
        while self._running:
            try:
                with self._lock:
                    if self._active_tasks >= self._max_concurrent:
                        time.sleep(0.1)
                        continue
                
                task = self._queue.dequeue()
                if task:
                    self._process_task(task)
                else:
                    time.sleep(self._poll_interval)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1.0)
    
    def _process_task(self, task) -> None:
        with self._lock:
            self._active_tasks += 1
        
        start_time = time.time()
        
        try:
            handler = self._queue._handlers.get(task.name)
            if not handler:
                raise ValueError(f"No handler registered for task: {task.name}")
            
            logger.info(f"Processing task {task.id}: {task.name}")
            
            if asyncio.iscoroutinefunction(handler):
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(handler(task.payload))
                finally:
                    loop.close()
            else:
                result = handler(task.payload)
            
            self._queue.complete(task.id, result or {})
            
            with self._lock:
                self._stats["tasks_succeeded"] += 1
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            self._queue.fail(task.id, str(e))
            
            with self._lock:
                self._stats["tasks_failed"] += 1
        
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            
            with self._lock:
                self._active_tasks -= 1
                self._stats["tasks_processed"] += 1
                self._stats["total_processing_time_ms"] += elapsed_ms
    
    def stats(self) -> dict:
        with self._lock:
            avg_time = 0
            if self._stats["tasks_processed"] > 0:
                avg_time = self._stats["total_processing_time_ms"] / self._stats["tasks_processed"]
            
            return {
                "running": self._running,
                "active_tasks": self._active_tasks,
                "max_concurrent": self._max_concurrent,
                "avg_processing_time_ms": round(avg_time, 2),
                **self._stats,
            }
