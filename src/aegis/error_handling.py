from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("aegis.errors")


class ErrorResponse:
    """Standardized error response."""

    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_type: str = "error",
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> JSONResponse:
        """Create a standardized error response."""
        content = {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        if details:
            content["error"]["details"] = details

        if request_id:
            content["error"]["request_id"] = request_id

        return JSONResponse(status_code=status_code, content=content)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", "")

        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Handle HTTP exceptions
            logger.warning(
                f"HTTP error {e.status_code}: {e.detail}",
                extra={
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
            )
            return ErrorResponse.create(
                status_code=e.status_code,
                message=str(e.detail),
                error_type="http_error",
                request_id=request_id,
            )

        except ValueError as e:
            # Handle validation errors
            logger.warning(
                f"Validation error: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
            )
            return ErrorResponse.create(
                status_code=400,
                message=str(e),
                error_type="validation_error",
                request_id=request_id,
            )

        except PermissionError as e:
            # Handle permission errors
            logger.warning(
                f"Permission error: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
            )
            return ErrorResponse.create(
                status_code=403,
                message=str(e) or "Permission denied",
                error_type="permission_error",
                request_id=request_id,
            )

        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                    "traceback": traceback.format_exc(),
                },
            )
            return ErrorResponse.create(
                status_code=500,
                message="An unexpected error occurred",
                error_type="internal_error",
                details={"error": str(e)} if logger.isEnabledFor(logging.DEBUG) else None,
                request_id=request_id,
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = datetime.now(timezone.utc)
        request_id = request.headers.get("X-Request-ID", "")

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client": request.client.host if request.client else "unknown",
                "request_id": request_id,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Log response
        logger.info(
            f"Response: {response.status_code} ({duration:.1f}ms)",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration,
                "path": request.url.path,
                "method": request.method,
                "request_id": request_id,
            },
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.1f}ms"
        if request_id:
            response.headers["X-Request-ID"] = request_id

        return response
