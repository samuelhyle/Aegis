from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aegis")


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Simple metrics collector for Prometheus-style metrics."""

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._labels: dict[str, dict[str, str]] = {}

    def inc_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] += value
        if labels:
            self._labels[key] = labels

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        if labels:
            self._labels[key] = labels

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Observe a value for a histogram metric."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        if labels:
            self._labels[key] = labels

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a metric key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics in a structured format."""
        metrics = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {},
        }

        for key, values in self._histograms.items():
            if values:
                metrics["histograms"][key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p50": sorted(values)[len(values) // 2],
                    "p95": sorted(values)[int(len(values) * 0.95)],
                    "p99": sorted(values)[int(len(values) * 0.99)],
                }

        return metrics

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._labels.clear()


class Tracer:
    """Simple tracer for distributed tracing."""

    def __init__(self):
        self._traces: dict[str, dict[str, Any]] = {}

    @contextmanager
    def trace(
        self,
        name: str,
        trace_id: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager for tracing a span."""
        span_id = f"{trace_id}-{name}-{int(time.time() * 1000)}"
        start_time = time.time()

        span = {
            "span_id": span_id,
            "trace_id": trace_id,
            "name": name,
            "start_time": start_time,
            "attributes": attributes or {},
            "events": [],
        }

        if trace_id not in self._traces:
            self._traces[trace_id] = {
                "trace_id": trace_id,
                "spans": [],
                "start_time": start_time,
            }

        self._traces[trace_id]["spans"].append(span)

        try:
            yield span
        except Exception as e:
            span["error"] = str(e)
            span["events"].append({
                "name": "exception",
                "timestamp": time.time(),
                "attributes": {"exception.type": type(e).__name__, "exception.message": str(e)},
            })
            raise
        finally:
            span["end_time"] = time.time()
            span["duration_ms"] = (span["end_time"] - start_time) * 1000

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent traces."""
        traces = list(self._traces.values())
        traces.sort(key=lambda t: t["start_time"], reverse=True)
        return traces[:limit]


class StructuredLogger:
    """Structured logger for AEGIS with correlation ID support."""

    def __init__(self, name: str = "aegis"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            self.logger.addHandler(handler)

    def _get_correlation_id(self) -> str:
        """Get current correlation ID from context."""
        try:
            from .tracing import get_correlation_id
            cid = get_correlation_id()
            if cid:
                return cid
        except ImportError:
            pass
        return ""

    def log_investigation(
        self,
        trace_id: str,
        patient_id: str,
        question: str,
        confidence: float,
        review_required: bool,
        agent_count: int,
        duration_ms: float,
    ):
        """Log an investigation event."""
        self.logger.info(
            "Investigation completed",
            extra={
                "event": "investigation",
                "correlation_id": self._get_correlation_id(),
                "trace_id": trace_id,
                "patient_id": patient_id,
                "question": question[:100],
                "confidence": confidence,
                "review_required": review_required,
                "agent_count": agent_count,
                "duration_ms": duration_ms,
            },
        )

    def log_review(
        self,
        trace_id: str,
        decision: str,
        reviewer_id: str,
    ):
        """Log a review event."""
        self.logger.info(
            "Investigation reviewed",
            extra={
                "event": "review",
                "correlation_id": self._get_correlation_id(),
                "trace_id": trace_id,
                "decision": decision,
                "reviewer_id": reviewer_id,
            },
        )

    def log_agent_execution(
        self,
        agent_name: str,
        patient_id: str,
        confidence: float,
        duration_ms: float,
        evidence_count: int,
    ):
        """Log an agent execution event."""
        self.logger.info(
            "Agent executed",
            extra={
                "event": "agent_execution",
                "correlation_id": self._get_correlation_id(),
                "agent_name": agent_name,
                "patient_id": patient_id,
                "confidence": confidence,
                "duration_ms": duration_ms,
                "evidence_count": evidence_count,
            },
        )

    def log_error(self, error: Exception, context: dict[str, Any] | None = None):
        """Log an error event."""
        self.logger.error(
            f"Error: {error}",
            extra={
                "event": "error",
                "correlation_id": self._get_correlation_id(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
            },
        )


# Global instances
metrics = MetricsCollector()
tracer = Tracer()
structured_logger = StructuredLogger()


def get_metrics() -> dict[str, Any]:
    """Get all metrics."""
    return metrics.get_metrics()


def get_traces(limit: int = 100) -> list[dict[str, Any]]:
    """Get recent traces."""
    return tracer.get_traces(limit)


def get_trace(trace_id: str) -> dict[str, Any] | None:
    """Get a specific trace."""
    return tracer.get_trace(trace_id)
