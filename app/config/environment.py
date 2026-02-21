import os
from enum import Enum
from typing import Optional
from functools import lru_cache


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    
    @property
    def is_development(self) -> bool:
        return self == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self == Environment.PRODUCTION
    
    @property
    def is_staging(self) -> bool:
        return self == Environment.STAGING
    
    @property
    def is_testing(self) -> bool:
        return self == Environment.TESTING
    
    @property
    def is_debug_enabled(self) -> bool:
        return self in (Environment.DEVELOPMENT, Environment.TESTING)
    
    @property
    def log_level(self) -> str:
        if self.is_debug_enabled:
            return "DEBUG"
        return "INFO"


@lru_cache()
def get_environment() -> Environment:
    env_name = os.getenv("APP_ENVIRONMENT", "development").lower()
    
    try:
        return Environment(env_name)
    except ValueError:
        return Environment.DEVELOPMENT


def require_environment(*envs: Environment) -> bool:
    current = get_environment()
    if current not in envs:
        raise EnvironmentError(
            f"Operation requires environment {[e.value for e in envs]}, "
            f"but current environment is {current.value}"
        )
    return True


def is_production() -> bool:
    return get_environment().is_production


def is_development() -> bool:
    return get_environment().is_development
