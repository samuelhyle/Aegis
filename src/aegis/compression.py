"""Compression middleware for API responses."""

from __future__ import annotations

import gzip
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware that compresses JSON responses using gzip.

    Only compresses responses that:
    1. Are JSON content type
    2. Are larger than 1KB
    3. Client accepts gzip encoding
    """

    MIN_SIZE_FOR_COMPRESSION = 1024  # 1KB

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response

        # Check content type
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Check if already compressed
        if response.headers.get("content-encoding") == "gzip":
            return response

        # Read response body
        try:
            body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body += chunk.encode("utf-8")
                else:
                    body += chunk

            # Skip if too small
            if len(body) < self.MIN_SIZE_FOR_COMPRESSION:
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=content_type,
                )

            # Compress
            compressed = gzip.compress(body)

            # Only use compressed if it's smaller
            if len(compressed) >= len(body):
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=content_type,
                )

            # Build new headers
            headers = dict(response.headers)
            headers["content-encoding"] = "gzip"
            headers["content-length"] = str(len(compressed))

            return Response(
                content=compressed,
                status_code=response.status_code,
                headers=headers,
                media_type=content_type,
            )

        except Exception:
            return response
