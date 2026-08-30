"""Enhanced agent system with retry logic, timeout, caching, and performance metrics."""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from functools import wraps
from typing import Any, TypeVar

from .models import AgentResult
from .store import SyntheaStore

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------

class AgentCapability(StrEnum):
    """Agent capabilities for capability negotiation."""
    TIMELINE_ANALYSIS = "timeline_analysis"
    MEDICATION_REVIEW = "medication_review"
    EVIDENCE_COLLECTION = "evidence_collection"
    CRITIQUE = "critique"
    DIAGNOSIS = "diagnosis"
    TREATMENT_ANALYSIS = "treatment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TEMPORAL_REASONING = "temporal_reasoning"


@dataclass
class AgentConfig:
    """Configuration for agent execution."""
    name: str
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_base_delay: float = 0.1
    retry_max_delay: float = 5.0
    retry_exponential_base: float = 2.0
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    capabilities: list[AgentCapability] = field(default_factory=list)


# Default agent configurations
DEFAULT_AGENT_CONFIGS: dict[str, AgentConfig] = {
    "timeline": AgentConfig(
        name="timeline",
        timeout_seconds=30.0,
        max_retries=3,
        capabilities=[AgentCapability.TIMELINE_ANALYSIS, AgentCapability.EVIDENCE_COLLECTION],
    ),
    "medication": AgentConfig(
        name="medication",
        timeout_seconds=25.0,
        max_retries=3,
        capabilities=[AgentCapability.MEDICATION_REVIEW, AgentCapability.EVIDENCE_COLLECTION],
    ),
    "evidence": AgentConfig(
        name="evidence",
        timeout_seconds=35.0,
        max_retries=2,
        capabilities=[AgentCapability.EVIDENCE_COLLECTION],
    ),
    "critic": AgentConfig(
        name="critic",
        timeout_seconds=20.0,
        max_retries=2,
        capabilities=[AgentCapability.CRITIQUE],
    ),
}


# ---------------------------------------------------------------------------
# Agent Cache
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    """Cached agent result."""
    result: AgentResult
    timestamp: datetime
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() - self.timestamp > timedelta(seconds=self.ttl_seconds)


class AgentResultCache:
    """Cache for agent results with TTL-based expiration."""

    def __init__(self, default_ttl: int = 300):
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _make_key(self, agent_name: str, patient_id: str, question: str) -> str:
        """Generate cache key from agent parameters."""
        data = f"{agent_name}:{patient_id}:{question}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, agent_name: str, patient_id: str, question: str) -> AgentResult | None:
        """Get cached result if available and not expired."""
        key = self._make_key(agent_name, patient_id, question)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.result

    def set(self, agent_name: str, patient_id: str, question: str, result: AgentResult, ttl: int | None = None) -> None:
        """Cache an agent result."""
        key = self._make_key(agent_name, patient_id, question)
        self._cache[key] = CacheEntry(
            result=result,
            timestamp=datetime.utcnow(),
            ttl_seconds=ttl or self._default_ttl,
        )

    def invalidate(self, agent_name: str, patient_id: str, question: str) -> bool:
        """Invalidate a cached entry."""
        key = self._make_key(agent_name, patient_id, question)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
            "entries": len(self._cache),
        }


# ---------------------------------------------------------------------------
# Agent Performance Metrics
# ---------------------------------------------------------------------------

@dataclass
class AgentMetrics:
    """Performance metrics for an agent."""
    agent_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    last_run_at: datetime | None = None
    retry_counts: dict[int, int] = field(default_factory=dict)

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_runs if self.total_runs > 0 else 0.0

    @property
    def success_rate(self) -> float:
        return self.successful_runs / self.total_runs if self.total_runs > 0 else 0.0

    def record_run(self, duration_ms: float, success: bool, retries: int = 0) -> None:
        """Record an agent run."""
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1

        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.last_run_at = datetime.utcnow()

        self.retry_counts[retries] = self.retry_counts.get(retries, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2) if self.min_duration_ms != float("inf") else 0,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "retry_distribution": self.retry_counts,
        }


