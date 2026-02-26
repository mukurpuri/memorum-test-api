from functools import wraps
from typing import Callable, Optional
from datetime import date
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import warnings

logger = logging.getLogger(__name__)


class DeprecationWarning:
    def __init__(
        self,
        message: str,
        deprecated_in: str,
        removed_in: Optional[str] = None,
        sunset_date: Optional[date] = None,
        alternative: Optional[str] = None,
    ):
        self.message = message
        self.deprecated_in = deprecated_in
        self.removed_in = removed_in
        self.sunset_date = sunset_date
        self.alternative = alternative
    
    def to_header(self) -> str:
        parts = [f'299 - "{self.message}"']
        
        if self.sunset_date:
            parts.append(f'sunset="{self.sunset_date.isoformat()}"')
        
        return " ".join(parts)
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "deprecated_in": self.deprecated_in,
            "removed_in": self.removed_in,
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "alternative": self.alternative,
        }


def deprecated_endpoint(
    deprecated_in: str,
    removed_in: Optional[str] = None,
    sunset_date: Optional[date] = None,
    message: Optional[str] = None,
    alternative: Optional[str] = None,
):
    def decorator(func: Callable) -> Callable:
        deprecation_message = message or f"This endpoint is deprecated since {deprecated_in}"
        
        deprecation = DeprecationWarning(
            message=deprecation_message,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            sunset_date=sunset_date,
            alternative=alternative,
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            logger.warning(
                f"Deprecated endpoint called: {func.__name__}",
                extra={
                    "endpoint": func.__name__,
                    "deprecated_in": deprecated_in,
                    "removed_in": removed_in,
                }
            )
            
            result = await func(*args, **kwargs)
            
            if isinstance(result, JSONResponse):
                result.headers["Warning"] = deprecation.to_header()
                result.headers["X-Deprecated"] = "true"
                if sunset_date:
                    result.headers["Sunset"] = sunset_date.isoformat()
                if alternative:
                    result.headers["X-Alternative"] = alternative
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger.warning(
                f"Deprecated endpoint called: {func.__name__}",
                extra={
                    "endpoint": func.__name__,
                    "deprecated_in": deprecated_in,
                }
            )
            
            result = func(*args, **kwargs)
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            async_wrapper.deprecation = deprecation
            return async_wrapper
        
        sync_wrapper.deprecation = deprecation
        return sync_wrapper
    
    return decorator


def emit_deprecation_warning(
    feature: str,
    deprecated_in: str,
    removed_in: Optional[str] = None,
    alternative: Optional[str] = None,
) -> None:
    message = f"{feature} is deprecated since {deprecated_in}"
    
    if removed_in:
        message += f" and will be removed in {removed_in}"
    
    if alternative:
        message += f". Use {alternative} instead"
    
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    logger.warning(message)
