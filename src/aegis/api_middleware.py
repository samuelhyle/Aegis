"""API response middleware for automatic envelope wrapping."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class APIResponseMiddleware(BaseHTTPMiddleware):
    """Middleware that wraps all responses in the standard API envelope.

    This middleware intercepts responses and wraps them in the standard
    {success, data, meta, errors, timestamp} format.

    Responses that are already wrapped (contain 'success' field) are not double-wrapped.
    """

    # Paths to exclude from envelope wrapping
    EXCLUDED_PATHS = {
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Content types to exclude
    EXCLUDED_CONTENT_TYPES = {
        "text/event-stream",
        "text/html",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Skip middleware for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return response

        # Skip middleware for non-JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Skip if streaming response
        if hasattr(response, "body_iterator"):
            return response

        # Read response body
        try:
            body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body += chunk.encode("utf-8")
                else:
                    body += chunk

            if not body:
                return response

            data = json.loads(body)

            # Skip if already wrapped
            if isinstance(data, dict) and "success" in data:
                return JSONResponse(
                    content=data,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # Wrap response in envelope
            if response.status_code >= 400:
                # Error response
                wrapped = {
                    "success": False,
                    "data": None,
                    "meta": None,
                    "errors": [
                        {
                            "code": "HTTP_ERROR",
                            "message": data.get("detail", str(data)) if isinstance(data, dict) else str(data),
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                # Success response
                wrapped = {
                    "success": True,
                    "data": data,
                    "meta": None,
                    "errors": None,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            return JSONResponse(
                content=wrapped,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except Exception:
            # If we can't parse the body, return original response
            return response
