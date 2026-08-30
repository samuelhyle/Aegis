from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("aegis.resilience")


class CircuitState(StrEnum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before half-open
    success_threshold: int = 3  # Successes to close from half-open
    timeout: float = 30.0  # Request timeout


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()
        self._lock = asyncio.Lock()

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state.state == CircuitState.OPEN:
                if self._should_try_reset():
                    self.state.state = CircuitState.HALF_OPEN
                    self.state.success_count = 0
                    logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} is OPEN"
                    )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            if self.state.state == CircuitState.HALF_OPEN:
                self.state.success_count += 1
                if self.state.success_count >= self.config.success_threshold:
                    self.state.state = CircuitState.CLOSED
                    self.state.failure_count = 0
                    logger.info(f"Circuit {self.name} CLOSED")
            else:
                self.state.failure_count = max(0, self.state.failure_count - 1)

    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self.state.failure_count += 1
            self.state.last_failure_time = time.time()

            if self.state.state == CircuitState.HALF_OPEN:
                self.state.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name} OPEN (half-open failure)")
            elif self.state.failure_count >= self.config.failure_threshold:
                self.state.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit {self.name} OPEN (threshold {self.config.failure_threshold})"
                )

    def _should_try_reset(self) -> bool:
        """Check if we should try to reset the circuit."""
        return (
            time.time() - self.state.last_failure_time
            >= self.config.recovery_timeout
        )

    def get_state(self) -> dict[str, Any]:
        """Get circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure": self.state.last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""
    pass


async def retry_async(
    func: Callable,
    config: RetryConfig | None = None,
    *args,
    **kwargs,
) -> Any:
    """Retry an async function with exponential backoff."""
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < config.max_retries:
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay,
                )
                if config.jitter:
                    import random
                    delay *= 0.5 + random.random()
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} after {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)

    raise RetryExhaustedError(
        f"All {config.max_retries} retries exhausted"
    ) from last_exception


def retry_sync(
    func: Callable,
    config: RetryConfig | None = None,
    *args,
    **kwargs,
) -> Any:
    """Retry a sync function with exponential backoff."""
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < config.max_retries:
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay,
                )
                if config.jitter:
                    import random
                    delay *= 0.5 + random.random()
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} after {delay:.1f}s: {e}"
                )
                time.sleep(delay)

    raise RetryExhaustedError(
        f"All {config.max_retries} retries exhausted"
    ) from last_exception


class FallbackChain:
    """Chain of fallback functions to try in order."""

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
    """Health check system for dependencies."""

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
                    "details": result,
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
                "details": result,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


class Bulkhead:
    """Bulkhead pattern for limiting concurrent executions."""

    def __init__(self, name: str, max_concurrent: int = 10, max_queue: int = 100):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_size = 0
        self.active_count = 0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection."""
        if self.queue_size >= self.max_queue:
            raise BulkheadFullError(
                f"Bulkhead {self.name} queue full ({self.max_queue})"
            )

        self.queue_size += 1
        try:
            async with self.semaphore:
                self.active_count += 1
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                finally:
                    self.active_count -= 1
        finally:
            self.queue_size -= 1

    def get_state(self) -> dict[str, Any]:
        """Get bulkhead state."""
        return {
            "name": self.name,
            "active": self.active_count,
            "queued": self.queue_size,
            "max_concurrent": self.max_concurrent,
            "max_queue": self.max_queue,
        }


class BulkheadFullError(Exception):
    """Raised when bulkhead is full."""
    pass


class Timeout:
    """Timeout wrapper for operations."""

    def __init__(self, seconds: float, operation_name: str = "operation"):
        self.seconds = seconds
        self.operation_name = operation_name

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.seconds,
                )
            else:
                return func(*args, **kwargs)
        except TimeoutError:
            raise TimeoutError(
                f"Operation {self.operation_name} timed out after {self.seconds}s"
            )


# Global instances
circuit_breakers: dict[str, CircuitBreaker] = {}
health_checker = HealthChecker()


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(name, config)
    return circuit_breakers[name]


def get_all_circuit_breaker_states() -> list[dict[str, Any]]:
    """Get states of all circuit breakers."""
    return [cb.get_state() for cb in circuit_breakers.values()]
