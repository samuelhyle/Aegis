"""
Tests for Optimization, Security Hardening, and Resilience modules
"""

import os

import pytest

# Set test environment
os.environ["AEGIS_AUTH_DISABLED"] = "true"
os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"

from aegis.optimization import (
    BatchProcessor,
    ConnectionPool,
    MemoryOptimizer,
    OptimizedCache,
    PerformanceStats,
)
from aegis.resilience_hardening import (
    AppError,
    CircuitBreaker,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    FallbackChain,
    GracefulDegradation,
    HealthChecker,
    RetryHandler,
)
from aegis.security_hardening import (
    EncryptionHelper,
    InputValidator,
    SecretsManager,
    SecurityAuditor,
    SecurityEvent,
    SecurityHeaders,
    SecurityLevel,
)

# ============================================================================
# Test Optimization
# ============================================================================

class TestOptimizedCache:
    """Tests for OptimizedCache."""

    def test_set_and_get(self):
        """Test basic set/get."""
        cache = OptimizedCache(max_size=10, default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = OptimizedCache(max_size=10, default_ttl=1)
        cache.set("key1", "value1")
        import time
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Test LRU eviction."""
        cache = OptimizedCache(max_size=3, default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Evicts key1
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_get_or_set(self):
        """Test get_or_set pattern."""
        cache = OptimizedCache(max_size=10, default_ttl=60)
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "computed"

        result1 = cache.get_or_set("key", factory)
        result2 = cache.get_or_set("key", factory)
        assert result1 == result2 == "computed"
        assert call_count == 1

    def test_invalidate_pattern(self):
        """Test pattern invalidation."""
        cache = OptimizedCache(max_size=10, default_ttl=60)
        cache.set("user:1:name", "Alice")
        cache.set("user:2:name", "Bob")
        cache.set("other:key", "value")

        count = cache.invalidate_pattern("user:")
        assert count == 2
        assert cache.get("other:key") == "value"

    def test_stats(self):
        """Test cache statistics."""
        cache = OptimizedCache(max_size=10, default_ttl=60)
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        assert cache.stats.hit_rate == 0.5


class TestPerformanceStats:
    """Tests for PerformanceStats."""

    def test_record_hit(self):
        """Test recording cache hit."""
        stats = PerformanceStats()
        stats.record_hit()
        assert stats.cache_hits == 1

    def test_record_miss(self):
        """Test recording cache miss."""
        stats = PerformanceStats()
        stats.record_miss()
        assert stats.cache_misses == 1

    def test_record_query(self):
        """Test recording query."""
        stats = PerformanceStats()
        stats.record_query(100.0)
        assert stats.total_queries == 1
        assert stats.avg_query_time_ms == 100.0

    def test_hit_rate(self):
        """Test hit rate calculation."""
        stats = PerformanceStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        assert stats.hit_rate == 2 / 3


class TestBatchProcessor:
    """Tests for BatchProcessor."""

    def test_process(self):
        """Test batch processing."""
        processor = BatchProcessor(batch_size=2)
        items = [1, 2, 3, 4, 5]
        results = processor.process(items, lambda batch: [x * 2 for x in batch])
        assert results == [2, 4, 6, 8, 10]


class TestMemoryOptimizer:
    """Tests for MemoryOptimizer."""

    def test_chunk_list(self):
        """Test list chunking."""
        data = [1, 2, 3, 4, 5, 6, 7]
        chunks = MemoryOptimizer.chunk_list(data, chunk_size=3)
        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]
        assert chunks[1] == [4, 5, 6]
        assert chunks[2] == [7]


class TestConnectionPool:
    """Tests for ConnectionPool."""

    def test_acquire_and_release(self):
        """Test acquire and release."""
        pool = ConnectionPool(max_size=2)
        conn1 = pool.acquire()
        pool.acquire()
        assert len(pool.pool) == 2

        pool.release(conn1)
        conn3 = pool.acquire()
        assert conn3 is conn1

    def test_pool_exhausted(self):
        """Test pool exhaustion."""
        pool = ConnectionPool(max_size=1)
        pool.acquire()
        with pytest.raises(RuntimeError, match="exhausted"):
            pool.acquire()


# ============================================================================
# Test Security Hardening
# ============================================================================

class TestInputValidator:
    """Tests for InputValidator."""

    def test_sanitize_string(self):
        """Test string sanitization."""
        result = InputValidator.sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_sanitize_null_bytes(self):
        """Test null byte removal."""
        result = InputValidator.sanitize_string("hello\x00world")
        assert result == "helloworld"

    def test_check_sql_injection(self):
        """Test SQL injection detection."""
        assert InputValidator.check_sql_injection("SELECT * FROM users") is True
        assert InputValidator.check_sql_injection("normal text") is False

    def test_check_xss(self):
        """Test XSS detection."""
        assert InputValidator.check_xss("<script>alert(1)</script>") is True
        assert InputValidator.check_xss("normal text") is False

    def test_check_path_traversal(self):
        """Test path traversal detection."""
        assert InputValidator.check_path_traversal("../etc/passwd") is True
        assert InputValidator.check_path_traversal("normal/path") is False

    def test_check_command_injection(self):
        """Test command injection detection."""
        assert InputValidator.check_command_injection("ls; rm -rf /") is True
        assert InputValidator.check_command_injection("normal text") is False

    def test_validate_patient_id(self):
        """Test patient ID validation."""
        assert InputValidator.validate_patient_id("patient-123") == "patient-123"
        with pytest.raises(ValueError):
            InputValidator.validate_patient_id("patient@123")

    def test_validate_question(self):
        """Test question validation."""
        assert InputValidator.validate_question("What is the condition?") == "What is the condition?"
        with pytest.raises(ValueError):
            InputValidator.validate_question("ab")

    def test_validate_email(self):
        """Test email validation."""
        assert InputValidator.validate_email("test@example.com") == "test@example.com"
        with pytest.raises(ValueError):
            InputValidator.validate_email("invalid-email")

    def test_validate_url(self):
        """Test URL validation."""
        assert InputValidator.validate_url("https://example.com") == "https://example.com"
        with pytest.raises(ValueError):
            InputValidator.validate_url("not-a-url")


class TestSecurityAuditor:
    """Tests for SecurityAuditor."""

    def test_log_event(self):
        """Test event logging."""
        auditor = SecurityAuditor()
        auditor.log_event(SecurityEvent(event_type="test"))
        assert len(auditor.events) == 1

    def test_log_auth_failure(self):
        """Test auth failure logging."""
        auditor = SecurityAuditor()
        auditor.log_auth_failure("127.0.0.1", "invalid_key")
        assert len(auditor.events) == 1
        assert auditor.events[0].event_type == "auth_failure"

    def test_log_input_validation_failure(self):
        """Test input validation failure logging."""
        auditor = SecurityAuditor()
        auditor.log_input_validation_failure("127.0.0.1", "query", "SELECT *")
        assert len(auditor.events) == 1
        assert auditor.events[0].blocked is True

    def test_get_events_by_severity(self):
        """Test getting events by severity."""
        auditor = SecurityAuditor()
        auditor.log_event(SecurityEvent(severity=SecurityLevel.LOW))
        auditor.log_event(SecurityEvent(severity=SecurityLevel.HIGH))
        auditor.log_event(SecurityEvent(severity=SecurityLevel.HIGH))

        high_events = auditor.get_events(severity=SecurityLevel.HIGH)
        assert len(high_events) == 2

    def test_get_blocked_events(self):
        """Test getting blocked events."""
        auditor = SecurityAuditor()
        auditor.log_event(SecurityEvent(blocked=True))
        auditor.log_event(SecurityEvent(blocked=False))
        auditor.log_event(SecurityEvent(blocked=True))

        blocked = auditor.get_blocked_events()
        assert len(blocked) == 2


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_set_and_get(self):
        """Test set and get."""
        manager = SecretsManager()
        manager.set("TEST_SECRET", "value123")
        assert manager.get("TEST_SECRET") == "value123"

    def test_get_masked(self):
        """Test masked value."""
        manager = SecretsManager()
        manager.set("TEST_SECRET", "abcdefghijklmnop")
        assert manager.get_masked("TEST_SECRET") == "ab...op"

    def test_rotate(self):
        """Test secret rotation."""
        manager = SecretsManager()
        manager.set("TEST_SECRET", "old_value")
        new_value = manager.rotate("TEST_SECRET")
        assert new_value != "old_value"
        assert manager.get("TEST_SECRET") == new_value


class TestEncryptionHelper:
    """Tests for EncryptionHelper."""

    def test_hash_password(self):
        """Test password hashing."""
        hashed, salt = EncryptionHelper.hash_password("password123")
        assert len(hashed) > 0
        assert len(salt) > 0

    def test_verify_password(self):
        """Test password verification."""
        hashed, salt = EncryptionHelper.hash_password("password123")
        assert EncryptionHelper.verify_password("password123", hashed, salt) is True
        assert EncryptionHelper.verify_password("wrong_password", hashed, salt) is False

    def test_generate_api_key(self):
        """Test API key generation."""
        key = EncryptionHelper.generate_api_key()
        assert key.startswith("aegis_")
        assert len(key) > 20

    def test_hash_data(self):
        """Test data hashing."""
        hash1 = EncryptionHelper.hash_data("test data")
        hash2 = EncryptionHelper.hash_data("test data")
        hash3 = EncryptionHelper.hash_data("different data")
        assert hash1 == hash2
        assert hash1 != hash3


class TestSecurityHeaders:
    """Tests for SecurityHeaders."""

    def test_get_headers(self):
        """Test getting security headers."""
        headers = SecurityHeaders.get_headers()
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers


# ============================================================================
# Test Resilience Hardening
# ============================================================================

class TestErrorHandler:
    """Tests for ErrorHandler."""

    def test_handle_validation_error(self):
        """Test handling validation error."""
        handler = ErrorHandler()
        error = handler.handle(ValueError("Invalid input"))
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW

    def test_handle_timeout_error(self):
        """Test handling timeout error."""
        handler = ErrorHandler()
        error = handler.handle(TimeoutError("Request timed out"))
        assert error.category == ErrorCategory.TIMEOUT

    def test_get_error_stats(self):
        """Test error statistics."""
        handler = ErrorHandler()
        handler.handle(ValueError("Error 1"))
        handler.handle(ValueError("Error 2"))
        handler.handle(TimeoutError("Timeout"))

        stats = handler.get_error_stats()
        assert stats["total"] == 3
        assert stats["by_category"]["validation"] == 2
        assert stats["by_category"]["timeout"] == 1


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_closed_state(self):
        """Test closed state."""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def success():
            return "ok"

        result = await cb.execute(success)
        assert result == "ok"
        assert cb.state == "closed"

    @pytest.mark.asyncio
    async def test_opens_after_failures(self):
        """Test circuit opens after failures."""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def fail():
            raise ValueError("fail")

        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.execute(fail)

        assert cb.state == "open"

    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        """Test half-open recovery."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)

        async def fail():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.execute(fail)

        assert cb.state == "open"

        # Wait for recovery
        import asyncio
        await asyncio.sleep(0.2)

        async def success():
            return "ok"

        # Should be half-open now
        result = await cb.execute(success)
        assert result == "ok"


class TestRetryHandler:
    """Tests for RetryHandler."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Test success on first try."""
        handler = RetryHandler(max_retries=3, base_delay=0.01)
        call_count = 0

        async def success():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await handler.execute(success)
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test success after retries."""
        handler = RetryHandler(max_retries=3, base_delay=0.01)
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not ready")
            return "ok"

        result = await handler.execute(flaky)
        assert result == "ok"
        assert call_count == 3


class TestFallbackChain:
    """Tests for FallbackChain."""

    @pytest.mark.asyncio
    async def test_first_succeeds(self):
        """Test first fallback succeeds."""
        chain = FallbackChain("test")
        chain.add("primary", lambda: "primary")
        chain.add("secondary", lambda: "secondary")

        result = await chain.execute()
        assert result == "primary"

    @pytest.mark.asyncio
    async def test_fallback_to_secondary(self):
        """Test fallback to secondary."""
        def failing():
            raise ValueError("fail")

        chain = FallbackChain("test")
        chain.add("primary", failing)
        chain.add("secondary", lambda: "secondary")

        result = await chain.execute()
        assert result == "secondary"


class TestHealthChecker:
    """Tests for HealthChecker."""

    @pytest.mark.asyncio
    async def test_check_all_healthy(self):
        """Test all checks healthy."""
        checker = HealthChecker()
        checker.register("service1", lambda: {"status": "ok"})
        checker.register("service2", lambda: {"status": "ok"})

        result = await checker.check_all()
        assert result["status"] == "healthy"
        assert len(result["checks"]) == 2

    @pytest.mark.asyncio
    async def test_check_unhealthy(self):
        """Test unhealthy check."""
        checker = HealthChecker()
        checker.register("healthy", lambda: {"status": "ok"})
        checker.register("unhealthy", lambda: 1 / 0)

        result = await checker.check_all()
        assert result["status"] == "degraded"


class TestGracefulDegradation:
    """Tests for GracefulDegradation."""

    def test_degrade(self):
        """Test degradation."""
        gd = GracefulDegradation()
        gd.degrade(1, ["feature1", "feature2"])
        assert gd.degradation_level == 1
        assert gd.is_feature_enabled("feature1") is False
        assert gd.is_feature_enabled("feature3") is True

    def test_restore(self):
        """Test restoration."""
        gd = GracefulDegradation()
        gd.degrade(2, ["feature1"])
        gd.restore(0)
        assert gd.degradation_level == 0
        assert gd.is_feature_enabled("feature1") is True


class TestAppError:
    """Tests for AppError."""

    def test_creation(self):
        """Test error creation."""
        error = AppError(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            message="Test error",
        )
        assert error.category == ErrorCategory.VALIDATION
        assert error.recoverable is True
