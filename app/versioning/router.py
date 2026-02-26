from typing import Dict, List, Optional, Callable
from fastapi import FastAPI, APIRouter, Request
from fastapi.routing import APIRoute
from datetime import date


class VersionedRouter:
    def __init__(self, prefix: str = "/api"):
        self.prefix = prefix
        self._versions: Dict[str, APIRouter] = {}
        self._default_version: Optional[str] = None
    
    def register_version(
        self,
        version: str,
        router: APIRouter,
        is_default: bool = False,
        deprecated: bool = False,
        sunset_date: Optional[date] = None,
    ) -> None:
        self._versions[version] = {
            "router": router,
            "deprecated": deprecated,
            "sunset_date": sunset_date,
        }
        
        if is_default:
            self._default_version = version
    
    def get_router(self, version: str) -> Optional[APIRouter]:
        version_info = self._versions.get(version)
        if version_info:
            return version_info["router"]
        return None
    
    def get_versions(self) -> List[str]:
        return list(self._versions.keys())
    
    def get_default_version(self) -> Optional[str]:
        return self._default_version
    
    def is_deprecated(self, version: str) -> bool:
        version_info = self._versions.get(version)
        if version_info:
            return version_info.get("deprecated", False)
        return False
    
    def get_sunset_date(self, version: str) -> Optional[date]:
        version_info = self._versions.get(version)
        if version_info:
            return version_info.get("sunset_date")
        return None
    
    def mount_to_app(self, app: FastAPI) -> None:
        for version, info in self._versions.items():
            router = info["router"]
            version_prefix = f"{self.prefix}/{version}"
            app.include_router(router, prefix=version_prefix)


def create_versioned_app(
    title: str,
    description: str = "",
    versions: Dict[str, APIRouter] = None,
    default_version: str = "v1",
) -> FastAPI:
    app = FastAPI(
        title=title,
        description=description,
    )
    
    versioned_router = VersionedRouter()
    
    if versions:
        for version, router in versions.items():
            is_default = version == default_version
            versioned_router.register_version(version, router, is_default=is_default)
    
    versioned_router.mount_to_app(app)
    
    @app.get("/api/versions")
    async def list_versions():
        return {
            "versions": versioned_router.get_versions(),
            "default": versioned_router.get_default_version(),
            "deprecated": [
                v for v in versioned_router.get_versions()
                if versioned_router.is_deprecated(v)
            ],
        }
    
    return app


class VersionedAPIRoute(APIRoute):
    def __init__(
        self,
        *args,
        introduced_in: str = "v1",
        deprecated_in: Optional[str] = None,
        removed_in: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.introduced_in = introduced_in
        self.deprecated_in = deprecated_in
        self.removed_in = removed_in
    
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()
        
        async def versioned_handler(request: Request):
            response = await original_handler(request)
            
            if self.deprecated_in:
                response.headers["X-API-Deprecated-In"] = self.deprecated_in
            if self.removed_in:
                response.headers["X-API-Removed-In"] = self.removed_in
            
            return response
        
        return versioned_handler
