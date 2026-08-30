import time
from unittest.mock import MagicMock

import pytest

from aegis.rate_limit import RateLimiter, RateLimitRule


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter for each test."""
    return RateLimiter()


@pytest.fixture
def mock_request():
    """Create a mock request without user state."""
    request = MagicMock()
    request.headers = {}
    request.url.path = "/test"
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.state = MagicMock(spec=[])  # No user attribute
    return request


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_initial_setup(self, rate_limiter):
        """Test that default rules are set up."""
        assert "default" in rate_limiter.rules
        assert "investigation" in rate_limiter.rules
        assert "auth" in rate_limiter.rules
        assert "search" in rate_limiter.rules

    def test_get_client_id_with_api_key(self, rate_limiter):
        """Test getting client ID from API key."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test_api_key_123"}
        request.url.path = "/test"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock(spec=[])  # No user attribute

        client_id = rate_limiter._get_client_id(request)
        assert client_id == "apikey:test_api"  # Truncated to 8 chars

    def test_get_client_id_with_ip(self, rate_limiter, mock_request):
        """Test getting client ID from IP address."""
        client_id = rate_limiter._get_client_id(mock_request)
        assert client_id == "ip:127.0.0.1"

    def test_get_rule_for_path(self, rate_limiter):
        """Test getting rate limit rule for different paths."""
        rule = rate_limiter._get_rule_for_path("/v1/investigations")
        assert rule.requests == 10

        rule = rate_limiter._get_rule_for_path("/health")
        assert rule.requests == 100

    def test_check_rate_limit_allowed(self, rate_limiter, mock_request):
        """Test that requests within limits are allowed."""
        allowed, headers = rate_limiter.check_rate_limit(mock_request)
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers

    def test_check_rate_limit_exceeded(self, rate_limiter, mock_request):
        """Test that requests exceeding limits are blocked."""
        # Make requests up to the limit
        for _ in range(100):
            rate_limiter.check_rate_limit(mock_request)

        # Next request should be blocked
        allowed, headers = rate_limiter.check_rate_limit(mock_request)
        assert allowed is False
        assert "Retry-After" in headers

    def test_rate_limit_window_reset(self, rate_limiter, mock_request):
        """Test that rate limit window resets after time passes."""
        # Make requests up to the limit
        for _ in range(100):
            rate_limiter.check_rate_limit(mock_request)

        # Manually expire the window
        client_id = rate_limiter._get_client_id(mock_request)
        rate_limiter.clients[client_id][mock_request.url.path].requests = [
            time.time() - 61  # 61 seconds ago
        ]

        # Should be allowed now
        allowed, _ = rate_limiter.check_rate_limit(mock_request)
        assert allowed is True

    def test_add_custom_rule(self, rate_limiter):
        """Test adding a custom rate limit rule."""
        rate_limiter.add_rule("custom", RateLimitRule(requests=50, window=30))
        assert "custom" in rate_limiter.rules
        assert rate_limiter.rules["custom"].requests == 50

    def test_get_stats(self, rate_limiter, mock_request):
        """Test getting rate limiter statistics."""
        # Make some requests
        for _ in range(5):
            rate_limiter.check_rate_limit(mock_request)

        stats = rate_limiter.get_stats()
        assert "total_clients" in stats
        assert "total_tracked_requests" in stats
        assert "rules" in stats
        assert stats["total_clients"] > 0

    def test_different_paths_different_limits(self, rate_limiter):
        """Test that different paths have different rate limits."""
        # Investigation path
        inv_request = MagicMock()
        inv_request.headers = {}
        inv_request.url.path = "/v1/investigations"
        inv_request.client = MagicMock()
        inv_request.client.host = "127.0.0.1"
        inv_request.state = MagicMock(spec=[])  # No user attribute

        # Make 10 investigation requests (limit)
        for _ in range(10):
            allowed, _ = rate_limiter.check_rate_limit(inv_request)
            assert allowed is True

        # 11th should be blocked
        allowed, _ = rate_limiter.check_rate_limit(inv_request)
        assert allowed is False

        # But health endpoint should still work
        health_request = MagicMock()
        health_request.headers = {}
        health_request.url.path = "/health"
        health_request.client = MagicMock()
        health_request.client.host = "127.0.0.1"
        health_request.state = MagicMock(spec=[])  # No user attribute

        allowed, _ = rate_limiter.check_rate_limit(health_request)
        assert allowed is True

    def test_client_id_with_forwarded_header(self, rate_limiter):
        """Test client ID with X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.url.path = "/test"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock(spec=[])  # No user attribute

        client_id = rate_limiter._get_client_id(request)
        assert client_id == "ip:192.168.1.1"

    def test_rate_limit_headers_content(self, rate_limiter, mock_request):
        """Test that rate limit headers contain correct values."""
        allowed, headers = rate_limiter.check_rate_limit(mock_request)
        assert allowed is True
        assert headers["X-RateLimit-Limit"] == "100"
        assert int(headers["X-RateLimit-Remaining"]) == 99
        assert "X-RateLimit-Reset" in headers

    def test_client_id_with_user_state(self, rate_limiter):
        """Test client ID when user is in request state."""
        request = MagicMock()
        request.headers = {}
        request.url.path = "/test"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        request.state.user = MagicMock()
        request.state.user.user_id = "user-123"

        client_id = rate_limiter._get_client_id(request)
        assert client_id == "user:user-123"
