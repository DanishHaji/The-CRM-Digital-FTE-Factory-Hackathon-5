"""Global error handlers for FastAPI application."""

from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register global error handlers for the FastAPI application.

    Handles:
    - Pydantic validation errors (422)
    - Request validation errors (422)
    - General exceptions (500)
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""

        request_id = getattr(request.state, "request_id", "unknown")

        # Extract validation errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        logger.error(
            "validation_error",
            request_id=request_id,
            path=request.url.path,
            errors=errors,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "detail": errors,
                "request_id": request_id,
            }
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request,
        exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""

        request_id = getattr(request.state, "request_id", "unknown")

        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        logger.error(
            "pydantic_validation_error",
            request_id=request_id,
            path=request.url.path,
            errors=errors,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "message": "Data validation failed",
                "detail": errors,
                "request_id": request_id,
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""

        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "unhandled_exception",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True,  # Include stack trace
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "detail": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
                "request_id": request_id,
            }
        )
