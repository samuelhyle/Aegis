
import pytest

from aegis.observability import (
    Alert,
    AlertManager,
    AlertSeverity,
    HealthMonitor,
    MetricsCollector,
    Span,
    Tracer,
)


@pytest.fixture
def metrics_collector():
    """Create a metrics collector for testing."""
    return MetricsCollector()


@pytest.fixture
def tracer():
    """Create a tracer for testing."""
    return Tracer()


@pytest.fixture
def alert_manager():
    """Create an alert manager for testing."""
    return AlertManager()


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_inc_counter(self, metrics_collector):
        """Test incrementing counter."""
        metrics_collector.inc_counter("test_counter")
        metrics = metrics_collector.get_metrics()
        assert metrics["counters"]["test_counter"] == 1

    def test_inc_counter_with_labels(self, metrics_collector):
        """Test incrementing counter with labels."""
        metrics_collector.inc_counter("test_counter", labels={"method": "GET"})
        metrics = metrics_collector.get_metrics()
        assert 'test_counter{method="GET"}' in metrics["counters"]

    def test_set_gauge(self, metrics_collector):
        """Test setting gauge."""
        metrics_collector.set_gauge("test_gauge", 42.0)
        metrics = metrics_collector.get_metrics()
        assert metrics["gauges"]["test_gauge"] == 42.0

    def test_observe_histogram(self, metrics_collector):
        """Test observing histogram."""
        metrics_collector.observe_histogram("test_histogram", 10.0)
        metrics_collector.observe_histogram("test_histogram", 20.0)
        metrics_collector.observe_histogram("test_histogram", 30.0)

        metrics = metrics_collector.get_metrics()
        hist = metrics["histograms"]["test_histogram"]
        assert hist["count"] == 3
        assert hist["sum"] == 60.0
        assert hist["avg"] == 20.0

    def test_get_prometheus_format(self, metrics_collector):
        """Test Prometheus format output."""
        metrics_collector.inc_counter("test_counter")
        metrics_collector.set_gauge("test_gauge", 42.0)

        output = metrics_collector.get_prometheus_format()
        assert "test_counter" in output
        assert "test_gauge" in output

    def test_reset(self, metrics_collector):
        """Test resetting metrics."""
        metrics_collector.inc_counter("test_counter")
        metrics_collector.reset()

        metrics = metrics_collector.get_metrics()
        assert len(metrics["counters"]) == 0


class TestTracer:
    """Tests for Tracer."""

    def test_start_span(self, tracer):
        """Test starting a span."""
        span = tracer.start_span("test_operation")
        assert span.name == "test_operation"
        assert span.span_id is not None
        assert span.trace_id is not None

    def test_trace_context_manager(self, tracer):
        """Test trace context manager."""
        with tracer.trace("test_operation") as span:
            assert span.name == "test_operation"
            span.add_event("test_event")

        assert span.end_time is not None
        assert span.duration_ms > 0

    def test_trace_with_error(self, tracer):
        """Test trace with error."""
        with pytest.raises(ValueError):
            with tracer.trace("test_operation") as span:
                raise ValueError("test error")

        assert span.status == "error"
        assert span.error == "test error"

    def test_get_trace(self, tracer):
        """Test getting a trace."""
        tracer.start_span("test_operation", trace_id="trace123")
        trace = tracer.get_trace("trace123")
        assert trace is not None
        assert len(trace) == 1

    def test_get_traces(self, tracer):
        """Test getting traces."""
        tracer.start_span("op1")
        tracer.start_span("op2")

        traces = tracer.get_traces()
        assert len(traces) >= 2

    def test_clear(self, tracer):
        """Test clearing traces."""
        tracer.start_span("test_operation")
        tracer.clear()
        assert len(tracer._traces) == 0


class TestSpan:
    """Tests for Span."""

    def test_creation(self):
        """Test span creation."""
        span = Span(name="test")
        assert span.name == "test"
        assert span.span_id is not None
        assert span.trace_id is not None

    def test_finish(self):
        """Test finishing span."""
        span = Span(name="test")
        span.finish()
        assert span.end_time is not None
        assert span.duration_ms >= 0

    def test_add_event(self):
        """Test adding event."""
        span = Span(name="test")
        span.add_event("test_event", {"key": "value"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"


class TestAlertManager:
    """Tests for AlertManager."""

    def test_check_alerts(self, alert_manager):
        """Test checking alerts."""
        metrics = {"errors_total": 150}
        alerts = alert_manager.check_alerts(metrics)
        assert len(alerts) > 0
        assert alerts[0].name == "high_error_rate"

    def test_get_active_alerts(self, alert_manager):
        """Test getting active alerts."""
        alert_manager.alerts.append(Alert(
            name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test alert",
        ))

        active = alert_manager.get_active_alerts()
        assert len(active) == 1

    def test_resolve_alert(self, alert_manager):
        """Test resolving alert."""
        alert = Alert(
            name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test alert",
        )
        alert_manager.alerts.append(alert)

        result = alert_manager.resolve_alert(alert.alert_id)
        assert result is True
        assert alert.resolved is True

    def test_get_alert_history(self, alert_manager):
        """Test getting alert history."""
        for i in range(5):
            alert_manager.alerts.append(Alert(
                name=f"alert_{i}",
                severity=AlertSeverity.INFO,
                message=f"Alert {i}",
            ))

        history = alert_manager.get_alert_history(limit=3)
        assert len(history) == 3


class TestHealthMonitor:
    """Tests for HealthMonitor."""

    @pytest.mark.asyncio
    async def test_check_health(self):
        """Test health check."""
        monitor = HealthMonitor()

        def healthy_check():
            return {"status": "ok"}

        monitor.register_check("test", healthy_check)
        result = await monitor.check_health()

        assert result["status"] == "healthy"
        assert len(result["checks"]) == 1

    @pytest.mark.asyncio
    async def test_check_health_unhealthy(self):
        """Test unhealthy health check."""
        monitor = HealthMonitor()

        def unhealthy_check():
            raise ValueError("service down")

        monitor.register_check("test", unhealthy_check)
        result = await monitor.check_health()

        assert result["status"] == "unhealthy"
