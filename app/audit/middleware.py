import time
import uuid
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.audit.logger import audit_logger
from app.audit.events import AuditEventType, AuditEventBuilder


class AuditMiddleware(BaseHTTPMiddleware):
    SENSITIVE_PATHS = ["/auth/login", "/auth/register", "/auth/logout"]
    EXCLUDED_PATHS = ["/health", "/docs", "/openapi.json", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        if any(request.url.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if any(request.url.path.startswith(p) for p in self.SENSITIVE_PATHS):
            self._log_auth_event(request, response, client_ip, user_id, duration_ms)
        else:
            self._log_api_event(request, response, client_ip, user_id, duration_ms, request_id)
        
        response.headers["X-Request-ID"] = request_id
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from app.auth.jwt import decode_token_unsafe
            token = auth_header[7:]
            payload = decode_token_unsafe(token)
            if payload:
                return payload.get("sub")
        return None
    
    def _log_auth_event(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        user_id: Optional[str],
        duration_ms: float,
    ) -> None:
        path = request.url.path
        
        if "/login" in path:
            event_type = AuditEventType.USER_LOGIN if response.status_code == 200 else AuditEventType.AUTH_FAILED_LOGIN
        elif "/register" in path:
            event_type = AuditEventType.USER_REGISTER
        elif "/logout" in path:
            event_type = AuditEventType.USER_LOGOUT
        else:
            return
        
        outcome = "success" if 200 <= response.status_code < 300 else "failure"
        
        event = (
            AuditEventBuilder(event_type)
            .actor(user_id or "anonymous", ip=client_ip)
            .action(f"{request.method} {path}")
            .outcome(outcome)
            .metadata(
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            .build()
        )
        
        audit_logger.log(event)
    
    def _log_api_event(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        user_id: Optional[str],
        duration_ms: float,
        request_id: str,
    ) -> None:
        outcome = "success" if 200 <= response.status_code < 300 else "failure"
        
        event = (
            AuditEventBuilder(AuditEventType.API_REQUEST)
            .actor(user_id or "anonymous", ip=client_ip)
            .action(f"{request.method} {request.url.path}")
            .outcome(outcome)
            .metadata(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                user_agent=request.headers.get("User-Agent", ""),
            )
            .build()
        )
        
        audit_logger.log(event)
