from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import Any


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """Thread-safe LRU cache implementation with TTL support."""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.stats = CacheStats()
        self.lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.stats.hits += 1
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    self.stats.evictions += 1

            self.stats.misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                # Evict oldest
                self.cache.popitem(last=False)
                self.stats.evictions += 1

            self.cache[key] = (value, time.time())
            self.stats.size = len(self.cache)

    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.size = len(self.cache)
                return True
            return False

    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

    def get_or_set(self, key: str, factory: Callable[[], Any]) -> Any:
        """Get a value from cache, or compute and cache it."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value)
        return value


class QueryCache:
    """Cache for database queries with TTL and patient-specific invalidation."""

    def __init__(self, max_size: int = 500, ttl: int = 60):
        self.cache = LRUCache(max_size, ttl)
        self.patient_keys: dict[str, set[str]] = {}
        self.max_size = max_size
        self.ttl = ttl

    def _make_key(self, table: str, patient_id: str, **kwargs) -> str:
        """Create a cache key for a query."""
        key_parts = [table, patient_id]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def get_patient_data(self, table: str, patient_id: str) -> list[dict[str, Any]] | None:
        """Get cached patient data."""
        key = self._make_key(table, patient_id)
        return self.cache.get(key)

    def set_patient_data(self, table: str, patient_id: str, data: list[dict[str, Any]]) -> None:
        """Cache patient data."""
        key = self._make_key(table, patient_id)
        self.cache.set(key, data)

        # Track patient-key relationship for invalidation
        if patient_id not in self.patient_keys:
            self.patient_keys[patient_id] = set()
        self.patient_keys[patient_id].add(key)

    def invalidate_patient(self, patient_id: str) -> None:
        """Invalidate all cached data for a patient."""
        keys = self.patient_keys.pop(patient_id, set())
        for key in keys:
            self.cache.delete(key)

    def clear_all(self) -> None:
        """Clear all cache data."""
        self.cache.clear()
        self.patient_keys.clear()


class ConnectionPool:
    """Simple connection pool for database connections."""

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.pool: list[Any] = []
        self.in_use: set[int] = set()
        self.lock = Lock()

    def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        with self.lock:
            # Try to reuse an existing connection
            for i, conn in enumerate(self.pool):
                if i not in self.in_use:
                    self.in_use.add(i)
                    return conn

            # Create new connection if pool not full
            if len(self.pool) < self.max_size:
                conn = self._create_connection()
                self.pool.append(conn)
                self.in_use.add(len(self.pool) - 1)
                return conn

            # Pool is full, wait and retry
            raise RuntimeError("Connection pool exhausted")

    def release(self, conn: Any) -> None:
        """Release a connection back to the pool."""
        with self.lock:
            for i, pool_conn in enumerate(self.pool):
                if pool_conn is conn:
                    self.in_use.discard(i)
                    break

    def _create_connection(self) -> Any:
        """Create a new database connection."""
        # This would create an actual database connection
        # For now, return a placeholder
        return {"id": id(self), "created": time.time()}

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self.lock:
            self.pool.clear()
            self.in_use.clear()


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}

    def record(self, metric_name: str, value: float) -> None:
        """Record a performance metric."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_stats(self, metric_name: str) -> dict[str, float]:
        """Get statistics for a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "mean": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all metrics."""
        return {name: self.get_stats(name) for name in self.metrics}

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


def timed(monitor: PerformanceMonitor | None = None):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.perf_counter() - start) * 1000
                if monitor:
                    monitor.record(func.__name__, duration)
        return wrapper
    return decorator


class BatchProcessor:
    """Process items in batches for efficiency."""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def process_batch(self, items: list[Any], processor: Callable[[list[Any]], Any]) -> list[Any]:
        """Process items in batches."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_result = processor(batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
        return results


class IndexBuilder:
    """Build indexes for fast lookups."""

    @staticmethod
    def build_index(data: list[dict[str, Any]], key_field: str) -> dict[str, list[dict[str, Any]]]:
        """Build an index on a field."""
        index: dict[str, list[dict[str, Any]]] = {}
        for item in data:
            key = str(item.get(key_field, ""))
            if key not in index:
                index[key] = []
            index[key].append(item)
        return index

    @staticmethod
    def build_composite_index(
        data: list[dict[str, Any]],
        key_fields: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build a composite index on multiple fields."""
        index: dict[str, list[dict[str, Any]]] = {}
        for item in data:
            key = "|".join(str(item.get(f, "")) for f in key_fields)
            if key not in index:
                index[key] = []
            index[key].append(item)
        return index


# Global instances
query_cache = QueryCache()
performance_monitor = PerformanceMonitor()
connection_pool = ConnectionPool()
