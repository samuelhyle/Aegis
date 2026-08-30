"""API response envelope types for standardized responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    per_page: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
    total_pages: int = Field(..., description="Total number of pages")


class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: str | None = Field(default=None, description="Field that caused the error")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    All API responses should follow this format:
    {
        "success": true/false,
        "data": <response_data>,
        "meta": <optional_metadata>,
        "errors": <optional_errors>,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: T | None = Field(default=None, description="Response data")
    meta: dict[str, Any] | PaginationMeta | None = Field(default=None, description="Response metadata")
    errors: list[ErrorDetail] | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class APIError(BaseModel):
    """Standard API error response."""
    success: bool = Field(default=False, description="Always false for errors")
    data: None = Field(default=None, description="Always null for errors")
    meta: None = Field(default=None, description="Always null for errors")
    errors: list[ErrorDetail] = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response envelope.

    Extends APIResponse with pagination metadata.
    """
    success: bool = Field(default=True, description="Whether the request was successful")
    data: list[T] = Field(default_factory=list, description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    errors: list[ErrorDetail] | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


def success_response(
    data: Any,
    meta: dict[str, Any] | PaginationMeta | None = None,
) -> dict[str, Any]:
    """Create a success response envelope."""
    return {
        "success": True,
        "data": data,
        "meta": meta,
        "errors": None,
        "timestamp": datetime.utcnow().isoformat(),
    }


def error_response(
    errors: list[dict[str, Any]] | dict[str, Any] | str,
    status_code: int = 400,
) -> dict[str, Any]:
    """Create an error response envelope."""
    if isinstance(errors, str):
        error_list = [{"code": "UNKNOWN_ERROR", "message": errors}]
    elif isinstance(errors, dict):
        error_list = [errors]
    else:
        error_list = errors

    return {
        "success": False,
        "data": None,
        "meta": None,
        "errors": error_list,
        "timestamp": datetime.utcnow().isoformat(),
    }


def paginated_response(
    data: list[Any],
    total: int,
    page: int,
    per_page: int,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a paginated response envelope."""
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    has_more = page * per_page < total

    meta = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": has_more,
        "total_pages": total_pages,
    }

    if extra_meta:
        meta.update(extra_meta)

    return {
        "success": True,
        "data": data,
        "meta": meta,
        "errors": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
