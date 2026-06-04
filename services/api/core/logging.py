import logging as py_logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from services.api.core.config import Settings


def configure_logging(settings: Settings) -> None:
    level = getattr(py_logging, settings.log_level.upper(), py_logging.INFO)
    py_logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> py_logging.Logger:
    return py_logging.getLogger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request metadata without logging prompts or request bodies."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings
        self.logger = get_logger("tellus_ai.requests")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        self.logger.info(
            "request method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

