from functools import wraps
from typing import Callable, Optional
import asyncio

from app.audit.logger import audit_logger
from app.audit.events import AuditEventType, AuditEventBuilder


def audit_action(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    action_name: Optional[str] = None,
):
    def decorator(func: Callable) -> Callable:
        func_action = action_name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            actor_id = kwargs.get("user_id") or kwargs.get("actor_id")
            resource_id = kwargs.get("resource_id") or kwargs.get("id")
            
            try:
                result = await func(*args, **kwargs)
                
                builder = (
                    AuditEventBuilder(event_type)
                    .action(func_action)
                    .outcome("success")
                )
                
                if actor_id:
                    builder.actor(str(actor_id))
                if resource_type and resource_id:
                    builder.resource(resource_type, str(resource_id))
                
                audit_logger.log(builder.build())
                
                return result
            except Exception as e:
                builder = (
                    AuditEventBuilder(event_type)
                    .action(func_action)
                    .outcome("failure")
                    .metadata(error=str(e))
                )
                
                if actor_id:
                    builder.actor(str(actor_id))
                if resource_type and resource_id:
                    builder.resource(resource_type, str(resource_id))
                
                audit_logger.log(builder.build())
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            actor_id = kwargs.get("user_id") or kwargs.get("actor_id")
            resource_id = kwargs.get("resource_id") or kwargs.get("id")
            
            try:
                result = func(*args, **kwargs)
                
                builder = (
                    AuditEventBuilder(event_type)
                    .action(func_action)
                    .outcome("success")
                )
                
                if actor_id:
                    builder.actor(str(actor_id))
                if resource_type and resource_id:
                    builder.resource(resource_type, str(resource_id))
                
                audit_logger.log(builder.build())
                
                return result
            except Exception as e:
                builder = (
                    AuditEventBuilder(event_type)
                    .action(func_action)
                    .outcome("failure")
                    .metadata(error=str(e))
                )
                
                if actor_id:
                    builder.actor(str(actor_id))
                if resource_type and resource_id:
                    builder.resource(resource_type, str(resource_id))
                
                audit_logger.log(builder.build())
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
