from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AuditEventType(str, Enum):
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_FAILED_LOGIN = "auth.failed_login"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"
    
    RESOURCE_CREATE = "resource.create"
    RESOURCE_READ = "resource.read"
    RESOURCE_UPDATE = "resource.update"
    RESOURCE_DELETE = "resource.delete"
    
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    PERMISSION_DENIED = "permission.denied"
    
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGED = "system.config_changed"
    
    API_REQUEST = "api.request"
    API_RATE_LIMITED = "api.rate_limited"


class AuditEvent(BaseModel):
    id: str
    event_type: AuditEventType
    timestamp: datetime
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    outcome: str
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


class AuditEventBuilder:
    def __init__(self, event_type: AuditEventType):
        self._event_type = event_type
        self._actor_id: Optional[str] = None
        self._actor_email: Optional[str] = None
        self._actor_ip: Optional[str] = None
        self._resource_type: Optional[str] = None
        self._resource_id: Optional[str] = None
        self._action: str = ""
        self._outcome: str = "success"
        self._metadata: Dict[str, Any] = {}
    
    def actor(self, user_id: str, email: Optional[str] = None, ip: Optional[str] = None):
        self._actor_id = user_id
        self._actor_email = email
        self._actor_ip = ip
        return self
    
    def resource(self, resource_type: str, resource_id: str):
        self._resource_type = resource_type
        self._resource_id = resource_id
        return self
    
    def action(self, action: str):
        self._action = action
        return self
    
    def outcome(self, outcome: str):
        self._outcome = outcome
        return self
    
    def metadata(self, **kwargs):
        self._metadata.update(kwargs)
        return self
    
    def build(self) -> AuditEvent:
        import uuid
        return AuditEvent(
            id=str(uuid.uuid4()),
            event_type=self._event_type,
            timestamp=datetime.utcnow(),
            actor_id=self._actor_id,
            actor_email=self._actor_email,
            actor_ip=self._actor_ip,
            resource_type=self._resource_type,
            resource_id=self._resource_id,
            action=self._action,
            outcome=self._outcome,
            metadata=self._metadata,
        )
