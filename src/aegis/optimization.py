"""
Performance Optimization Module

This module provides performance optimizations for the AEGIS system:
1. Connection pooling for database operations
2. Query result caching with TTL
3. Lazy loading for expensive operations
4. Batch processing for bulk operations
5. Memory optimization for large datasets
"""

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
class PerformanceStats:
    """Performance statistics."""
    cache_hits: int = 0
    cache_misses: int = 0
    total_queries: int = 0
    total_time_ms: float = 0.0
    avg_query_time_ms: float = 0.0

    def record_hit(self):
        self.cache_hits += 1

    def record_miss(self):
        self.cache_misses += 1

    def record_query(self, duration_ms: float):
        self.total_queries += 1
        self.total_time_ms += duration_ms
        self.avg_query_time_ms = self.total_time_ms / self.total_queries

    @property
    def hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class OptimizedCache:
    """High-performance LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, tuple[Any, float, int]] = OrderedDict()
        self.stats = PerformanceStats()
        self.lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        with self.lock:
            if key in self.cache:
                value, timestamp, ttl = self.cache[key]
                if time.time() - timestamp < ttl:
                    self.cache.move_to_end(key)
                    self.stats.record_hit()
                    return value
                else:
                    del self.cache[key]

            self.stats.record_miss()
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)

            self.cache[key] = (value, time.time(), ttl or self.default_ttl)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: int | None = None) -> Any:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
            return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()


class QueryOptimizer:
    """Optimizes database queries."""

    def __init__(self):
        self.query_cache = OptimizedCache(max_size=500, default_ttl=60)
        self.index_cache: dict[str, dict[str, list[str]]] = {}

    def build_index(self, data: list[dict[str, Any]], key_field: str) -> dict[str, list[str]]:
        """Build an index for fast lookups."""
        cache_key = f"index_{key_field}_{len(data)}"
        return self.query_cache.get_or_set(
            cache_key,
            lambda: self._build_index_impl(data, key_field),
            ttl=300,
        )

    def _build_index_impl(self, data: list[dict[str, Any]], key_field: str) -> dict[str, list[str]]:
        """Build index implementation."""
        index: dict[str, list[str]] = {}
        for i, item in enumerate(data):
            key = str(item.get(key_field, ""))
            if key not in index:
                index[key] = []
            index[key].append(str(i))
        return index

    def batch_query(self, queries: list[Callable[[], Any]]) -> list[Any]:
        """Execute multiple queries in batch."""
        results = []
        for query in queries:
            results.append(query())
        return results


class MemoryOptimizer:
    """Optimizes memory usage."""

    @staticmethod
    def optimize_dataframe(df: Any) -> Any:
        """Optimize pandas DataFrame memory usage."""
        if df is None:
            return None

        try:
            import pandas as pd

            for col in df.columns:
                col_type = df[col].dtype

                if col_type == 'object':
                    # Try to convert to category if few unique values
                    unique_ratio = len(df[col].unique()) / len(df)
                    if unique_ratio < 0.5:
                        df[col] = df[col].astype('category')

                elif col_type == 'int64':
                    # Downcast integers
                    df[col] = pd.to_numeric(df[col], downcast='integer')

                elif col_type == 'float64':
                    # Downcast floats
                    df[col] = pd.to_numeric(df[col], downcast='float')

            return df
        except Exception:
            return df

    @staticmethod
    def chunk_list(data: list, chunk_size: int = 1000) -> list[list]:
        """Split a list into chunks."""
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    @staticmethod
    def lazy_property(func: Callable) -> property:
        """Decorator for lazy property evaluation."""
        attr_name = f'_lazy_{func.__name__}'

        @property
        def lazy_wrapper(self):
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)

        return lazy_wrapper


class BatchProcessor:
    """Processes items in batches for efficiency."""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def process(self, items: list[Any], processor: Callable[[list[Any]], list[Any]]) -> list[Any]:
        """Process items in batches."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
        return results

    async def process_async(self, items: list[Any], processor: Callable[[list[Any]], Any]) -> list[Any]:
        """Process items in batches asynchronously."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await processor(batch)
            results.extend(batch_results)
        return results


class ConnectionPool:
    """Connection pool for database connections."""

    def __init__(self, max_size: int = 10, create_func: Callable = None):
        self.max_size = max_size
        self.create_func = create_func or (lambda: {"id": id(self), "created": time.time()})
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
                conn = self.create_func()
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

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self.lock:
            self.pool.clear()
            self.in_use.clear()


def timed(monitor: Any = None):
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


def cached(cache: OptimizedCache, key_prefix: str, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix] + [str(arg) for arg in args]
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            return cache.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl)
        return wrapper
    return decorator


# Global instances
query_optimizer = QueryOptimizer()
memory_optimizer = MemoryOptimizer()
batch_processor = BatchProcessor()
connection_pool = ConnectionPool()
performance_cache = OptimizedCache(max_size=1000, default_ttl=300)
