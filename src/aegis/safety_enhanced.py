"""Enhanced safety features with rate limiting per user role and input validation."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Rate Limiting per User Role
# ---------------------------------------------------------------------------

class UserRole(StrEnum):
    """User roles with different rate limits."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a role."""
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int = 10
    burst_window_seconds: float = 1.0


DEFAULT_RATE_LIMITS: dict[UserRole, RateLimitConfig] = {
    UserRole.ADMIN: RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=2000,
        burst_size=50,
        burst_window_seconds=1.0,
    ),
    UserRole.CLINICIAN: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=20,
        burst_window_seconds=1.0,
    ),
    UserRole.RESEARCHER: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        burst_size=10,
        burst_window_seconds=1.0,
    ),
    UserRole.VIEWER: RateLimitConfig(
        requests_per_minute=15,
        requests_per_hour=200,
        burst_size=5,
        burst_window_seconds=1.0,
    ),
}


@dataclass
class TokenBucket:
    """Token bucket for burst rate limiting."""
    capacity: int
    tokens: float
    last_refill: float
    refill_rate: float  # tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


@dataclass
class RateLimitEntry:
    """Rate limit tracking for a user."""
    user_id: str
    role: UserRole
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    minute_reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=1))
    hour_reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    bucket: TokenBucket | None = None

    def __post_init__(self):
        config = DEFAULT_RATE_LIMITS.get(self.role, DEFAULT_RATE_LIMITS[UserRole.VIEWER])
        self.bucket = TokenBucket(
            capacity=config.burst_size,
            tokens=config.burst_size,
            last_refill=time.time(),
            refill_rate=config.burst_size / config.burst_window_seconds,
        )


class RateLimiter:
    """Rate limiter with per-role limits and token bucket for bursts."""

    def __init__(self, default_role: UserRole = UserRole.VIEWER):
        self._entries: dict[str, RateLimitEntry] = {}
        self._default_role = default_role
        self._config = DEFAULT_RATE_LIMITS

    def _get_or_create_entry(self, user_id: str, role: UserRole | None = None) -> RateLimitEntry:
        """Get or create rate limit entry for a user."""
        if user_id not in self._entries:
            self._entries[user_id] = RateLimitEntry(
                user_id=user_id,
                role=role or self._default_role,
            )
        return self._entries[user_id]

    def check_rate_limit(self, user_id: str, role: UserRole | None = None) -> dict[str, Any]:
        """Check if a request is allowed for the given user."""
        entry = self._get_or_create_entry(user_id, role)
        config = self._config.get(entry.role, self._config[self._default_role])

        now = datetime.now(timezone.utc)

        # Reset counters if window has passed
        if now >= entry.minute_reset_at:
            entry.requests_this_minute = 0
            entry.minute_reset_at = now + timedelta(minutes=1)

        if now >= entry.hour_reset_at:
            entry.requests_this_hour = 0
            entry.hour_reset_at = now + timedelta(hours=1)

        # Check burst limit
        if entry.bucket and not entry.bucket.consume():
            return {
                "allowed": False,
                "reason": "Burst limit exceeded",
                "retry_after_seconds": 1.0,
                "limit": config.burst_size,
                "remaining": int(entry.bucket.tokens) if entry.bucket else 0,
            }

        # Check per-minute limit
        if entry.requests_this_minute >= config.requests_per_minute:
            retry_after = (entry.minute_reset_at - now).total_seconds()
            return {
                "allowed": False,
                "reason": "Per-minute rate limit exceeded",
                "retry_after_seconds": max(retry_after, 1),
                "limit": config.requests_per_minute,
                "remaining": 0,
            }

        # Check per-hour limit
        if entry.requests_this_hour >= config.requests_per_hour:
            retry_after = (entry.hour_reset_at - now).total_seconds()
            return {
                "allowed": False,
                "reason": "Per-hour rate limit exceeded",
                "retry_after_seconds": max(retry_after, 1),
                "limit": config.requests_per_hour,
                "remaining": 0,
            }

        # Allow request
        entry.requests_this_minute += 1
        entry.requests_this_hour += 1

        return {
            "allowed": True,
            "limit": config.requests_per_minute,
            "remaining": config.requests_per_minute - entry.requests_this_minute,
            "reset_at": entry.minute_reset_at.isoformat(),
        }

    def get_user_stats(self, user_id: str) -> dict[str, Any] | None:
        """Get rate limit stats for a user."""
        entry = self._entries.get(user_id)
        if not entry:
            return None

        config = self._config.get(entry.role, self._config[self._default_role])

        return {
            "user_id": user_id,
            "role": entry.role.value,
            "requests_this_minute": entry.requests_this_minute,
            "requests_this_hour": entry.requests_this_hour,
            "minute_limit": config.requests_per_minute,
            "hour_limit": config.requests_per_hour,
            "minute_reset_at": entry.minute_reset_at.isoformat(),
            "hour_reset_at": entry.hour_reset_at.isoformat(),
        }

    def reset_user(self, user_id: str) -> bool:
        """Reset rate limit for a user."""
        if user_id in self._entries:
            del self._entries[user_id]
            return True
        return False

    def get_all_stats(self) -> dict[str, Any]:
        """Get stats for all users."""
        return {
            "total_users": len(self._entries),
            "users": {
                uid: self.get_user_stats(uid)
                for uid in self._entries
            },
        }


# Global rate limiter
rate_limiter = RateLimiter()


# ---------------------------------------------------------------------------
# Input Validation Middleware
# ---------------------------------------------------------------------------

