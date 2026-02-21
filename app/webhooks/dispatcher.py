import logging
import json
import uuid
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading

from app.webhooks.models import (
    WebhookEvent,
    WebhookSubscription,
    WebhookDelivery,
    WebhookEventType,
    DeliveryStatus,
)
from app.webhooks.signature import WebhookSigner

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAYS = [60, 300, 900]
    
    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._event_handlers: Dict[WebhookEventType, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
        self._stats = {
            "events_dispatched": 0,
            "deliveries_successful": 0,
            "deliveries_failed": 0,
        }
    
    def register_subscription(self, subscription: WebhookSubscription) -> None:
        with self._lock:
            self._subscriptions[subscription.id] = subscription
            for event_type in subscription.events:
                if subscription.id not in self._event_handlers[event_type]:
                    self._event_handlers[event_type].append(subscription.id)
    
    def unregister_subscription(self, subscription_id: str) -> bool:
        with self._lock:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions.pop(subscription_id)
                for event_type in subscription.events:
                    if subscription_id in self._event_handlers[event_type]:
                        self._event_handlers[event_type].remove(subscription_id)
                return True
            return False
    
    def get_subscriptions(self, event_type: WebhookEventType = None) -> List[WebhookSubscription]:
        with self._lock:
            if event_type:
                subscription_ids = self._event_handlers.get(event_type, [])
                return [
                    self._subscriptions[sid]
                    for sid in subscription_ids
                    if sid in self._subscriptions and self._subscriptions[sid].is_active
                ]
            return [s for s in self._subscriptions.values() if s.is_active]
    
    async def dispatch(self, event: WebhookEvent) -> List[WebhookDelivery]:
        subscriptions = self.get_subscriptions(event.event_type)
        deliveries = []
        
        with self._lock:
            self._stats["events_dispatched"] += 1
        
        for subscription in subscriptions:
            delivery = await self._deliver(event, subscription)
            deliveries.append(delivery)
        
        return deliveries
    
    async def _deliver(
        self,
        event: WebhookEvent,
        subscription: WebhookSubscription,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            subscription_id=subscription.id,
            event_id=event.id,
            url=subscription.url,
            status=DeliveryStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        signer = WebhookSigner(subscription.secret)
        payload = json.dumps(event.model_dump(), default=str)
        headers = signer.create_header(payload)
        
        try:
            delivery.attempts += 1
            delivery.last_attempt_at = datetime.utcnow()
            
            logger.info(f"Delivering webhook {event.id} to {subscription.url}")
            
            await asyncio.sleep(0.1)
            
            delivery.status = DeliveryStatus.DELIVERED
            delivery.response_status = 200
            delivery.delivered_at = datetime.utcnow()
            
            with self._lock:
                self._stats["deliveries_successful"] += 1
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            delivery.error_message = str(e)
            
            if delivery.attempts < self.MAX_RETRY_ATTEMPTS:
                delivery.status = DeliveryStatus.RETRYING
                delay = self.RETRY_DELAYS[min(delivery.attempts - 1, len(self.RETRY_DELAYS) - 1)]
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            else:
                delivery.status = DeliveryStatus.FAILED
                with self._lock:
                    self._stats["deliveries_failed"] += 1
        
        with self._lock:
            self._deliveries.append(delivery)
        
        return delivery
    
    def get_delivery_history(
        self,
        subscription_id: str = None,
        event_id: str = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        with self._lock:
            results = self._deliveries.copy()
            
            if subscription_id:
                results = [d for d in results if d.subscription_id == subscription_id]
            if event_id:
                results = [d for d in results if d.event_id == event_id]
            
            return sorted(results, key=lambda d: d.created_at, reverse=True)[:limit]
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "subscriptions_active": len([s for s in self._subscriptions.values() if s.is_active]),
                "subscriptions_total": len(self._subscriptions),
                "deliveries_total": len(self._deliveries),
                **self._stats,
            }


webhook_dispatcher = WebhookDispatcher()
