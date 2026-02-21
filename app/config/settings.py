import os
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    url: str = ":memory:"
    pool_min_size: int = 2
    pool_max_size: int = 10
    echo: bool = False


class AuthSettings(BaseModel):
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class CacheSettings(BaseModel):
    enabled: bool = True
    default_ttl: int = 300
    max_size: int = 1000
    backend: str = "memory"
    redis_url: Optional[str] = None


class RateLimitSettings(BaseModel):
    enabled: bool = True
    requests_per_minute: int = 60
    burst_size: int = 10


class CorsSettings(BaseModel):
    enabled: bool = True
    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False


class Settings(BaseModel):
    app_name: str = "Memorum Test API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    database: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    cache: CacheSettings = CacheSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    cors: CorsSettings = CorsSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_prefix = "APP_"
        env_nested_delimiter = "__"


def load_settings_from_env() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Memorum Test API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        debug=os.getenv("APP_DEBUG", "false").lower() == "true",
        environment=os.getenv("APP_ENVIRONMENT", "development"),
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        workers=int(os.getenv("APP_WORKERS", "1")),
        database=DatabaseSettings(
            url=os.getenv("DATABASE_URL", ":memory:"),
            pool_min_size=int(os.getenv("DATABASE_POOL_MIN", "2")),
            pool_max_size=int(os.getenv("DATABASE_POOL_MAX", "10")),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        ),
        auth=AuthSettings(
            secret_key=os.getenv("JWT_SECRET", "dev-secret-change-in-production"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
        ),
        cache=CacheSettings(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            default_ttl=int(os.getenv("CACHE_TTL", "300")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            redis_url=os.getenv("REDIS_URL"),
        ),
        rate_limit=RateLimitSettings(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
        ),
    )


@lru_cache()
def get_settings() -> Settings:
    return load_settings_from_env()


settings = get_settings()