class InputValidationError(Exception):
    """Exception for input validation errors."""

    def __init__(self, message: str, field: str | None = None, code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.field = field
        self.code = code


@dataclass
class ValidationResult:
    """Result of input validation."""
    valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    sanitized_data: dict[str, Any] = field(default_factory=dict)


class InputValidator:
    """Input validation and sanitization."""

    # Max lengths for common fields
    MAX_LENGTHS = {
        "patient_id": 100,
        "question": 1000,
        "notes": 2000,
        "reviewer_id": 100,
        "search_query": 500,
    }

    # Patterns to sanitize
    SANITIZE_PATTERNS = [
        (r"<script.*?</script>", "[REDACTED]"),
        (r"javascript:", "[REDACTED]"),
        (r"on\w+\s*=", "[REDACTED]"),
        (r"<iframe.*?</iframe>", "[REDACTED]"),
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|FETCH|DECLARE|TRUNCATE)\b)",
        r"(--|;|'|\"|\bOR\b\s+\b1\s*=\s*1\b)",
        r"(\bAND\b\s+\b1\s*=\s*1\b)",
    ]

    @classmethod
    def validate_string(
        cls,
        value: str,
        field_name: str,
        min_length: int = 1,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
    ) -> tuple[bool, str | None]:
        """Validate a string field."""
        if not required and (value is None or value == ""):
            return True, None

        if required and (value is None or value == ""):
            return False, f"{field_name} is required"

        if not isinstance(value, str):
            return False, f"{field_name} must be a string"

        if len(value) < min_length:
            return False, f"{field_name} must be at least {min_length} characters"

        max_len = max_length or cls.MAX_LENGTHS.get(field_name, 10000)
        if len(value) > max_len:
            return False, f"{field_name} must be at most {max_len} characters"

        if pattern and not re.match(pattern, value):
            return False, f"{field_name} format is invalid"

        return True, None

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return value

        sanitized = value

        # Apply sanitize patterns
        for pattern, replacement in cls.SANITIZE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE | re.DOTALL)

        # Check for SQL injection
        for sql_pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(sql_pattern, sanitized, re.IGNORECASE):
                raise InputValidationError(
                    "Potentially dangerous input detected",
                    code="SQL_INJECTION_DETECTED"
                )

        return sanitized.strip()

    @classmethod
    def validate_patient_id(cls, patient_id: str) -> tuple[bool, str | None]:
        """Validate a patient ID."""
        if not patient_id:
            return False, "Patient ID is required"

        if len(patient_id) > cls.MAX_LENGTHS["patient_id"]:
            return False, f"Patient ID must be at most {cls.MAX_LENGTHS['patient_id']} characters"

        # Allow alphanumeric, hyphens, underscores
        if not re.match(r"^[a-zA-Z0-9\-_]+$", patient_id):
            return False, "Patient ID contains invalid characters"

        return True, None

    @classmethod
    def validate_question(cls, question: str) -> tuple[bool, str | None]:
        """Validate an investigation question."""
        return cls.validate_string(
            question,
            "question",
            min_length=3,
            max_length=cls.MAX_LENGTHS["question"],
        )

    @classmethod
    def validate_investigation_request(cls, patient_id: str, question: str) -> ValidationResult:
        """Validate an investigation request."""
        errors = []
        sanitized = {}

        # Validate patient ID
        valid, error = cls.validate_patient_id(patient_id)
        if not valid:
            errors.append({"field": "patient_id", "message": error})
        else:
            try:
                sanitized["patient_id"] = cls.sanitize_string(patient_id)
            except InputValidationError as e:
                errors.append({"field": "patient_id", "message": str(e), "code": e.code})

        # Validate question
        valid, error = cls.validate_question(question)
        if not valid:
            errors.append({"field": "question", "message": error})
        else:
            try:
                sanitized["question"] = cls.sanitize_string(question)
            except InputValidationError as e:
                errors.append({"field": "question", "message": str(e), "code": e.code})

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized,
        )


# Global input validator
input_validator = InputValidator()


# ---------------------------------------------------------------------------
# Enhanced Safety Gate with Rate Limiting
# ---------------------------------------------------------------------------

class EnhancedSafetyGate:
    """Safety gate with rate limiting and input validation."""

    def __init__(self):
        self.rate_limiter = rate_limiter
        self.input_validator = input_validator

    def check_request(
        self,
        user_id: str,
        user_role: UserRole,
        patient_id: str,
        question: str,
    ) -> dict[str, Any]:
        """Comprehensive request check including rate limiting and validation."""
        errors = []

        # Rate limit check
        rate_check = self.rate_limiter.check_rate_limit(user_id, user_role)
        if not rate_check["allowed"]:
            errors.append({
                "type": "rate_limit",
                "message": rate_check["reason"],
                "retry_after_seconds": rate_check["retry_after_seconds"],
            })

        # Input validation
        validation = self.input_validator.validate_investigation_request(patient_id, question)
        if not validation.valid:
            errors.extend(validation.errors)

        return {
            "allowed": len(errors) == 0,
            "errors": errors,
            "sanitized_data": validation.sanitized_data if validation.valid else None,
            "rate_limit": rate_check,
        }

    def get_user_rate_stats(self, user_id: str) -> dict[str, Any] | None:
        """Get rate limit stats for a user."""
        return self.rate_limiter.get_user_stats(user_id)


# Global enhanced safety gate
enhanced_safety_gate = EnhancedSafetyGate()
