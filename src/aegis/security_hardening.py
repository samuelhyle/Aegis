"""
Security Hardening Module

This module provides security enhancements for the AEGIS system:
1. Input validation and sanitization
2. SQL injection prevention
3. XSS prevention
4. Path traversal prevention
5. Rate limiting enhancements
6. Audit logging
7. Secrets management
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SecurityLevel(StrEnum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """A security event."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    severity: SecurityLevel = SecurityLevel.MEDIUM
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str = ""
    ip_address: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


class InputValidator:
    """Validates and sanitizes user input."""

    # Dangerous patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|;|/\*|\*/)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\b\s+['\"].*['\"])",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<form",
        r"<input",
        r"<textarea",
        r"<button",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        r"%252e%252e",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`.*`",
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
        for pattern in cls.SQL_PATTERNS:
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
    def check_command_injection(cls, value: str) -> bool:
        """Check for command injection attempts."""
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
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

        if cls.check_command_injection(value):
            raise ValueError(f"Potential command injection in {field_name}")

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

    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate email format."""
        value = cls.sanitize_string(value, max_length=254)
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise ValueError("Invalid email format")
        return value

    @classmethod
    def validate_url(cls, value: str) -> str:
        """Validate URL format."""
        value = cls.sanitize_string(value, max_length=2000)
        if not re.match(r"^https?://", value):
            raise ValueError("Invalid URL format")
        return value


class SecurityAuditor:
    """Audits security events."""

    def __init__(self):
        self.events: list[SecurityEvent] = []
        self.max_events = 10000

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        self.events.append(event)

        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events // 2:]

    def log_auth_failure(self, ip_address: str, reason: str, user_id: str = "") -> None:
        """Log an authentication failure."""
        self.log_event(SecurityEvent(
            event_type="auth_failure",
            severity=SecurityLevel.MEDIUM,
            ip_address=ip_address,
            user_id=user_id,
            details={"reason": reason},
        ))

    def log_input_validation_failure(self, ip_address: str, field: str, value: str) -> None:
        """Log an input validation failure."""
        self.log_event(SecurityEvent(
            event_type="input_validation_failure",
            severity=SecurityLevel.HIGH,
            ip_address=ip_address,
            details={"field": field, "value": value[:100]},
            blocked=True,
        ))

    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str) -> None:
        """Log a rate limit exceeded event."""
        self.log_event(SecurityEvent(
            event_type="rate_limit_exceeded",
            severity=SecurityLevel.MEDIUM,
            ip_address=ip_address,
            details={"endpoint": endpoint},
            blocked=True,
        ))

    def log_suspicious_activity(self, ip_address: str, activity: str) -> None:
        """Log suspicious activity."""
        self.log_event(SecurityEvent(
            event_type="suspicious_activity",
            severity=SecurityLevel.HIGH,
            ip_address=ip_address,
            details={"activity": activity},
        ))

    def get_events(self, severity: SecurityLevel | None = None, limit: int = 100) -> list[SecurityEvent]:
        """Get security events."""
        events = self.events
        if severity:
            events = [e for e in events if e.severity == severity]
        return events[-limit:]

    def get_blocked_events(self, limit: int = 100) -> list[SecurityEvent]:
        """Get blocked events."""
        return [e for e in self.events if e.blocked][-limit:]

    def get_events_by_ip(self, ip_address: str, limit: int = 100) -> list[SecurityEvent]:
        """Get events by IP address."""
        return [e for e in self.events if e.ip_address == ip_address][-limit:]


class SecretsManager:
    """Manages secrets securely."""

    def __init__(self):
        self._secrets: dict[str, str] = {}
        self._load_from_env()

    def _load_from_env(self):
        """Load secrets from environment variables."""
        secret_prefixes = ["AEGIS_", "OPENAI_", "DATABASE_", "REDIS_"]
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in secret_prefixes):
                if any(sensitive in key for sensitive in ["SECRET", "KEY", "PASSWORD", "TOKEN"]):
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

    def validate_secret_strength(self, key: str) -> bool:
        """Validate secret strength."""
        value = self._secrets.get(key, "")
        if len(value) < 16:
            return False
        if not re.search(r"[A-Z]", value):
            return False
        if not re.search(r"[a-z]", value):
            return False
        if not re.search(r"[0-9]", value):
            return False
        return True


class EncryptionHelper:
    """Helper for encryption operations."""

    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash a password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for password hashing
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=100000,
        )

        return key.hex(), salt

    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify a password against a hash."""
        key, _ = EncryptionHelper.hash_password(password, salt)
        return hmac.compare_digest(key, hashed)

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return f"aegis_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data for integrity checking."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


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
input_validator = InputValidator()
security_auditor = SecurityAuditor()
secrets_manager = SecretsManager()
encryption_helper = EncryptionHelper()
