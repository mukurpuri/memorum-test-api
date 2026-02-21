from functools import wraps
from typing import Callable, Optional, Any
import hashlib
import json

from app.cache.backend import cache


def _make_key(prefix: str, args: tuple, kwargs: dict) -> str:
    key_parts = [prefix]
    
    for arg in args:
        if hasattr(arg, '__dict__'):
            key_parts.append(str(id(arg)))
        else:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    prefix: Optional[str] = None,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
):
    def decorator(func: Callable) -> Callable:
        cache_prefix = prefix or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _make_key(cache_prefix, args, kwargs)
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _make_key(cache_prefix, args, kwargs)
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def cache_aside(
    key: str,
    ttl: Optional[int] = None,
    loader: Optional[Callable] = None,
) -> Any:
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value
    
    if loader:
        value = loader()
        cache.set(key, value, ttl)
        return value
    
    return None


def invalidate_cache(pattern: str) -> int:
    count = 0
    keys_to_delete = []
    
    for key in list(cache._cache.keys()):
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache.delete(key)
        count += 1
    
    return count
