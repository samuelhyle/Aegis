import time

import pytest

from aegis.cache import (
    CacheManager,
    MemoryCacheBackend,
    cache_key,
    cached,
)


@pytest.fixture
def memory_backend():
    """Create a memory cache backend."""
    return MemoryCacheBackend(max_size=10, default_ttl=60)


@pytest.fixture
def cache_manager(memory_backend):
    """Create a cache manager with memory backend."""
    return CacheManager(memory_backend)


class TestMemoryCacheBackend:
    """Tests for MemoryCacheBackend."""

    def test_set_and_get(self, memory_backend):
        """Test setting and getting values."""
        memory_backend.set("key1", "value1")
        assert memory_backend.get("key1") == "value1"

    def test_get_nonexistent(self, memory_backend):
        """Test getting a nonexistent key."""
        assert memory_backend.get("nonexistent") is None

    def test_delete(self, memory_backend):
        """Test deleting a value."""
        memory_backend.set("key1", "value1")
        assert memory_backend.delete("key1") is True
        assert memory_backend.get("key1") is None

    def test_delete_nonexistent(self, memory_backend):
        """Test deleting a nonexistent key."""
        assert memory_backend.delete("nonexistent") is False

    def test_clear(self, memory_backend):
        """Test clearing all values."""
        memory_backend.set("key1", "value1")
        memory_backend.set("key2", "value2")
        memory_backend.clear()
        assert memory_backend.get("key1") is None
        assert memory_backend.get("key2") is None

    def test_exists(self, memory_backend):
        """Test checking if key exists."""
        memory_backend.set("key1", "value1")
        assert memory_backend.exists("key1") is True
        assert memory_backend.exists("nonexistent") is False

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        backend = MemoryCacheBackend(max_size=10, default_ttl=1)
        backend.set("key1", "value1")
        assert backend.get("key1") == "value1"

        time.sleep(1.1)
        assert backend.get("key1") is None

    def test_max_size_eviction(self):
        """Test max size eviction."""
        backend = MemoryCacheBackend(max_size=3, default_ttl=60)
        backend.set("key1", "value1")
        backend.set("key2", "value2")
        backend.set("key3", "value3")
        backend.set("key4", "value4")  # Should evict key1

        assert backend.get("key1") is None
        assert backend.get("key4") == "value4"

    def test_stats(self, memory_backend):
        """Test cache statistics."""
        memory_backend.set("key1", "value1")
        memory_backend.get("key1")  # Hit
        memory_backend.get("nonexistent")  # Miss

        stats = memory_backend.stats
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5


class TestCacheManager:
    """Tests for CacheManager."""

    def test_get_or_set(self, cache_manager):
        """Test get_or_set pattern."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "computed_value"

        result1 = cache_manager.get_or_set("key1", factory)
        result2 = cache_manager.get_or_set("key1", factory)

        assert result1 == "computed_value"
        assert result2 == "computed_value"
        assert call_count == 1  # Factory called only once

    def test_invalidate_pattern(self, cache_manager):
        """Test pattern invalidation."""
        cache_manager.set("user:1:name", "Alice")
        cache_manager.set("user:2:name", "Bob")
        cache_manager.set("other:key", "value")

        count = cache_manager.invalidate_pattern("user:")
        assert count == 2
        assert cache_manager.get("other:key") == "value"

    def test_get_stats(self, cache_manager):
        """Test getting cache stats."""
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")

        stats = cache_manager.get_stats()
        assert "backend" in stats
        assert stats["backend"] == "memory"


class TestCacheKey:
    """Tests for cache_key function."""

    def test_basic_key(self):
        """Test basic key generation."""
        key = cache_key("arg1", "arg2")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash

    def test_kwargs_key(self):
        """Test key with kwargs."""
        key1 = cache_key(param1="a", param2="b")
        key2 = cache_key(param2="b", param1="a")
        assert key1 == key2  # Order shouldn't matter

    def test_different_args_different_keys(self):
        """Test different args produce different keys."""
        key1 = cache_key("a", "b")
        key2 = cache_key("a", "c")
        assert key1 != key2


class TestCachedDecorator:
    """Tests for cached decorator."""

    def test_cached_function(self, cache_manager):
        """Test cached decorator."""
        call_count = 0

        @cached(cache_manager, "test", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once
