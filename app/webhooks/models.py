from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class WebhookEventType(str, Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"
    
    RESOURCE_CREATED = "resource.created"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookEvent(BaseModel):
    id: str
    event_type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


class WebhookSubscription(BaseModel):
    id: str
    url: str
    events: List[WebhookEventType]
    secret: str
    is_active: bool = True
    created_at: datetime
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


class WebhookDelivery(BaseModel):
    id: str
    subscription_id: str
    event_id: str
    url: str
    status: DeliveryStatus
    attempts: int = 0
    max_attempts: int = 3
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class WebhookPayload(BaseModel):
    event: WebhookEvent
    subscription_id: str
    timestamp: datetime
    signature: str
