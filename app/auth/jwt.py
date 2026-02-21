import os
import hashlib
import hmac
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def _create_signature(header_payload: str) -> str:
    signature = hmac.new(
        SECRET_KEY.encode(),
        header_payload.encode(),
        hashlib.sha256
    ).digest()
    return _base64url_encode(signature)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
    })
    
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_encoded = _base64url_encode(json.dumps(header).encode())
    payload_encoded = _base64url_encode(json.dumps(to_encode).encode())
    
    header_payload = f"{header_encoded}.{payload_encoded}"
    signature = _create_signature(header_payload)
    
    return f"{header_payload}.{signature}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_encoded, payload_encoded, signature = parts
        
        expected_signature = _create_signature(f"{header_encoded}.{payload_encoded}")
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        payload = json.loads(_base64url_decode(payload_encoded))
        
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None
        
        return payload
    except Exception:
        return None


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload_encoded = parts[1]
        return json.loads(_base64url_decode(payload_encoded))
    except Exception:
        return None
