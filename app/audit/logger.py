import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque
import threading

from app.audit.events import AuditEvent, AuditEventType

logger = logging.getLogger("audit")


class AuditLogger:
    def __init__(self, max_buffer_size: int = 10000, retention_days: int = 90):
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self._retention_days = retention_days
        self._lock = threading.RLock()
        self._handlers: List[callable] = []
    
    def log(self, event: AuditEvent) -> None:
        with self._lock:
            self._buffer.append(event)
        
        log_data = event.model_dump()
        log_data["timestamp"] = event.timestamp.isoformat()
        logger.info(json.dumps(log_data))
        
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Audit handler error: {e}")
    
    def add_handler(self, handler: callable) -> None:
        self._handlers.append(handler)
    
    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        with self._lock:
            results = []
            for event in reversed(self._buffer):
                if len(results) >= limit:
                    break
                
                if event_type and event.event_type != event_type:
                    continue
                if actor_id and event.actor_id != actor_id:
                    continue
                if resource_type and event.resource_type != resource_type:
                    continue
                if resource_id and event.resource_id != resource_id:
                    continue
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue
                
                results.append(event)
            
            return results
    
    def get_user_activity(self, user_id: str, limit: int = 50) -> List[AuditEvent]:
        return self.query(actor_id=user_id, limit=limit)
    
    def get_resource_history(
        self, resource_type: str, resource_id: str, limit: int = 50
    ) -> List[AuditEvent]:
        return self.query(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
    
    def get_failed_logins(
        self, since: Optional[datetime] = None, limit: int = 100
    ) -> List[AuditEvent]:
        if since is None:
            since = datetime.utcnow() - timedelta(hours=24)
        return self.query(
            event_type=AuditEventType.AUTH_FAILED_LOGIN,
            start_time=since,
            limit=limit
        )
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            event_counts: Dict[str, int] = {}
            for event in self._buffer:
                event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            return {
                "total_events": len(self._buffer),
                "buffer_capacity": self._buffer.maxlen,
                "event_counts": event_counts,
                "retention_days": self._retention_days,
            }
    
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()


audit_logger = AuditLogger()
