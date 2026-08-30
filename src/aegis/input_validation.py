"""Input validation middleware for FastAPI."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .safety_enhanced import InputValidationError, InputValidator


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware that validates and sanitizes request inputs."""

    # Paths to validate
    VALIDATED_PATHS = {
        "/v1/investigations": ["POST"],
        "/v2/investigations": ["POST"],
    }

    # Fields to validate in request body
    VALIDATION_RULES = {
        "patient_id": {
            "max_length": 100,
            "pattern": r"^[a-zA-Z0-9\-_]+$",
            "required": True,
        },
        "question": {
            "min_length": 3,
            "max_length": 1000,
            "required": True,
        },
        "reviewer_id": {
            "max_length": 100,
            "required": False,
        },
        "notes": {
            "max_length": 2000,
            "required": False,
        },
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this path/method needs validation
        path = request.url.path
        method = request.method

        if path not in self.VALIDATED_PATHS or method not in self.VALIDATED_PATHS[path]:
            return await call_next(request)

        # Only validate JSON requests
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return await call_next(request)

        try:
            # Read request body
            body = await request.body()

            if not body:
                return await call_next(request)

            import json
            data = json.loads(body)

            if not isinstance(data, dict):
                return await call_next(request)

            # Validate fields
            errors = []
            sanitized_data = {}

            for field_name, rules in self.VALIDATION_RULES.items():
                if field_name not in data:
                    if rules.get("required", False):
                        errors.append({
                            "field": field_name,
                            "message": f"{field_name} is required",
                            "code": "REQUIRED",
                        })
                    continue

                value = data[field_name]

                # Sanitize string values
                if isinstance(value, str):
                    try:
                        value = InputValidator.sanitize_string(value)
                    except InputValidationError as e:
                        errors.append({
                            "field": field_name,
                            "message": str(e),
                            "code": e.code,
                        })
                        continue

                # Validate length
                if isinstance(value, str):
                    min_length = rules.get("min_length", 1)
                    max_length = rules.get("max_length", 10000)

                    if len(value) < min_length:
                        errors.append({
                            "field": field_name,
                            "message": f"{field_name} must be at least {min_length} characters",
                            "code": "MIN_LENGTH",
                        })
                    elif len(value) > max_length:
                        errors.append({
                            "field": field_name,
                            "message": f"{field_name} must be at most {max_length} characters",
                            "code": "MAX_LENGTH",
                        })

                # Validate pattern
                if isinstance(value, str) and "pattern" in rules:
                    if not re.match(rules["pattern"], value):
                        errors.append({
                            "field": field_name,
                            "message": f"{field_name} format is invalid",
                            "code": "INVALID_FORMAT",
                        })

                sanitized_data[field_name] = value

            # Return validation errors
            if errors:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "data": None,
                        "meta": None,
                        "errors": [
                            {
                                "code": error.get("code", "VALIDATION_ERROR"),
                                "message": error["message"],
                                "field": error.get("field"),
                            }
                            for error in errors
                        ],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            # Rebuild request with sanitized data if needed
            if sanitized_data != {k: data[k] for k in sanitized_data if k in data}:
                sanitized_body = json.dumps(sanitized_data).encode()
                request._body = sanitized_body

            return await call_next(request)

        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "data": None,
                    "meta": None,
                    "errors": [
                        {
                            "code": "INVALID_JSON",
                            "message": "Request body must be valid JSON",
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            # Log error and continue
            return await call_next(request)
