from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    total_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        total = self.hits + self.misses
        return self.total_latency_ms / total if total > 0 else 0.0


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Set a value in cache with optional TTL."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...


class MemoryCacheBackend(CacheBackend):
    """In-memory LRU cache backend with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, tuple[Any, float, int]] = OrderedDict()  # (value, timestamp, ttl)
        self.stats = CacheStats()
        self.lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        start = time.perf_counter()
        with self.lock:
            if key in self.cache:
                value, timestamp, ttl = self.cache[key]
                if ttl == 0 or time.time() - timestamp < ttl:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.stats.hits += 1
                    self.stats.total_latency_ms += (time.perf_counter() - start) * 1000
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    self.stats.evictions += 1

            self.stats.misses += 1
            self.stats.total_latency_ms += (time.perf_counter() - start) * 1000
            return None

    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Set a value in cache."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
                self.stats.evictions += 1

            self.cache[key] = (value, time.time(), ttl or self.default_ttl)
            self.stats.size = len(self.cache)

    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.size = len(self.cache)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self.lock:
            if key in self.cache:
                _, timestamp, ttl = self.cache[key]
                if ttl == 0 or time.time() - timestamp < ttl:
                    return True
                else:
                    del self.cache[key]
                    self.stats.evictions += 1
            return False


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for distributed caching."""

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "aegis:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._client = None

    def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self.redis_url, decode_responses=True)
            except ImportError:
                raise ImportError("redis package required for Redis cache backend")
        return self._client

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any | None:
        """Get a value from Redis."""
        try:
            client = self._get_client()
            data = client.get(self._make_key(key))
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Set a value in Redis."""
        try:
            client = self._get_client()
            data = json.dumps(value, default=str)
            if ttl > 0:
                client.setex(self._make_key(key), ttl, data)
            else:
                client.set(self._make_key(key), data)
        except Exception:
            pass  # Graceful degradation

    def delete(self, key: str) -> bool:
        """Delete a value from Redis."""
        try:
            client = self._get_client()
            return client.delete(self._make_key(key)) > 0
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all cache entries with prefix."""
        try:
            client = self._get_client()
            keys = client.keys(f"{self.prefix}*")
            if keys:
                client.delete(*keys)
        except Exception:
            pass

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            client = self._get_client()
            return client.exists(self._make_key(key)) > 0
        except Exception:
            return False


class CacheManager:
    """Unified cache manager with multiple backends and strategies."""

    def __init__(
        self,
        backend: CacheBackend | None = None,
        enable_stats: bool = True,
    ):
        self.backend = backend or MemoryCacheBackend()
        self.enable_stats = enable_stats
        self._key_generators: dict[str, Callable] = {}

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Set a value in cache."""
        self.backend.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        return self.backend.delete(key)

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int = 0,
    ) -> Any:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        # For memory cache, we need to iterate
        if isinstance(self.backend, MemoryCacheBackend):
            count = 0
            with self.backend.lock:
                keys_to_delete = [
                    k for k in self.backend.cache.keys()
                    if pattern in k
                ]
                for key in keys_to_delete:
                    del self.backend.cache[key]
                    count += 1
                self.backend.stats.size = len(self.backend.cache)
            return count
        return 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if isinstance(self.backend, MemoryCacheBackend):
            return {
                "backend": "memory",
                "hits": self.backend.stats.hits,
                "misses": self.backend.stats.misses,
                "hit_rate": self.backend.stats.hit_rate,
                "evictions": self.backend.stats.evictions,
                "size": self.backend.stats.size,
                "max_size": self.backend.max_size,
                "avg_latency_ms": self.backend.stats.avg_latency_ms,
            }
        return {"backend": "redis"}

    def clear(self) -> None:
        """Clear all cache entries."""
        self.backend.clear()


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    raw = "|".join(key_parts)
    return hashlib.md5(raw.encode()).hexdigest()


def cached(
    cache: CacheManager,
    key_prefix: str,
    ttl: int = 300,
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            key = f"{key_prefix}:{cache_key(*args, **kwargs)}"
            return cache.get_or_set(key, lambda: func(*args, **kwargs), ttl)

        async def async_wrapper(*args, **kwargs):
            key = f"{key_prefix}:{cache_key(*args, **kwargs)}"
            result = cache.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def _build_cache_manager(
    max_size: int = 1000,
    default_ttl: int = 300,
    key_prefix: str = "aegis:",
) -> CacheManager:
    """Build a CacheManager using Redis if configured, else in-memory."""
    import os
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            backend = RedisCacheBackend(redis_url=redis_url, prefix=key_prefix)
            # Verify connectivity
            client = backend._get_client()
            client.ping()
            return CacheManager(backend)
        except Exception:
            pass
    return CacheManager(MemoryCacheBackend(max_size=max_size, default_ttl=default_ttl))


# Global cache instances
default_cache = _build_cache_manager(max_size=1000, default_ttl=300, key_prefix="aegis:default:")
query_cache = _build_cache_manager(max_size=500, default_ttl=60, key_prefix="aegis:query:")
llm_cache = _build_cache_manager(max_size=200, default_ttl=3600, key_prefix="aegis:llm:")
investigation_cache = _build_cache_manager(max_size=200, default_ttl=600, key_prefix="aegis:inv:")
