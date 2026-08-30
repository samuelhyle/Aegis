from __future__ import annotations

import logging
import os
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("aegis.security")


class AuditEventType(StrEnum):
    """Types of audit events."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    INVESTIGATION = "investigation"
    REVIEW = "review"
    ADMIN_ACTION = "admin_action"
    SECURITY_EVENT = "security_event"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    CONFIG_CHANGE = "config_change"


class AuditSeverity(StrEnum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """An audit event record."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: AuditEventType = AuditEventType.DATA_ACCESS
    severity: AuditSeverity = AuditSeverity.INFO
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = ""
    user_ip: str = ""
    resource_type: str = ""
    resource_id: str = ""
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(self, log_file: str | None = None):
        self.events: list[AuditEvent] = []
        self.log_file = log_file
        self._setup_logger()

    def _setup_logger(self):
        """Setup audit logger."""
        self.logger = logging.getLogger("aegis.audit")
        self.logger.setLevel(logging.INFO)

        if self.log_file:
            handler = logging.FileHandler(self.log_file)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            self.logger.addHandler(handler)

    def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
        self.events.append(event)

        # Log to file
        self.logger.info(
            f"[{event.event_type.value}] "
            f"user={event.user_id} "
            f"resource={event.resource_type}/{event.resource_id} "
            f"action={event.action} "
            f"success={event.success}"
        )

        # Keep only last 10000 events in memory
        if len(self.events) > 10000:
            self.events = self.events[-5000:]

    def log_auth_success(self, user_id: str, user_ip: str, method: str) -> None:
        """Log successful authentication."""
        self.log(AuditEvent(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id=user_id,
            user_ip=user_ip,
            action=f"login_{method}",
            details={"method": method},
        ))

    def log_auth_failure(self, user_ip: str, reason: str, username: str = "") -> None:
        """Log failed authentication."""
        self.log(AuditEvent(
            event_type=AuditEventType.AUTH_FAILURE,
            severity=AuditSeverity.WARNING,
            user_ip=user_ip,
            action="login_failed",
            details={"reason": reason, "username": username},
            success=False,
        ))

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
    ) -> None:
        """Log data access."""
        self.log(AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
        ))

    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        changes: dict[str, Any] | None = None,
    ) -> None:
        """Log data modification."""
        self.log(AuditEvent(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details={"changes": changes or {}},
        ))

    def log_investigation(
        self,
        user_id: str,
        patient_id: str,
        question: str,
        trace_id: str,
    ) -> None:
        """Log investigation execution."""
        self.log(AuditEvent(
            event_type=AuditEventType.INVESTIGATION,
            user_id=user_id,
            resource_type="investigation",
            resource_id=trace_id,
            action="run_investigation",
            details={
                "patient_id": patient_id,
                "question": question[:200],
            },
        ))

    def log_review(
        self,
        user_id: str,
        trace_id: str,
        decision: str,
        notes: str = "",
    ) -> None:
        """Log review action."""
        self.log(AuditEvent(
            event_type=AuditEventType.REVIEW,
            user_id=user_id,
            resource_type="investigation",
            resource_id=trace_id,
            action=f"review_{decision}",
            details={"decision": decision, "notes": notes[:200]},
        ))

    def log_security_event(
        self,
        event_type: str,
        user_id: str = "",
        user_ip: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log security-related event."""
        self.log(AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            user_ip=user_ip,
            action=event_type,
            details=details or {},
        ))

    def get_events(
        self,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get audit events with optional filtering."""
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        return events[-limit:]

    def get_security_events(self, limit: int = 50) -> list[AuditEvent]:
        """Get recent security events."""
        return [
            e for e in self.events
            if e.event_type in [
                AuditEventType.AUTH_FAILURE,
                AuditEventType.SECURITY_EVENT,
            ]
        ][-limit:]


class InputSanitizer:
    """Input sanitization and validation."""

    # Patterns for dangerous content
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|;|/\*|\*/)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            return str(value)[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # Limit length
        value = value[:max_length]

        # Strip whitespace
        value = value.strip()

        return value

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection."""
        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for potential XSS."""
        value_lower = value.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """Check for path traversal attempts."""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def validate_input(cls, value: str, field_name: str = "input") -> str:
        """Validate and sanitize input, raising on dangerous content."""
        value = cls.sanitize_string(value)

        if cls.check_sql_injection(value):
            raise ValueError(f"Potential SQL injection in {field_name}")

        if cls.check_xss(value):
            raise ValueError(f"Potential XSS in {field_name}")

        if cls.check_path_traversal(value):
            raise ValueError(f"Potential path traversal in {field_name}")

        return value

    @classmethod
    def validate_patient_id(cls, value: str) -> str:
        """Validate patient ID format."""
        value = cls.sanitize_string(value, max_length=100)
        if not re.match(r"^[a-zA-Z0-9\-_]+$", value):
            raise ValueError("Invalid patient ID format")
        return value

    @classmethod
    def validate_question(cls, value: str) -> str:
        """Validate investigation question."""
        value = cls.sanitize_string(value, max_length=2000)
        if len(value) < 3:
            raise ValueError("Question too short")
        return value


class SecretsManager:
    """Secrets management for sensitive configuration."""

    def __init__(self):
        self._secrets: dict[str, str] = {}
        self._load_from_env()

    def _load_from_env(self):
        """Load secrets from environment variables."""
        secret_prefixes = ["AEGIS_", "OPENAI_", "DATABASE_", "REDIS_"]
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in secret_prefixes):
                if "SECRET" in key or "KEY" in key or "PASSWORD" in key or "TOKEN" in key:
                    self._secrets[key] = value

    def get(self, key: str, default: str = "") -> str:
        """Get a secret value."""
        return self._secrets.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set a secret value."""
        self._secrets[key] = value

    def get_masked(self, key: str) -> str:
        """Get a masked version of the secret."""
        value = self._secrets.get(key, "")
        if len(value) <= 4:
            return "****"
        return f"{value[:2]}...{value[-2:]}"

    def rotate(self, key: str) -> str:
        """Generate a new secret value."""
        new_value = secrets.token_urlsafe(32)
        self._secrets[key] = new_value
        return new_value


class SecurityHeaders:
    """Security headers for HTTP responses."""

    @staticmethod
    def get_headers() -> dict[str, str]:
        """Get security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }


class RateLimitConfig:
    """Rate limit configuration."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size


# Global instances
audit_logger = AuditLogger()
secrets_manager = SecretsManager()
input_sanitizer = InputSanitizer()