class AgentMetricsCollector:
    """Collects and aggregates metrics across all agents."""

    def __init__(self):
        self._metrics: dict[str, AgentMetrics] = {}

    def record(self, agent_name: str, duration_ms: float, success: bool, retries: int = 0) -> None:
        """Record an agent run."""
        if agent_name not in self._metrics:
            self._metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        self._metrics[agent_name].record_run(duration_ms, success, retries)

    def get_agent_metrics(self, agent_name: str) -> AgentMetrics | None:
        """Get metrics for a specific agent."""
        return self._metrics.get(agent_name)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all agents."""
        return {name: metrics.to_dict() for name, metrics in self._metrics.items()}

    def get_summary(self) -> dict[str, Any]:
        """Get summary metrics across all agents."""
        total_runs = sum(m.total_runs for m in self._metrics.values())
        successful_runs = sum(m.successful_runs for m in self._metrics.values())
        total_duration = sum(m.total_duration_ms for m in self._metrics.values())

        return {
            "total_agents": len(self._metrics),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0.0,
            "avg_duration_ms": total_duration / total_runs if total_runs > 0 else 0.0,
        }


# Global metrics collector
agent_metrics_collector = AgentMetricsCollector()


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator for retrying function calls with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        break

                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Enhanced Agent Base
# ---------------------------------------------------------------------------

class EnhancedAgent(ABC):
    """Enhanced abstract base class with retry, timeout, caching, and metrics."""

    name: str = "base"

    def __init__(self, store: SyntheaStore, config: AgentConfig | None = None):
        self.store = store
        self.config = config or DEFAULT_AGENT_CONFIGS.get(self.name, AgentConfig(name=self.name))
        self.cache = AgentResultCache(default_ttl=self.config.cache_ttl_seconds)
        self.metrics = AgentMetrics(agent_name=self.name)

    def run_with_features(
        self,
        patient_id: str,
        question: str,
        use_cache: bool = True,
        record_metrics: bool = True,
    ) -> AgentResult:
        """Run agent with retry, timeout, caching, and metrics."""
        start_time = time.perf_counter()
        retries = 0
        last_exception = None

        # Check cache first
        if use_cache and self.config.cache_enabled:
            cached = self.cache.get(self.name, patient_id, question)
            if cached is not None:
                return cached

        # Retry loop
        for attempt in range(self.config.max_retries + 1):
            retries = attempt
            try:
                # Run with timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.run, patient_id, question)
                    result = future.result(timeout=self.config.timeout_seconds)

                # Record success
                duration_ms = (time.perf_counter() - start_time) * 1000

                if record_metrics:
                    self.metrics.record_run(duration_ms, success=True, retries=retries)
                    agent_metrics_collector.record(self.name, duration_ms, success=True, retries=retries)

                # Cache result
                if use_cache and self.config.cache_enabled:
                    self.cache.set(self.name, patient_id, question, result)

                return result

            except FuturesTimeoutError:
                last_exception = TimeoutError(f"Agent {self.name} timed out after {self.config.timeout_seconds}s")
            except Exception as e:
                last_exception = e

            # Exponential backoff before retry
            if attempt < self.config.max_retries:
                delay = min(
                    self.config.retry_base_delay * (self.config.retry_exponential_base ** attempt),
                    self.config.retry_max_delay
                )
                time.sleep(delay)

        # All retries failed
        duration_ms = (time.perf_counter() - start_time) * 1000

        if record_metrics:
            self.metrics.record_run(duration_ms, success=False, retries=retries)
            agent_metrics_collector.record(self.name, duration_ms, success=False, retries=retries)

        # Return error result
        return AgentResult(
            agent=self.name,
            status="failed",
            summary=f"Agent failed after {retries} retries: {str(last_exception)}",
            evidence=[],
            confidence=0.0,
            duration_ms=duration_ms,
        )

    @abstractmethod
    def run(self, patient_id: str, question: str) -> AgentResult:
        """Run the agent's investigation (to be implemented by subclasses)."""
        ...

    def _safe_rows(self, table: str, patient_id: str) -> list[dict[str, Any]]:
        """Safely get rows from the store, returning empty list on error."""
        try:
            return self.store.rows(table, patient_id)
        except Exception:
            return []

    def get_capabilities(self) -> list[AgentCapability]:
        """Get agent capabilities."""
        return self.config.capabilities

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.config.capabilities


# ---------------------------------------------------------------------------
# Enhanced Agent Implementations
# ---------------------------------------------------------------------------

class EnhancedTimelineAgent(EnhancedAgent):
    """Enhanced timeline agent with retry and caching."""

    name = "timeline"

    def __init__(self, store: SyntheaStore, config: AgentConfig | None = None):
        super().__init__(store, config or DEFAULT_AGENT_CONFIGS["timeline"])

    def run(self, patient_id: str, question: str) -> AgentResult:
        from time import perf_counter
        t = perf_counter()

        encounters = self._safe_rows("encounters", patient_id)
        conditions = self._safe_rows("conditions", patient_id)
        observations = self._safe_rows("observations", patient_id)
        procedures = self._safe_rows("procedures", patient_id)

        total = len(encounters) + len(conditions) + len(observations) + len(procedures)

        summary_parts = []
        evidence = []

        if encounters:
            summary_parts.append(f"{len(encounters)} encounters")
            evidence.append(f"encounters={len(encounters)}")
        if conditions:
            summary_parts.append(f"{len(conditions)} conditions")
            evidence.append(f"conditions={len(conditions)}")
        if observations:
            summary_parts.append(f"{len(observations)} observations")
            evidence.append(f"observations={len(observations)}")
        if procedures:
            summary_parts.append(f"{len(procedures)} procedures")
            evidence.append(f"procedures={len(procedures)}")

        if summary_parts:
            summary = f"Timeline: {', '.join(summary_parts)}."
        else:
            summary = "No timeline data found for this patient."

        confidence = min(0.5 + (total * 0.02), 0.85) if total > 0 else 0.3

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            duration_ms=(perf_counter() - t) * 1000,
        )


