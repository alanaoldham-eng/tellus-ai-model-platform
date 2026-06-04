from collections.abc import Awaitable, Callable
from secrets import compare_digest

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.api.core.config import Settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Protect internal API endpoints with an API key."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings
        self.exempt_paths = {
            "/",
            "/flow-builder/demo",
            "/flow-builder/demo/generate",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/favicon.png",
        }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "OPTIONS" or request.url.path in self.exempt_paths:
            return await call_next(request)

        supplied_key = request.headers.get("x-api-key")
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied_key = authorization[7:].strip()

        tenant_header = request.headers.get("x-tellus-tenant-id")
        tenant_match = self._tenant_for_key(supplied_key or "")
        global_match = bool(supplied_key) and compare_digest(supplied_key, self.settings.api_key)

        if tenant_header and tenant_match and tenant_header != tenant_match:
            return JSONResponse(
                status_code=403,
                content={"detail": "Tenant API key does not match X-Tellus-Tenant-Id."},
            )

        if tenant_match:
            request.state.tenant_id = tenant_match
        elif global_match:
            request.state.tenant_id = tenant_header
        else:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key."},
            )

        if self.settings.require_tenant_header and not getattr(request.state, "tenant_id", None):
            return JSONResponse(
                status_code=401,
                content={"detail": "X-Tellus-Tenant-Id is required."},
            )

        return await call_next(request)

    def _tenant_for_key(self, supplied_key: str) -> str | None:
        for tenant_id, tenant_key in self.settings.tenant_api_keys.items():
            if compare_digest(supplied_key, tenant_key):
                return tenant_id
        return None
