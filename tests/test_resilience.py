import asyncio

import pytest

from aegis.resilience import (
    Bulkhead,
    BulkheadFullError,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    FallbackChain,
    RetryConfig,
    RetryExhaustedError,
    Timeout,
    retry_async,
)


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker for testing."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,
        success_threshold=2,
        timeout=5.0,
    )
    return CircuitBreaker("test", config)


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state."""
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0

    @pytest.mark.asyncio
    async def test_success(self, circuit_breaker):
        """Test successful execution."""
        async def success_func():
            return "success"

        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_counting(self, circuit_breaker):
        """Test failure counting."""
        async def failing_func():
            raise ValueError("test error")

        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        assert circuit_breaker.state.failure_count == 2
        assert circuit_breaker.state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens(self, circuit_breaker):
        """Test circuit opens after threshold."""
        async def failing_func():
            raise ValueError("test error")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        assert circuit_breaker.state.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self, circuit_breaker):
        """Test circuit rejects requests when open."""
        async def failing_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        # Should reject
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.execute(success_func)

    @pytest.mark.asyncio
    async def test_circuit_half_open(self, circuit_breaker):
        """Test circuit half-open state."""
        async def failing_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Should be half-open now
        result = await circuit_breaker.execute(success_func)
        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_from_half_open(self, circuit_breaker):
        """Test circuit closes from half-open after successes."""
        async def failing_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Success threshold is 2
        await circuit_breaker.execute(success_func)
        await circuit_breaker.execute(success_func)

        assert circuit_breaker.state.state == CircuitState.CLOSED

    def test_get_state(self, circuit_breaker):
        """Test getting circuit breaker state."""
        state = circuit_breaker.get_state()
        assert "name" in state
        assert "state" in state
        assert "failure_count" in state


class TestRetryAsync:
    """Tests for retry_async."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Test success on first try."""
        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await retry_async(success_func, config)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test success after retries."""
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "success"

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await retry_async(flaky_func, config)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self):
        """Test all retries exhausted."""
        async def always_fail():
            raise ValueError("always fails")

        config = RetryConfig(max_retries=2, base_delay=0.01)
        with pytest.raises(RetryExhaustedError):
            await retry_async(always_fail, config)


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
            raise ValueError("primary failed")

        chain = FallbackChain("test")
        chain.add("primary", failing)
        chain.add("secondary", lambda: "secondary")

        result = await chain.execute()
        assert result == "secondary"

    @pytest.mark.asyncio
    async def test_all_fail(self):
        """Test all fallbacks fail."""
        def fail1():
            raise ValueError("fail 1")

        def fail2():
            raise ValueError("fail 2")

        chain = FallbackChain("test")
        chain.add("primary", fail1)
        chain.add("secondary", fail2)

        with pytest.raises(ValueError):
            await chain.execute()


class TestBulkhead:
    """Tests for Bulkhead."""

    @pytest.mark.asyncio
    async def test_within_limits(self):
        """Test execution within limits."""
        bulkhead = Bulkhead("test", max_concurrent=2, max_queue=5)

        async def work():
            await asyncio.sleep(0.1)
            return "done"

        result = await bulkhead.execute(work)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_queue_full(self):
        """Test queue full rejection."""
        bulkhead = Bulkhead("test", max_concurrent=1, max_queue=1)

        async def slow_work():
            await asyncio.sleep(1)
            return "done"

        # Start one task
        task1 = asyncio.create_task(bulkhead.execute(slow_work))
        await asyncio.sleep(0.01)

        # Queue should be full
        with pytest.raises(BulkheadFullError):
            await bulkhead.execute(slow_work)

        task1.cancel()

    def test_get_state(self):
        """Test getting bulkhead state."""
        bulkhead = Bulkhead("test", max_concurrent=5, max_queue=10)
        state = bulkhead.get_state()
        assert state["name"] == "test"
        assert state["max_concurrent"] == 5
        assert state["max_queue"] == 10


class TestTimeout:
    """Tests for Timeout."""

    @pytest.mark.asyncio
    async def test_within_timeout(self):
        """Test execution within timeout."""
        timeout = Timeout(1.0, "test")

        async def fast_work():
            return "done"

        result = await timeout.execute(fast_work)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_exceeds_timeout(self):
        """Test execution exceeds timeout."""
        timeout = Timeout(0.1, "test")

        async def slow_work():
            await asyncio.sleep(1)
            return "done"

        with pytest.raises(TimeoutError):
            await timeout.execute(slow_work)
