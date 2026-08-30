"""
Error Handling and Resilience Module

This module provides error handling and resilience patterns:
1. Circuit breakers for fault tolerance
2. Retry logic with exponential backoff
3. Fallback mechanisms
4. Graceful degradation
5. Health checks
6. Error classification and handling
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("aegis.resilience")


class ErrorSeverity(StrEnum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(StrEnum):
    """Error categories."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    INTERNAL = "internal"
    TIMEOUT = "timeout"


@dataclass
class AppError:
    """Application error with context."""
    error_id: str = field(default_factory=lambda: str(uuid4())[:8])
    category: ErrorCategory = ErrorCategory.INTERNAL
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    recoverable: bool = True
    retry_after: float | None = None


class ErrorHandler:
    """Centralized error handler."""

    def __init__(self):
        self.errors: list[AppError] = []
        self.max_errors = 1000

    def handle(self, error: Exception, context: dict[str, Any] = None) -> AppError:
        """Handle an error and return an AppError."""
        app_error = self._classify_error(error, context)
        self.errors.append(app_error)

        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors // 2:]

        # Log the error
        self._log_error(app_error)

        return app_error

    def _classify_error(self, error: Exception, context: dict[str, Any] = None) -> AppError:
        """Classify an error into categories."""
        error_type = type(error).__name__
        error_message = str(error)

        # Classify based on error type
        if isinstance(error, ValueError):
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
        elif isinstance(error, PermissionError):
            category = ErrorCategory.AUTHORIZATION
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, FileNotFoundError):
            category = ErrorCategory.NOT_FOUND
            severity = ErrorSeverity.LOW
        elif isinstance(error, TimeoutError):
            category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, ConnectionError):
            category = ErrorCategory.EXTERNAL_SERVICE
            severity = ErrorSeverity.HIGH
        elif isinstance(error, MemoryError):
            category = ErrorCategory.INTERNAL
            severity = ErrorSeverity.CRITICAL
        else:
            category = ErrorCategory.INTERNAL
            severity = ErrorSeverity.MEDIUM

        return AppError(
            category=category,
            severity=severity,
            message=error_message,
            details={
                "error_type": error_type,
                "context": context or {},
            },
            recoverable=severity != ErrorSeverity.CRITICAL,
        )

    def _log_error(self, error: AppError) -> None:
        """Log an error."""
        log_message = f"[{error.category.value}] {error.message}"

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def get_errors(self, category: ErrorCategory = None, limit: int = 100) -> list[AppError]:
        """Get errors with optional filtering."""
        errors = self.errors
        if category:
            errors = [e for e in errors if e.category == category]
        return errors[-limit:]

    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics."""
        stats = {
            "total": len(self.errors),
            "by_category": {},
            "by_severity": {},
        }

        for error in self.errors:
            stats["by_category"][error.category.value] = stats["by_category"].get(error.category.value, 0) + 1
            stats["by_severity"][error.severity.value] = stats["by_severity"].get(error.severity.value, 0) + 1

        return stats


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                self.success_count = 0
            else:
                raise RuntimeError(f"Circuit breaker {self.name} is open")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful execution."""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        else:
            self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "half_open":
            self.state = "open"
        elif self.failure_count >= self.failure_threshold:
            self.state = "open"

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
        }


class RetryHandler:
    """Retry handler with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {delay:.1f}s: {e}")
                    await asyncio.sleep(delay)

        raise last_exception


class FallbackChain:
    """Chain of fallback functions."""

    def __init__(self, name: str):
        self.name = name
        self.fallbacks: list[tuple[str, Callable]] = []

    def add(self, name: str, func: Callable) -> FallbackChain:
        """Add a fallback function."""
        self.fallbacks.append((name, func))
        return self

    async def execute(self, *args, **kwargs) -> Any:
        """Execute fallback chain until one succeeds."""
        last_exception = None

        for name, func in self.fallbacks:
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback {name} failed: {e}")
                last_exception = e

        raise last_exception


class HealthChecker:
    """Health check system."""

    def __init__(self):
        self.checks: dict[str, Callable] = {}
        self.results: dict[str, dict[str, Any]] = {}

    def register(self, name: str, check_func: Callable) -> None:
        """Register a health check."""
        self.checks[name] = check_func

    async def check_all(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {}
        all_healthy = True

        for name, check_func in self.checks.items():
            try:
                start = time.perf_counter()
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                duration_ms = (time.perf_counter() - start) * 1000

                results[name] = {
                    "status": "healthy",
                    "duration_ms": round(duration_ms, 2),
                    "details": result if isinstance(result, dict) else {},
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                all_healthy = False

        self.results = results
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": results,
        }

    async def check(self, name: str) -> dict[str, Any]:
        """Run a specific health check."""
        if name not in self.checks:
            return {"status": "unknown", "error": f"Check {name} not found"}

        try:
            start = time.perf_counter()
            check_func = self.checks[name]
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            duration_ms = (time.perf_counter() - start) * 1000

            return {
                "status": "healthy",
                "duration_ms": round(duration_ms, 2),
                "details": result if isinstance(result, dict) else {},
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


class GracefulDegradation:
    """Graceful degradation handler."""

    def __init__(self):
        self.degradation_level = 0  # 0 = normal, 1 = degraded, 2 = severely degraded
        self.disabled_features: set[str] = set()

    def degrade(self, level: int, features: list[str] = None) -> None:
        """Degrade system performance."""
        self.degradation_level = min(level, 2)
        if features:
            self.disabled_features.update(features)

    def restore(self, level: int = 0) -> None:
        """Restore system performance."""
        self.degradation_level = max(level, 0)
        if level == 0:
            self.disabled_features.clear()

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return feature not in self.disabled_features

    def get_status(self) -> dict[str, Any]:
        """Get degradation status."""
        return {
            "level": self.degradation_level,
            "disabled_features": list(self.disabled_features),
        }


# Global instances
error_handler = ErrorHandler()
health_checker = HealthChecker()
graceful_degradation = GracefulDegradation()
