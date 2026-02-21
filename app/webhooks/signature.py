import hmac
import hashlib
import time
from typing import Tuple


class WebhookSigner:
    SIGNATURE_VERSION = "v1"
    TIMESTAMP_TOLERANCE = 300
    
    def __init__(self, secret: str):
        self.secret = secret
    
    def sign(self, payload: str, timestamp: int = None) -> Tuple[str, int]:
        if timestamp is None:
            timestamp = int(time.time())
        
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{self.SIGNATURE_VERSION}={signature}", timestamp
    
    def verify(self, payload: str, signature: str, timestamp: int) -> bool:
        current_time = int(time.time())
        if abs(current_time - timestamp) > self.TIMESTAMP_TOLERANCE:
            return False
        
        expected_signature, _ = self.sign(payload, timestamp)
        return hmac.compare_digest(signature, expected_signature)
    
    def create_header(self, payload: str) -> dict:
        signature, timestamp = self.sign(payload)
        return {
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(timestamp),
        }
    
    def verify_header(
        self,
        payload: str,
        signature_header: str,
        timestamp_header: str,
    ) -> bool:
        try:
            timestamp = int(timestamp_header)
            return self.verify(payload, signature_header, timestamp)
        except (ValueError, TypeError):
            return False
