from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    We chose a sliding window approach over token bucket because:
    - Simpler to reason about for API consumers
    - Provides predictable rate limiting behavior
    - Easier to debug when users hit limits
    
    For production, this should be replaced with Redis-backed storage.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = timedelta(minutes=1)
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(self, client_id: str, now: datetime) -> None:
        cutoff = now - self.window_size
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > cutoff
        ]
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        now = datetime.utcnow()
        self._clean_old_requests(client_id, now)
        
        current_count = len(self._requests[client_id])
        remaining = max(0, self.requests_per_minute - current_count)
        
        if current_count >= self.requests_per_minute:
            return False, remaining
        
        self._requests[client_id].append(now)
        return True, remaining - 1
    
    def get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


rate_limiter = RateLimiter(requests_per_minute=60)


async def rate_limit_middleware(request: Request, call_next):
    client_id = rate_limiter.get_client_id(request)
    allowed, remaining = rate_limiter.is_allowed(client_id)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in 1 minute.",
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response
