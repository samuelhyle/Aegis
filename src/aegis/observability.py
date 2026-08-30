from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("aegis.observability")


class MetricType(StrEnum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metric_type: MetricType = MetricType.COUNTER


@dataclass
class Span:
    """A distributed tracing span."""
    span_id: str = field(default_factory=lambda: str(uuid4())[:8])
    trace_id: str = field(default_factory=lambda: str(uuid4())[:8])
    parent_id: str | None = None
    name: str = ""
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: str | None = None

    def finish(self, status: str = "ok", error: str | None = None):
        """Finish the span."""
        self.end_time = time.perf_counter()
        self.status = status
        self.error = error

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })


class MetricsCollector:
    """Prometheus-compatible metrics collector."""

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._labels: dict[str, dict[str, str]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def inc_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] += value
        if labels:
            self._labels[key] = labels
        self._metadata[key] = {"type": "counter", "name": name}

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ):
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        if labels:
            self._labels[key] = labels
        self._metadata[key] = {"type": "gauge", "name": name}

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ):
        """Observe a value for a histogram metric."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        if labels:
            self._labels[key] = labels
        self._metadata[key] = {"type": "histogram", "name": name}

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
                sorted_values = sorted(values)
                count = len(sorted_values)
                metrics["histograms"][key] = {
                    "count": count,
                    "sum": sum(sorted_values),
                    "avg": sum(sorted_values) / count,
                    "min": sorted_values[0],
                    "max": sorted_values[-1],
                    "p50": sorted_values[count // 2],
                    "p95": sorted_values[int(count * 0.95)],
                    "p99": sorted_values[int(count * 0.99)],
                }

        return metrics

    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus format."""
        lines = []

        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")

        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")

        for key, values in self._histograms.items():
            if values:
                name = key.split('{')[0]
                sorted_values = sorted(values)
                count = len(sorted_values)
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_count {count}")
                lines.append(f"{name}_sum {sum(sorted_values)}")

        return "\n".join(lines)

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._labels.clear()
        self._metadata.clear()


class Tracer:
    """Distributed tracing system."""

    def __init__(self):
        self._traces: dict[str, list[Span]] = {}
        self._current_span: Span | None = None

    def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new tracing span."""
        span = Span(
            name=name,
            trace_id=trace_id or str(uuid4())[:8],
            parent_id=parent_id,
            attributes=attributes or {},
        )

        if span.trace_id not in self._traces:
            self._traces[span.trace_id] = []
        self._traces[span.trace_id].append(span)

        self._current_span = span
        return span

    @contextmanager
    def trace(
        self,
        name: str,
        trace_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Span, None, None]:
        """Context manager for tracing a span."""
        span = self.start_span(name, trace_id, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.finish(status="error", error=str(e))
            raise
        else:
            span.finish()

    def get_trace(self, trace_id: str) -> list[Span] | None:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent traces."""
        traces = []
        for trace_id, spans in self._traces.items():
            if spans:
                traces.append({
                    "trace_id": trace_id,
                    "span_count": len(spans),
                    "start_time": spans[0].start_time,
                    "duration_ms": sum(s.duration_ms for s in spans),
                })
        traces.sort(key=lambda t: t["start_time"], reverse=True)
        return traces[:limit]

    def clear(self):
        """Clear all traces."""
        self._traces.clear()
        self._current_span = None


class AlertSeverity(StrEnum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """An alert instance."""
    alert_id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: datetime | None = None


class AlertManager:
    """Alert management system."""

    def __init__(self):
        self.alerts: list[Alert] = []
        self.rules: list[dict[str, Any]] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules."""
        self.rules = [
            {
                "name": "high_error_rate",
                "condition": lambda m: m.get("errors_total", 0) > 100,
                "severity": AlertSeverity.WARNING,
                "message": "High error rate detected",
            },
            {
                "name": "high_latency",
                "condition": lambda m: m.get("avg_latency_ms", 0) > 5000,
                "severity": AlertSeverity.WARNING,
                "message": "High latency detected",
            },
            {
                "name": "circuit_breaker_open",
                "condition": lambda m: m.get("circuit_breakers_open", 0) > 0,
                "severity": AlertSeverity.ERROR,
                "message": "Circuit breaker is open",
            },
        ]

    def check_alerts(self, metrics: dict[str, Any]) -> list[Alert]:
        """Check metrics against alert rules."""
        new_alerts = []

        for rule in self.rules:
            try:
                if rule["condition"](metrics):
                    alert = Alert(
                        name=rule["name"],
                        severity=rule["severity"],
                        message=rule["message"],
                        labels={"rule": rule["name"]},
                    )
                    new_alerts.append(alert)
                    self.alerts.append(alert)
            except Exception:
                pass

        return new_alerts

    def get_active_alerts(self) -> list[Alert]:
        """Get active (unresolved) alerts."""
        return [a for a in self.alerts if not a.resolved]

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                return True
        return False

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """Get alert history."""
        return self.alerts[-limit:]


class HealthStatus(StrEnum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """A health check result."""
    name: str
    status: HealthStatus
    message: str = ""
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """System health monitoring."""

    def __init__(self):
        self.checks: dict[str, Any] = {}
        self.last_check: datetime | None = None
        self.status: HealthStatus = HealthStatus.HEALTHY

    def register_check(self, name: str, check_func: Any) -> None:
        """Register a health check."""
        self.checks[name] = check_func

    async def check_health(self) -> dict[str, Any]:
        """Run all health checks."""
        results = []
        overall_status = HealthStatus.HEALTHY

        for name, check_func in self.checks.items():
            try:
                start = time.perf_counter()
                if callable(check_func):
                    result = check_func()
                else:
                    result = await check_func
                duration_ms = (time.perf_counter() - start) * 1000

                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    duration_ms=duration_ms,
                    details=result if isinstance(result, dict) else {},
                ))
            except Exception as e:
                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                ))
                overall_status = HealthStatus.UNHEALTHY

        self.last_check = datetime.now(timezone.utc)
        self.status = overall_status

        return {
            "status": overall_status.value,
            "timestamp": self.last_check.isoformat(),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "duration_ms": c.duration_ms,
                }
                for c in results
            ],
        }


# Global instances
metrics = MetricsCollector()
tracer = Tracer()
alert_manager = AlertManager()
health_monitor = HealthMonitor()


def get_metrics() -> dict[str, Any]:
    """Get all metrics."""
    return metrics.get_metrics()


def get_traces(limit: int = 100) -> list[dict[str, Any]]:
    """Get recent traces."""
    return tracer.get_traces(limit)


def get_trace(trace_id: str) -> list[dict[str, Any]] | None:
    """Get a specific trace."""
    spans = tracer.get_trace(trace_id)
    if spans:
        return [
            {
                "span_id": s.span_id,
                "name": s.name,
                "duration_ms": s.duration_ms,
                "status": s.status,
                "attributes": s.attributes,
            }
            for s in spans
        ]
    return None


def get_alerts() -> list[dict[str, Any]]:
    """Get active alerts."""
    return [
        {
            "alert_id": a.alert_id,
            "name": a.name,
            "severity": a.severity.value,
            "message": a.message,
            "timestamp": a.timestamp.isoformat(),
        }
        for a in alert_manager.get_active_alerts()
    ]
