from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.api.core.config import Settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Protect internal API endpoints with an API key."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings
        self.exempt_paths = {"/health", "/docs", "/openapi.json", "/redoc"}

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

        if not supplied_key or supplied_key != self.settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key."},
            )

        return await call_next(request)

