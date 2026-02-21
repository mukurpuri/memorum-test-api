import os
from typing import Dict, Set, Optional, Any
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._overrides: Dict[str, bool] = {}
        self._user_overrides: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        env_prefix = "FEATURE_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                flag_name = key[len(env_prefix):].lower()
                self._flags[flag_name] = value.lower() in ("true", "1", "yes", "on")
    
    def register(
        self,
        name: str,
        default: bool = False,
        description: str = "",
    ) -> None:
        with self._lock:
            if name not in self._flags:
                self._flags[name] = default
    
    def is_enabled(
        self,
        name: str,
        user_id: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        with self._lock:
            if user_id and name in self._user_overrides:
                if user_id in self._user_overrides[name]:
                    return True
            
            if name in self._overrides:
                return self._overrides[name]
            
            return self._flags.get(name, default)
    
    def enable(self, name: str) -> None:
        with self._lock:
            self._overrides[name] = True
            logger.info(f"Feature flag '{name}' enabled")
    
    def disable(self, name: str) -> None:
        with self._lock:
            self._overrides[name] = False
            logger.info(f"Feature flag '{name}' disabled")
    
    def enable_for_user(self, name: str, user_id: str) -> None:
        with self._lock:
            if name not in self._user_overrides:
                self._user_overrides[name] = set()
            self._user_overrides[name].add(user_id)
    
    def disable_for_user(self, name: str, user_id: str) -> None:
        with self._lock:
            if name in self._user_overrides:
                self._user_overrides[name].discard(user_id)
    
    def reset(self, name: str) -> None:
        with self._lock:
            self._overrides.pop(name, None)
            self._user_overrides.pop(name, None)
    
    def reset_all(self) -> None:
        with self._lock:
            self._overrides.clear()
            self._user_overrides.clear()
    
    def list_flags(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {
                name: {
                    "default": self._flags.get(name, False),
                    "override": self._overrides.get(name),
                    "effective": self.is_enabled(name),
                    "user_overrides_count": len(self._user_overrides.get(name, set())),
                }
                for name in set(self._flags.keys()) | set(self._overrides.keys())
            }


feature_flags = FeatureFlags()

feature_flags.register("new_auth_flow", default=False)
feature_flags.register("enhanced_logging", default=True)
feature_flags.register("rate_limit_v2", default=False)
feature_flags.register("webhook_retries", default=True)
feature_flags.register("cache_warming", default=False)
