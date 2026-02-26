import re
from typing import Optional, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class VersionMiddleware(BaseHTTPMiddleware):
    VERSION_PATTERN = re.compile(r"/api/(v\d+)/")
    HEADER_NAME = "X-API-Version"
    SUPPORTED_VERSIONS = ["v1", "v2"]
    DEFAULT_VERSION = "v1"
    DEPRECATED_VERSIONS = ["v1"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        version = self._extract_version(request)
        
        if version and version not in self.SUPPORTED_VERSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. "
                       f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}",
            )
        
        response = await call_next(request)
        
        if version:
            response.headers["X-API-Version"] = version
            
            if version in self.DEPRECATED_VERSIONS:
                response.headers["X-API-Deprecated"] = "true"
                response.headers["Warning"] = (
                    f'299 - "API version {version} is deprecated. '
                    f'Please migrate to {self.SUPPORTED_VERSIONS[-1]}."'
                )
        
        response.headers["X-API-Supported-Versions"] = ", ".join(self.SUPPORTED_VERSIONS)
        
        return response
    
    def _extract_version(self, request: Request) -> Optional[str]:
        header_version = request.headers.get(self.HEADER_NAME)
        if header_version:
            return header_version.lower()
        
        match = self.VERSION_PATTERN.search(request.url.path)
        if match:
            return match.group(1)
        
        return None


class ContentNegotiationMiddleware(BaseHTTPMiddleware):
    ACCEPT_VERSION_PATTERN = re.compile(r"application/vnd\.api\.(v\d+)\+json")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        accept_header = request.headers.get("Accept", "")
        
        match = self.ACCEPT_VERSION_PATTERN.search(accept_header)
        if match:
            version = match.group(1)
            request.state.api_version = version
        
        response = await call_next(request)
        
        if hasattr(request.state, "api_version"):
            response.headers["Content-Type"] = (
                f"application/vnd.api.{request.state.api_version}+json"
            )
        
        return response