class EnhancedMedicationAgent(EnhancedAgent):
    """Enhanced medication agent with retry and caching."""

    name = "medication"

    def __init__(self, store: SyntheaStore, config: AgentConfig | None = None):
        super().__init__(store, config or DEFAULT_AGENT_CONFIGS["medication"])

    def run(self, patient_id: str, question: str) -> AgentResult:
        from time import perf_counter
        t = perf_counter()

        meds = self._safe_rows("medications", patient_id)
        allergies = self._safe_rows("allergies", patient_id)

        summary_parts = []
        evidence = []

        if meds:
            summary_parts.append(f"{len(meds)} medication records")
            evidence.append(f"medication_records={len(meds)}")
        if allergies:
            summary_parts.append(f"{len(allergies)} allergies")
            evidence.append(f"allergies={len(allergies)}")

        if summary_parts:
            summary = f"Medications: {', '.join(summary_parts)}."
        else:
            summary = "No medication data found for this patient."

        confidence = min(0.5 + (len(meds) * 0.05), 0.85) if meds else 0.3

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            duration_ms=(perf_counter() - t) * 1000,
        )


class EnhancedEvidenceAgent(EnhancedAgent):
    """Enhanced evidence agent with retry and caching."""

    name = "evidence"

    def __init__(self, store: SyntheaStore, config: AgentConfig | None = None):
        super().__init__(store, config or DEFAULT_AGENT_CONFIGS["evidence"])

    def run(self, patient_id: str, question: str) -> AgentResult:
        from time import perf_counter
        t = perf_counter()

        evidence_sources = []
        total_records = 0

        for table in ["conditions", "medications", "observations", "procedures", "allergies", "careplans", "immunizations"]:
            rows = self._safe_rows(table, patient_id)
            if rows:
                evidence_sources.append(f"{table}={len(rows)}")
                total_records += len(rows)

        patient = self.store.patient(patient_id)
        if patient:
            evidence_sources.insert(0, "patient_record")

        summary = f"Evidence collected from {len(evidence_sources)} sources ({total_records} total records)."
        confidence = min(0.5 + (total_records * 0.01), 0.8) if total_records > 0 else 0.3

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            evidence=evidence_sources,
            confidence=confidence,
            duration_ms=(perf_counter() - t) * 1000,
        )


class EnhancedCriticAgent(EnhancedAgent):
    """Enhanced critic agent with retry and caching."""

    name = "critic"

    def __init__(self, store: SyntheaStore, config: AgentConfig | None = None):
        super().__init__(store, config or DEFAULT_AGENT_CONFIGS["critic"])

    def run(self, patient_id: str, question: str) -> AgentResult:
        from time import perf_counter
        t = perf_counter()

        issues = []
        warnings = []

        patient = self.store.patient(patient_id)
        if not patient:
            issues.append("Patient not found in dataset")

        conditions = self._safe_rows("conditions", patient_id)
        meds = self._safe_rows("medications", patient_id)

        if not conditions:
            warnings.append("No conditions recorded")
        if not meds:
            warnings.append("No medications recorded")

        if issues:
            summary = f"Critic found {len(issues)} issues: {'; '.join(issues)}"
            confidence = 0.3
        elif warnings:
            summary = f"Critic notes {len(warnings)} warnings: {'; '.join(warnings)}. Recommend human review."
            confidence = 0.6
        else:
            summary = "No critical issues found. Recommend human review for medical interpretation."
            confidence = 0.8

        evidence = ["safety_boundary", "human_review_required"]
        if issues:
            evidence.extend([f"issue:{i}" for i in issues])
        if warnings:
            evidence.extend([f"warning:{w}" for w in warnings])

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            duration_ms=(perf_counter() - t) * 1000,
        )


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Registry of available agents with capability negotiation."""

    def __init__(self):
        self._agents: dict[str, EnhancedAgent] = {}

    def register(self, agent: EnhancedAgent) -> None:
        """Register an agent."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> EnhancedAgent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "name": agent.name,
                "capabilities": [cap.value for cap in agent.config.capabilities],
                "config": {
                    "timeout_seconds": agent.config.timeout_seconds,
                    "max_retries": agent.config.max_retries,
                    "cache_enabled": agent.config.cache_enabled,
                },
            }
            for agent in self._agents.values()
        ]

    def get_agents_with_capability(self, capability: AgentCapability) -> list[EnhancedAgent]:
        """Get all agents that have a specific capability."""
        return [
            agent for agent in self._agents.values()
            if agent.has_capability(capability)
        ]

    def get_agents_for_capabilities(self, capabilities: list[AgentCapability]) -> list[EnhancedAgent]:
        """Get agents that cover all required capabilities."""
        result = []
        for agent in self._agents.values():
            if any(cap in agent.config.capabilities for cap in capabilities):
                result.append(agent)
        return result


# Global agent registry
agent_registry = AgentRegistry()


def init_agent_registry(store: SyntheaStore) -> AgentRegistry:
    """Initialize the agent registry with default agents."""
    registry = AgentRegistry()

    registry.register(EnhancedTimelineAgent(store))
    registry.register(EnhancedMedicationAgent(store))
    registry.register(EnhancedEvidenceAgent(store))
    registry.register(EnhancedCriticAgent(store))

    return registry
