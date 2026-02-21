from typing import Optional


class CacheKey:
    USER_PREFIX = "user"
    SESSION_PREFIX = "session"
    RATE_LIMIT_PREFIX = "rate_limit"
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"{CacheKey.USER_PREFIX}:{user_id}"
    
    @staticmethod
    def user_by_email(email: str) -> str:
        return f"{CacheKey.USER_PREFIX}:email:{email.lower()}"
    
    @staticmethod
    def user_list(page: int = 1, limit: int = 10) -> str:
        return f"{CacheKey.USER_PREFIX}:list:{page}:{limit}"
    
    @staticmethod
    def session(session_id: str) -> str:
        return f"{CacheKey.SESSION_PREFIX}:{session_id}"
    
    @staticmethod
    def rate_limit(client_id: str, endpoint: Optional[str] = None) -> str:
        if endpoint:
            return f"{CacheKey.RATE_LIMIT_PREFIX}:{client_id}:{endpoint}"
        return f"{CacheKey.RATE_LIMIT_PREFIX}:{client_id}"
    
    @staticmethod
    def invalidation_pattern(prefix: str) -> str:
        return f"{prefix}:*"
