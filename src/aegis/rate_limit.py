from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    requests: int  # Maximum requests
    window: int  # Time window in seconds
    burst: int = 0  # Maximum burst requests (0 = same as requests)


@dataclass
class RateLimitState:
    """Rate limit state for a client."""
    requests: list[float] = field(default_factory=list)
    last_request: float = 0.0


class RateLimiter:
    """Token bucket rate limiter with sliding window."""

    def __init__(self):
        self.rules: dict[str, RateLimitRule] = {}
        self.clients: dict[str, dict[str, RateLimitState]] = defaultdict(lambda: defaultdict(RateLimitState))
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default rate limit rules."""
        self.rules = {
            "default": RateLimitRule(requests=100, window=60),  # 100 requests per minute
            "investigation": RateLimitRule(requests=10, window=60),  # 10 investigations per minute
            "auth": RateLimitRule(requests=5, window=60),  # 5 auth attempts per minute
            "search": RateLimitRule(requests=30, window=60),  # 30 searches per minute
        }

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use API key, user ID, or IP address
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:8]}"

        # Try to get user from request state
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user.user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _get_rule_for_path(self, path: str) -> RateLimitRule:
        """Get rate limit rule for a request path."""
        if "/investigations" in path:
            return self.rules["investigation"]
        if "/auth" in path or "/token" in path:
            return self.rules["auth"]
        if "/search" in path:
            return self.rules["search"]
        return self.rules["default"]

    def check_rate_limit(self, request: Request) -> tuple[bool, dict[str, Any]]:
        """Check if request is within rate limits. Returns (allowed, headers)."""
        client_id = self._get_client_id(request)
        rule = self._get_rule_for_path(request.url.path)
        state = self.clients[client_id][request.url.path]

        now = time.time()
        window_start = now - rule.window

        # Remove old requests outside the window
        state.requests = [t for t in state.requests if t > window_start]

        # Check if within limits
        if len(state.requests) >= rule.requests:
            retry_after = int(state.requests[0] + rule.window - now) + 1
            return False, {
                "X-RateLimit-Limit": str(rule.requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(state.requests[0] + rule.window)),
                "Retry-After": str(retry_after),
            }

        # Add current request
        state.requests.append(now)
        state.last_request = now

        return True, {
            "X-RateLimit-Limit": str(rule.requests),
            "X-RateLimit-Remaining": str(rule.requests - len(state.requests)),
            "X-RateLimit-Reset": str(int(now + rule.window)),
        }

    def add_rule(self, name: str, rule: RateLimitRule):
        """Add a custom rate limit rule."""
        self.rules[name] = rule

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics."""
        total_clients = len(self.clients)
        total_requests = sum(
            len(state.requests)
            for client_paths in self.clients.values()
            for state in client_paths.values()
        )
        return {
            "total_clients": total_clients,
            "total_tracked_requests": total_requests,
            "rules": {name: {"requests": r.requests, "window": r.window} for name, r in self.rules.items()},
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, rate_limiter: RateLimiter | None = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self._disabled = os.getenv("AEGIS_RATE_LIMIT_DISABLED", "").lower() == "true"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting if disabled
        if self._disabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Check rate limit
        allowed, headers = self.rate_limiter.check_rate_limit(request)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


# Global rate limiter
rate_limiter = RateLimiter()
