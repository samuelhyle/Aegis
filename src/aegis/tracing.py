from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aegis.tracing")

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
_span_stack: ContextVar[list[dict[str, Any]]] = ContextVar("span_stack", default=[])


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(cid: str) -> str:
    _correlation_id.set(cid)
    return cid


def get_trace_id() -> str:
    return _trace_id_var.get()


def generate_correlation_id() -> str:
    return uuid.uuid4().hex[:16]


@dataclass
class Span:
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    trace_id: str = ""
    parent_id: str | None = None
    name: str = ""
    kind: str = "internal"
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None
    status: str = "OK"
    status_message: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    resource: dict[str, str] = field(default_factory=dict)

    def finish(self, status: str = "OK", status_message: str = ""):
        self.end_time = time.perf_counter()
        self.status = status
        self.status_message = status_message

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": self.events,
            "resource": self.resource,
        }


class TracerProvider:
    """Lightweight OpenTelemetry-compatible tracer provider."""

    def __init__(self, service_name: str = "aegis", service_version: str = "0.4.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.resource = {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": os.getenv("AEGIS_ENV", "development"),
        }
        self._spans: dict[str, list[Span]] = {}
        self._exporters: list[Any] = []

    def add_exporter(self, exporter: Any):
        self._exporters.append(exporter)

    def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_id: str | None = None,
        kind: str = "internal",
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        tid = trace_id or _trace_id_var.get() or generate_correlation_id()
        span = Span(
            name=name,
            trace_id=tid,
            parent_id=parent_id,
            kind=kind,
            attributes=attributes or {},
            resource=self.resource,
        )
        if tid not in self._spans:
            self._spans[tid] = []
        self._spans[tid].append(span)
        return span

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_id: str | None = None,
        kind: str = "internal",
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Span, None, None]:
        span = self.start_span(name, trace_id, parent_id, kind, attributes)
        token = _span_stack.set(_span_stack.get() + [span])
        try:
            yield span
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.add_event("exception", {
                "exception.type": type(e).__name__,
                "exception.message": str(e),
            })
            span.finish("ERROR", str(e))
            raise
        else:
            span.finish()
        finally:
            _span_stack.reset(token)

    def get_trace(self, trace_id: str) -> list[dict[str, Any]] | None:
        spans = self._spans.get(trace_id)
        if spans:
            return [s.to_dict() for s in spans]
        return None

    def get_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        result = []
        for tid, spans in self._spans.items():
            if spans:
                first = spans[0]
                total_duration = sum(s.duration_ms for s in spans)
                result.append({
                    "trace_id": tid,
                    "span_count": len(spans),
                    "start_time": first.start_time,
                    "duration_ms": total_duration,
                    "status": "ERROR" if any(s.status == "ERROR" for s in spans) else "OK",
                })
        result.sort(key=lambda t: t["start_time"], reverse=True)
        return result[:limit]

    def get_trace_detail(self, trace_id: str) -> dict[str, Any] | None:
        spans = self._spans.get(trace_id)
        if not spans:
            return None
        return {
            "trace_id": trace_id,
            "spans": [s.to_dict() for s in spans],
            "total_duration_ms": sum(s.duration_ms for s in spans),
            "span_count": len(spans),
            "status": "ERROR" if any(s.status == "ERROR" for s in spans) else "OK",
        }

    def clear(self):
        self._spans.clear()


class FastAPITracingMiddleware:
    """Middleware to automatically trace FastAPI requests with correlation IDs."""

    def __init__(self, app: Any, provider: TracerProvider | None = None):
        self.app = app
        self.provider = provider or TracerProvider()

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID from headers
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", b"").decode()
        if not correlation_id:
            correlation_id = generate_correlation_id()

        set_correlation_id(correlation_id)
        _trace_id_var.set(correlation_id)

        request_method = scope.get("method", "UNKNOWN")
        request_path = scope.get("path", "/")

        with self.provider.start_as_current_span(
            name=f"{request_method} {request_path}",
            trace_id=correlation_id,
            kind="server",
            attributes={
                "http.method": request_method,
                "http.url": request_path,
                "http.scheme": scope.get("scheme", "http"),
                "http.host": dict(scope.get("headers", [])).get(b"host", b"").decode(),
                "correlation_id": correlation_id,
            },
        ) as span:
            start = time.perf_counter()
            status_code = 500

            async def send_wrapper(message: dict):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                span.set_attribute("http.status_code", status_code)
                span.set_attribute("http.response_time_ms", round(duration_ms, 2))
                if status_code >= 400:
                    span.set_attribute("error", True)

        _correlation_id.set("")
        _trace_id_var.set("")


def get_tracer(provider: TracerProvider | None = None) -> TracerProvider:
    return provider or _default_provider


_default_provider = TracerProvider()
tracer = _default_provider
