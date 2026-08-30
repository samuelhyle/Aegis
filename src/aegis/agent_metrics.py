from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMetric:
    agent_name: str
    operation: str
    duration_ms: float
    success: bool
    retry_count: int = 0
    error_type: str | None = None
    timestamp: float = field(default_factory=time.time)


class AgentMetricsCollector:
    """Collects agent-specific Prometheus-compatible metrics."""

    def __init__(self):
        self._invocations: dict[str, int] = defaultdict(int)
        self._successes: dict[str, int] = defaultdict(int)
        self._failures: dict[str, int] = defaultdict(int)
        self._durations: dict[str, list[float]] = defaultdict(list)
        self._retries: dict[str, int] = defaultdict(int)
        self._errors: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._active: dict[str, int] = defaultdict(int)

    def record_invocation(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        retry_count: int = 0,
        error_type: str | None = None,
    ):
        self._invocations[agent_name] += 1
        self._durations[agent_name].append(duration_ms)
        if success:
            self._successes[agent_name] += 1
        else:
            self._failures[agent_name] += 1
        self._retries[agent_name] += retry_count
        if error_type:
            self._errors[agent_name][error_type] += 1

    @contextmanager
    def track(
        self,
        agent_name: str,
        retries: int = 0,
    ) -> Generator[dict[str, Any], None, None]:
        self._active[agent_name] += 1
        meta: dict[str, Any] = {"retries": retries, "success": False, "error_type": None}
        start = time.perf_counter()
        try:
            yield meta
        except Exception as e:
            meta["error_type"] = type(e).__name__
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._active[agent_name] -= 1
            self.record_invocation(
                agent_name=agent_name,
                duration_ms=duration_ms,
                success=meta["success"],
                retry_count=meta["retries"],
                error_type=meta["error_type"],
            )

    def get_agent_summary(self, agent_name: str) -> dict[str, Any]:
        invocations = self._invocations.get(agent_name, 0)
        successes = self._successes.get(agent_name, 0)
        failures = self._failures.get(agent_name, 0)
        durations = self._durations.get(agent_name, [])
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "agent": agent_name,
            "invocations": invocations,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / invocations if invocations > 0 else 0,
            "avg_duration_ms": round(avg_duration, 2),
            "p50_duration_ms": round(sorted(durations)[len(durations) // 2], 2) if durations else 0,
            "p95_duration_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2) if durations else 0,
            "total_retries": self._retries.get(agent_name, 0),
            "active": self._active.get(agent_name, 0),
            "error_types": dict(self._errors.get(agent_name, {})),
        }

    def get_all_summaries(self) -> dict[str, dict[str, Any]]:
        agents = set(self._invocations.keys()) | set(self._active.keys())
        return {agent: self.get_agent_summary(agent) for agent in agents}

    def get_prometheus_format(self) -> str:
        lines = []
        for agent in set(self._invocations.keys()) | set(self._active.keys()):
            lines.append(f"# HELP aegis_agent_invocations_total Total invocations for {agent}")
            lines.append("# TYPE aegis_agent_invocations_total counter")
            lines.append(f'aegis_agent_invocations_total{{agent="{agent}"}} {self._invocations.get(agent, 0)}')

            lines.append(f"# HELP aegis_agent_successes_total Total successes for {agent}")
            lines.append("# TYPE aegis_agent_successes_total counter")
            lines.append(f'aegis_agent_successes_total{{agent="{agent}"}} {self._successes.get(agent, 0)}')

            lines.append(f"# HELP aegis_agent_failures_total Total failures for {agent}")
            lines.append("# TYPE aegis_agent_failures_total counter")
            lines.append(f'aegis_agent_failures_total{{agent="{agent}"}} {self._failures.get(agent, 0)}')

            durations = self._durations.get(agent, [])
            if durations:
                sorted_d = sorted(durations)
                lines.append("# HELP aegis_agent_duration_ms Agent execution duration")
                lines.append("# TYPE aegis_agent_duration_ms histogram")
                lines.append(f'aegis_agent_duration_ms_count{{agent="{agent}"}} {len(sorted_d)}')
                lines.append(f'aegis_agent_duration_ms_sum{{agent="{agent}"}} {sum(sorted_d):.2f}')

            lines.append(f"# HELP aegis_agent_retries_total Total retries for {agent}")
            lines.append("# TYPE aegis_agent_retries_total counter")
            lines.append(f'aegis_agent_retries_total{{agent="{agent}"}} {self._retries.get(agent, 0)}')

            lines.append(f"# HELP aegis_agent_active Currently active invocations for {agent}")
            lines.append("# TYPE aegis_agent_active gauge")
            lines.append(f'aegis_agent_active{{agent="{agent}"}} {self._active.get(agent, 0)}')

        return "\n".join(lines)

    def reset(self):
        self._invocations.clear()
        self._successes.clear()
        self._failures.clear()
        self._durations.clear()
        self._retries.clear()
        self._errors.clear()
        self._active.clear()


agent_metrics = AgentMetricsCollector()
