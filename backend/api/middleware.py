"""FastAPI middleware for request tracing and context propagation."""
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = structlog.get_logger("docintel.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request tracing and structured logging context."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with automatic context binding and timing."""
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info(
            "request_started",
            client_host=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as error:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "request_failed",
                error_type=type(error).__name__,
                error_message=str(error),
                duration_ms=duration_ms,
            )
            raise
