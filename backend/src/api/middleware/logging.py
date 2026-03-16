"""Request logging middleware for structured logging."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests with structured context.

    Adds:
    - Request ID to all logs
    - Request/response timing
    - HTTP method, path, status code
    - Error tracking
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add logging."""

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Bind request context to logger
        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # Log incoming request
        log.info(
            "request_started",
            query_params=dict(request.query_params),
            headers={
                "user-agent": request.headers.get("user-agent"),
                "content-type": request.headers.get("content-type"),
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            # Log successful response
            log.info(
                "request_completed",
                status_code=response.status_code,
                process_time_seconds=process_time,
            )

            return response

        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            log.error(
                "request_failed",
                error_type=type(exc).__name__,
                error_message=str(exc),
                process_time_seconds=process_time,
            )

            # Re-raise for error handler
            raise
