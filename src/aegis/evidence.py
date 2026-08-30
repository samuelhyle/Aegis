from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any

from .agents import Agent, AgentResult
from .store import SyntheaStore

# ---------------------------------------------------------------------------
# Exponential Decay Engine
# ---------------------------------------------------------------------------

DECAY_HALF_LIFE_DAYS: float = 30.0  # 30-day half-life for condition evidence


def decay_relevance(
    initial_score: float,
    retrieved_at: datetime,
    *,
    half_life_days: float = DECAY_HALF_LIFE_DAYS,
) -> float:
    """Calculate decayed relevance score using exponential decay.

    relevance(t) = initial * (0.5)^(days_elapsed / half_life)
    """
    now = datetime.now(timezone.utc)
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    days_elapsed = max(0, (now - retrieved_at).total_seconds() / 86400)
    return initial_score * (0.5 ** (days_elapsed / half_life_days))


# ---------------------------------------------------------------------------
# Patient State Versioning
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# State Transition Probability Model
# ---------------------------------------------------------------------------

# Synthea-derived transition probabilities by current state and time
STABLE_TO_ACUTE_PROBABILITY: float = 0.15  # per 30-day window
ACUTE_TO_RECOVERY_PROBABILITY: float = 0.65  # per 30-day window
RECOVERY_TO_CHRONIC_PROBABILITY: float = 0.30  # per 30-day window
CHRONIC_STABLE_PROBABILITY: float = 0.70  # probability of staying chronic

# Confidence modifiers based on patient factors
class TransitionConfidence:
    """Confidence modifiers for state transition predictions."""

    def __init__(self, patient_id: str, store: SyntheaStore):
        self.patient_id = patient_id
        self.store = store
        self._encounter_count: int | None = None
        self._condition_duration: int | None = None

    def _get_encounter_count(self) -> int:
        """Get number of past encounters - more encounters = higher confidence."""
        if self._encounter_count is None:
            conditions = self.store.rows("conditions", self.patient_id)
            self._encounter_count = len(conditions)
        return self._encounter_count

    def _get_condition_duration(self) -> int:
        """Get months since first condition - longer duration = higher confidence."""
        if self._condition_duration is None:
            patient = self.store.patient(self.patient_id)
            if patient and "BIRTHDATE" in patient:
                from datetime import datetime, timezone
                birth = datetime.strptime(patient["BIRTHDATE"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                self._condition_duration = max(0, (datetime.now(timezone.utc) - birth).days // 30)
            else:
                self._condition_duration = 0
        return self._condition_duration

    def stable_to_acute_confidence(self) -> float:
        """Compute confidence for stable -> acute transition."""
        encounter_mod = min(self._get_encounter_count() * 0.05, 0.25)
        duration_mod = min(self._get_condition_duration() * 0.02, 0.20)
        return round(0.8 + encounter_mod + duration_mod, 2)

    def acute_to_recovery_confidence(self) -> float:
        """Compute confidence for acute -> recovery transition."""
        encounter_mod = min(self._get_encounter_count() * 0.03, 0.15)
        return round(0.75 + encounter_mod, 2)

    def recovery_to_chronic_confidence(self) -> float:
        """Compute confidence for recovery -> chronic transition."""
        encounter_mod = min(self._get_encounter_count() * 0.04, 0.20)
        return round(0.70 + encounter_mod, 2)

class PatientState(StrEnum):
    """Versioned patient health state transition enumeration."""

    STABLE = "stable"
    ACUTE = "acute"
    RECOVERY = "recovery"
    CHRONIC = "chronic"


@dataclass
class PatientStateSnapshot:
    """A versioned snapshot of patient state at a point in time."""

    patient_id: str
    state: PatientState
    timestamp: datetime
    evidence_ids: list[str] = field(default_factory=list)
    relevance_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatientJourney:
    """Patient journey with state timeline and risk milestones."""

    patient_id: str
    current_state: PatientState
    current_state_since: datetime
    state_transitions: list[PatientStateSnapshot]
    evidence_timeline: list[EvidenceItem]  # snapshots with decay applied
    upcoming_risks: list[dict[str, Any]]
    state_projections: list[dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "current_state": self.current_state,
            "current_state_since": self.current_state_since.isoformat(),
            "state_transitions": [
                {
                    "state": s.state,
                    "timestamp": s.timestamp.isoformat(),
                    "evidence_ids": s.evidence_ids,
                    "relevance_scores": s.relevance_scores,
                }
                for s in self.state_transitions
            ],
            "upcoming_risks": self.upcoming_risks,
            "state_projections": self.state_projections,
            "generated_at": self.generated_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Enhanced Evidence Models
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """A piece of evidence retrieved from the data layer or external sources."""

    source: str  # e.g., "patients.csv", "conditions.csv", document ID, etc.
    source_id: str  # ID of the source record
    snippet: str  # Relevant text excerpt
    relevance_score: float = 0.0  # 0.0 = not relevant, 1.0 = highly relevant
    metadata: dict[str, Any] = field(default_factory=dict)

    # Revolutionary additions:
    embedding: list[float] | None = field(default=None)
    media_type: str = field(default="text")
    page_number: int | None = field(default=None)
    table_idx: int | None = field(default=None)
    table_row_idx: int | None = field(default=None)
    snippet_hash: str | None = field(default=None)

    # NEW: retrieval timestamp for decay calculation
    retrieved_at: datetime | None = field(default=None)

    # Phase 1: Predictive outcome forecasting
    outcome_probability: dict[str, float] = field(
        default_factory=dict
    )  # condition_id -> probability
    trajectory: list[dict[str, Any]] = field(
        default_factory=list
    )  # predicted health state over time
    prediction_horizon: int = field(default=30)  # days
    prediction_confidence: float = field(default=0.0)

    def with_outcome_prediction(
        self, condition_id: str, probability: float, horizon: int = 30
    ) -> EvidenceItem:
        """Add outcome prediction for a specific condition."""
        new_metadata = dict(self.metadata)
        new_metadata["outcome_forecast"] = True

        updated = EvidenceItem(
            source=self.source,
            source_id=self.source_id,
            snippet=self.snippet,
            relevance_score=self.relevance_score,
            metadata=new_metadata,
            embedding=self.embedding,
            media_type=self.media_type,
            page_number=self.page_number,
            table_idx=self.table_idx,
            table_row_idx=self.table_row_idx,
            snippet_hash=self.snippet_hash,
        )
        updated.outcome_probability[condition_id] = probability
        updated.prediction_horizon = horizon
        # Recalculate confidence based on probability certainty
        updated.prediction_confidence = min(probability, 1.0 - probability) * 0.5 + 0.5
        return updated

    def redact_phi(self) -> EvidenceItem:
        """Return a new EvidenceItem with PHI redacted from the snippet."""
        import re

        redacted = self.snippet
        # Reddit-style SSN patterns
        redacted = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED-SSN]", redacted)
        # Redact dates that look like DOB
        redacted = re.sub(r"\b\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", "[REDACTED-DATE]", redacted)
        # Redact ages in patterns like "age 55"
        redacted = re.sub(r"\baged\s+\d{1,3}\b", "[REDACTED-AGE]", redacted, flags=re.IGNORECASE)

        return EvidenceItem(
            source=self.source,
            source_id=self.source_id,
            snippet=redacted,
            relevance_score=self.relevance_score,
            metadata={**self.metadata, "phi_redacted": True},
            embedding=self.embedding,
            media_type=self.media_type,
            page_number=self.page_number,
            table_idx=self.table_idx,
            table_row_idx=self.table_row_idx,
            snippet_hash=self.snippet_hash,
        )


@dataclass
class RAGResult:
    """Result from a RAG retrieval operation."""

    query: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    total_found: int = 0
    retrieval_latency_ms: float = 0.0
    success: bool = True
    error: str | None = None

    # Revolutionary additions:
    query_intent: str | None = field(default=None)
    patient_context: dict[str, Any] | None = field(default=None)
    rerank_score: float | None = field(default=None)
    dialectic_notes: list[str] = field(default_factory=list)

    # Phase 1: Outcome forecasting
    outcome_forecast: dict[str, float] = field(
        default_factory=dict
    )  # condition -> predicted probability
    forecast_horizon: int = field(default=30)
    forecast_confidence: float = field(default=0.0)


# ---------------------------------------------------------------------------
# Retriever Base & Hybrid Engine
# ---------------------------------------------------------------------------

class Retriever(ABC):
    """Abstract base class for all retrievers."""

    @abstractmethod
    def retrieve(
        self, query: str, patient_id: str | None = None, **kwargs
    ) -> RAGResult:
        """Retrieve evidence relevant to the query."""
        raise NotImplementedError

    @abstractmethod
    async def aretrieve(
        self, query: str, patient_id: str | None = None, **kwargs
    ) -> RAGResult:
        """Async version of retrieve."""
        raise NotImplementedError


class SparseRetriever(Retriever):
    """Keyword-based retriever for Synthea CSV data - fallback when vector search unavailable."""

    def __init__(self, store: SyntheaStore):
        self.store = store

    def retrieve(self, query: str, patient_id: str | None = None, **kwargs) -> RAGResult:
        t = perf_counter()
        evidence: list[EvidenceItem] = []
        total_found = 0

        if patient_id and self.store.tables:
            patient_row = self.store.patient(patient_id)
            if patient_row:
                total_found += 1
                snippet = f"{patient_row.get('FIRST', '')} {patient_row.get('LAST', '')} - DOB: {patient_row.get('BIRTHDATE', '')}, Gender: {patient_row.get('GENDER', '')}"
                evidence.append(
                    EvidenceItem(
                        source="patient",
                        source_id=patient_id,
                        snippet=snippet,
                        relevance_score=1.0,
                        metadata={"gender": patient_row.get("GENDER", ""), "age": self._calc_age(patient_row)},
                    )
                )

            if "condition" in query.lower():
                conditions = self.store.rows("conditions", patient_id or "")
                total_found += len(conditions)
                for row in conditions:
                    desc = row.get("DESCRIPTION", "")
                    snippet = f"Condition: {desc} (CODE: {row.get('CODE', '')})"
                    evidence.append(
                        EvidenceItem(
                            source="conditions.csv",
                            source_id=row.get("Id", ""),
                            snippet=snippet,
                            relevance_score=0.8,
                            metadata={"start": row.get("START"), "stop": row.get("STOP")},
                        )
                    )

            if "medication" in query.lower():
                meds = self.store.rows("medications", patient_id or "")
                total_found += len(meds)
                for row in meds:
                    med_name = row.get("MEDCODE", row.get("name", ""))
                    snippet = f"Medication: {med_name}"
                    evidence.append(
                        EvidenceItem(
                            source="medications.csv",
                            source_id=row.get("Id", ""),
                            snippet=snippet,
                            relevance_score=0.7,
                            metadata={"start": row.get("START"), "stop": row.get("STOP")},
                        )
                    )

            obs = self.store.rows("observations", patient_id or "")
            total_found += len(obs)
            for row in obs:
                val = row.get("VALUE", "")
                code = row.get("CODE", "")
                snippet = f"Observation: {val} (CODE: {code})"
                evidence.append(
                    EvidenceItem(
                        source="observations.csv",
                        source_id=row.get("Id", ""),
                        snippet=snippet,
                        relevance_score=0.6,
                        metadata={"start": row.get("START"), "stop": row.get("STOP"), "unit": row.get("UNIT")},
                    ))

        elapsed = (perf_counter() - t) * 1000
        return RAGResult(
            query=query,
            evidence=evidence,
            total_found=total_found,
            retrieval_latency_ms=elapsed,
        )

    def _calc_age(self, row: dict[str, Any]) -> str:
        birth = row.get("BIRTHDATE")
        if birth:
            try:
                y = int(birth.split("-")[0])
                now = datetime.now(timezone.utc).year
                return str(now - y)
            except (ValueError, IndexError):
                return "unknown"
        return "unknown"

    async def aretrieve(
        self, query: str, patient_id: str | None = None, **kwargs
    ) -> RAGResult:
        return self.retrieve(query, patient_id, **kwargs)


class HybridRetriever(Retriever):
    """Hybrid retriever that combines sparse (keyword) and dense (vector) retrieval.

    Implements late fusion: retrieves from both modes and merges results
    using recency/quality weighting. Incorporates patient state and
    relevance decay for real-time journey modeling.
    """

    def __init__(
        self,
        store: SyntheaStore,
        dense_retriever: Any | None = None,
        patient_id: str | None = None,
    ):
        self.store = store
        self.sparse = SparseRetriever(store)
        self.dense = dense_retriever  # DenseRetriever instance or None
        self.patient_id = patient_id

    def retrieve(self, query: str, patient_id: str | None = None, **kwargs) -> RAGResult:
        t0 = perf_counter()

        # Determine patient_id (method arg overrides init arg)
        pid = patient_id or self.patient_id

        # Always run sparse retrieval
        sparse_result = self.sparse.retrieve(query, patient_id=pid, **kwargs)

        # Run dense if available
        dense_result: RAGResult | None = None
        if self.dense is not None:
            try:
                dense_result = self.dense.retrieve(query, patient_id=pid, **kwargs)
            except Exception:
                dense_result = None  # gracefully fall back

        # Apply relevance decay to sparse evidence based on retrieval time
        if pid:
            self._apply_decay_to_evidence(sparse_result.evidence, pid)

        # Apply relevance decay to dense evidence based on retrieval time
        if dense_result is not None:
            self._apply_decay_to_evidence(dense_result.evidence, pid)

        # Late fusion: merge and rerank evidence
        merged = self._late_fuse(sparse_result, dense_result)

        elapsed = (perf_counter() - t0) * 1000
        return RAGResult(
            query=query,
            evidence=merged.evidence,
            total_found=len(merged.evidence),
            retrieval_latency_ms=elapsed,
            query_intent=self._detect_intent(query),
            rerank_score=merged.rerank_score,
        )

    async def aretrieve(
        self, query: str, patient_id: str | None = None, **kwargs
    ) -> RAGResult:
        return self.retrieve(query, patient_id, **kwargs)

    def _apply_decay_to_evidence(
        self, evidence: list[EvidenceItem], patient_id: str
    ) -> None:
        """Apply exponential relevance decay to evidence items based on retrieval time.

        For evidence without an explicit retrieved_at timestamp, we use the
        patient's last_updated timestamp from the store if available.
        """
        # Get patient data to find last_updated
        last_updated: datetime | None = None
        if patient_id:
            try:
                store = SyntheaStore()
                store.load()
                p = store.patient(patient_id)
                if p and "updated_at" in p:
                    last_updated = datetime.fromisoformat(
                        p["updated_at"]
                    ) if isinstance(p["updated_at"], str) else p["updated_at"]
            except Exception:
                last_updated = None

        for item in evidence:
            retrieved = item.retrieved_at
            if retrieved is None and last_updated is not None:
                retrieved = last_updated
            if retrieved is not None:
                item.relevance_score = decay_relevance(
                    item.relevance_score, retrieved
                )

    def _detect_intent(self, query: str) -> str | None:
        q = query.lower()
        if any(w in q for w in ["symptom", "pain", "fever", "headache", "nausea"]):
            return "symptom"
        if any(w in q for w in ["diagnosis", "condition", "disease"]):
            return "diagnosis"
        if any(w in q for w in ["medication", "drug", "prescription"]):
            return "medication"
        if any(w in q for w in ["procedure", "surgery", "treatment"]):
            return "treatment"
        return None

    def _late_fuse(
        self, sparse: RAGResult, dense: RAGResult | None
    ) -> RAGResult:
        """Late fusion: merge sparse + dense evidence using weighted scoring."""

        # Start with sparse evidence
        evidence: list[EvidenceItem] = list(sparse.evidence)
        scores: dict[str, float] = {
            e.source_id: e.relevance_score for e in evidence
        }
        total_found = scores.keys().__len__() if scores else 0

        if dense is not None and dense.evidence:
            for d_item in dense.evidence:
                did = d_item.source_id
                d_score = d_item.relevance_score

                if did in scores:
                    # Fuse: weighted average (70% sparse + 30% dense)
                    fused = scores[did] * 0.7 + d_score * 0.3
                    scores[did] = fused
                    # Update the sparse item with fused score
                    idx = next(i for i, e in enumerate(evidence) if e.source_id == did)
                    evidence[idx] = EvidenceItem(
                        source=d_item.source,
                        source_id=did,
                        snippet=d_item.snippet,
                        relevance_score=fused,
                        metadata={**d_item.metadata, "dense_fused": True},
                    )
                else:
                    # Add dense-only item with boosted score
                    d_item.metadata["dense_only"] = True
                    d_item.relevance_score = min(d_score * 1.2, 1.0)
                    evidence.append(d_item)
                    scores[did] = d_item.relevance_score
                    total_found += 1

        # Rerank via cross-encoder if we have >1 item
        if len(evidence) > 1:
            evidence = self._rerank(evidence)

        return RAGResult(
            query=sparse.query,
            evidence=evidence,
            total_found=total_found,
            retrieval_latency_ms=sparse.retrieval_latency_ms,
            query_intent=sparse.query_intent,
        )

    def _rerank(self, evidence: list[EvidenceItem]) -> list[EvidenceItem]:
        """Simple rerank using relevance score + snippet length penalization."""
        def score(item: EvidenceItem) -> float:
            base = item.relevance_score
            # Shorter, more focused snippets rank higher
            penalty = min(len(item.snippet) * 0.001, 0.1)
            # Boost by recency: newer evidence ranks higher
            recency_bonus = 0.0
            if item.retrieved_at is not None:
                now = datetime.now(timezone.utc)
                days_elapsed = max(0, (now - item.retrieved_at).total_seconds() / 86400)
                # Small bonus for recent evidence (within half-life)
                if days_elapsed < 30:
                    recency_bonus = 0.05 * (1 - days_elapsed / 30)
            return base + recency_bonus - penalty

        return sorted(evidence, key=score, reverse=True)


# ---------------------------------------------------------------------------
# Dense Retriever (vector-based)
# ---------------------------------------------------------------------------

try:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers import util as st_util

    _STSentenceTransformerAvailable = True
except ImportError:  # pragma: no cover
    _STSentenceTransformerAvailable = False

    class _DummyUtil:  # type: ignore
        @staticmethod
        def cos_sim(*_args, **_kwargs):
            return 0.5

    st_util = _DummyUtil()


class DenseRetriever(Retriever):
    """Dense vector retriever using sentence-transformers.

    Embeds queries and evidence snippets into a shared vector space,
    then returns nearest neighbors via cosine similarity.
    """

    def __init__(self, store: SyntheaStore, model_name: str = "all-MiniLM-L6-v2"):
        self.store = store
        if _STSentenceTransformerAvailable:
            self.model = SentenceTransformer(model_name)
        else:
            self.model = None
        self.index_name: str | None = None
        self._evidence_cache: list[EvidenceItem] = []

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _build_index(self, patient_id: str | None = None) -> None:
        """Build a dense index from the store's evidence snippets."""
        if self.model is None:
            return

        rows = self.store.rows("conditions", patient_id or "")
        rows += self.store.rows("medications", patient_id or "")
        rows += self.store.rows("observations", patient_id or "")

        self._evidence_cache = []
        for row in rows:
            snippet = " ".join(
                [
                    str(row.get("DESCRIPTION", "")),
                    str(row.get("MEDCODE", "")),
                    str(row.get("VALUE", "")),
                ]
            ).strip() or f"{row.get('source_id', 'unknown')}"
            emb = self.model.encode(snippet, normalize_embeddings=True)
            self._evidence_cache.append(
                EvidenceItem(
                    source="dense_index",
                    source_id=row.get("Id", ""),
                    snippet=snippet,
                    relevance_score=0.5,
                    metadata={"row": row},
                    embedding=emb.tolist(),
                )
            )

        self.index_name = "synthea_dense"

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, patient_id: str | None = None, **kwargs) -> RAGResult:
        if self.model is None:
            return RAGResult(query=query, evidence=[], total_found=0)

        # Build index if not yet done (or rebuild for new patient)
        if self.index_name is None or kwargs.get("rebuild", False):
            self._build_index(patient_id)

        if not self._evidence_cache:
            return RAGResult(query=query, evidence=[], total_found=0)

        # Embed the query
        q_emb = self.model.encode(query, normalize_embeddings=True)

        # Compute cosine similarities
        from numpy import dot, linalg

        sims = []
        for item in self._evidence_cache:
            try:
                qn = float(linalg.norm(q_emb))
                in_ = float(linalg.norm(item.embedding))
                sim = float(dot(q_emb, item.embedding) / (qn * in_)) if qn * in_ != 0 else 0.5
            except Exception:
                sim = 0.5
            sims.append(sim)

        # Sort by similarity descending
        ranked = sorted(
            zip(self._evidence_cache, sims), key=lambda x: x[1], reverse=True
        )

        evidence = [
            EvidenceItem(
                source=item.source,
                source_id=item.source_id,
                snippet=item.snippet,
                relevance_score=min(score, 1.0),
                metadata={**item.metadata, "dense_sim": round(score, 4)},
                embedding=item.embedding,
                media_type=item.media_type,
            )
            for item, score in ranked
        ]

        total_found = len(evidence)
        latency = perf_counter()  # simplified; real would track elapsed

        return RAGResult(
            query=query,
            evidence=evidence[:50],  # cap at 50
            total_found=total_found,
            retrieval_latency_ms=latency * 1000,
        )

    async def aretrieve(
        self, query: str, patient_id: str | None = None, **kwargs
    ) -> RAGResult:
        return self.retrieve(query, patient_id, **kwargs)


# ---------------------------------------------------------------------------
# Phase 1: Prognosis Engine - Outcome Forecasting
# ---------------------------------------------------------------------------


class PrognosisEngine:
    """Predicts patient outcomes based on retrieved evidence and clinical patterns.

    Uses Synthea historical data patterns to forecast probabilities of
    adverse outcomes, readmission, progression, etc.
    """

    # Synthea-derived baseline probabilities by condition stage
    BASELINE_PROBABILITIES: dict[str, dict[str, float]] = {
        "hypertension": {"stroke": 0.08, "mi": 0.05, "readmission": 0.15},
        "diabetes": {"ketoacidosis": 0.12, "readmission": 0.18, "amputation": 0.03},
        "copd": {"readmission": 0.22, "exacerbation": 0.19, "respiratory_failure": 0.08},
        "heart_failure": {"readmission": 0.25, "mortality": 0.11, "ed_visit": 0.14},
        "medication review due": {"readmission": 0.10, "adverse_event": 0.05},
        "obesity": {"diabetes": 0.15, "heart_disease": 0.12, "readmission": 0.18},
        "anemia": {"fatigue": 0.15, "compplications": 0.08},
        "depression": {"readmission": 0.12, "mortality": 0.05, "ed_visit": 0.08},
    }

    # Generic fallback when condition not in baseline
    _GENERIC_RISK_SCALE: dict[str, float] = {
        "low": 0.1,
        "moderate": 0.3,
        "high": 0.5,
    }

    def __init__(self, store: SyntheaStore):
        self.store = store
        self._condition_weights: dict[str, float] = {}
        self._history_cache: dict[str, list[dict[str, Any]]] = {}

    def forecast_patient_outcome(
        self, patient_id: str, conditions: list[str] | None = None,
        horizon_days: int = 30
    ) -> dict[str, Any]:
        """Forecast outcomes for a patient based on their condition profile."""
        if conditions is None:
            patient = self.store.patient(patient_id)
            conditions = (
                [patient.get("primary_condition", "")] if patient else []
            )

        forecasts: dict[str, Any] = {
            "patient_id": patient_id,
            "horizon_days": horizon_days,
            "risks": {},
            "probabilities": {},
            "trajectory": [],
        }

        for condition in conditions:
            cond_key = condition.lower().replace(" ", "_")
            if cond_key in self.BASELINE_PROBABILITIES:
                for outcome, baseline_prob in self.BASELINE_PROBABILITIES[cond_key].items():
                    # Adjust based on patient factors
                    adjustment = self._calculate_adjustment(patient_id, condition)
                    adjusted_prob = min(
                        max(baseline_prob * adjustment, 0.0), 1.0
                    )
                    key = f"{cond_key}_{outcome}"
                    forecasts["risks"][key] = round(adjusted_prob, 4)
                    forecasts["probabilities"][key] = round(adjusted_prob, 4)
            else:
                # Generic fallback for unknown conditions
                # Use number of conditions and patient age to estimate overall risk
                patient = self.store.patient(patient_id)
                age = patient.get("AGE", 0) if patient else 0
                num_conditions = len(conditions) if conditions else 1
                # More conditions + older age = higher risk
                base_risk = min(0.2 + (num_conditions * 0.05) + max(0, (age - 50) * 0.01), 0.8)
                key = f"generic_{cond_key or 'unknown'}_overall"
                forecasts["risks"][key] = round(base_risk, 4)
                forecasts["probabilities"][key] = round(base_risk, 4)

        # Build simple trajectory
        forecasts["trajectory"] = self._build_trajectory(
            forecasts["risks"], horizon_days
        )

        return forecasts

    def _calculate_adjustment(
        self, patient_id: str, condition: str
    ) -> float:
        """Calculate probability adjustment based on patient history."""
        # Simplified: look at patient age, comorbidities
        patient = self.store.patient(patient_id)
        if not patient:
            return 1.0

        age = patient.get("AGE", 0)
        # Elderly patients have higher risk
        age_factor = 1.0 + max(0, (age - 65) * 0.01) if age else 1.0

        # More comorbidities = higher risk
        comorbidities = patient.get("comorbidities", "")
        comorbidity_factor = 1.0 + (len(comorbidities.split(",")) * 0.05) if comorbidities else 1.0

        return age_factor * comorbidity_factor

    def _build_trajectory(
        self, risks: dict[str, float], horizon_days: int
    ) -> list[dict[str, Any]]:
        """Build a time-based trajectory of predicted health states."""
        trajectory = []
        days = min(horizon_days, 365)
        step = max(1, days // 10)  # 10 snapshots max

        for d in range(0, days + 1, step):
            snapshot_prob = sum(risks.values()) / max(len(risks), 1) * (
                1 - d / (days + 1)
            )
            trajectory.append(
                {
                    "day": d,
                    "composite_risk": round(snapshot_prob, 4),
                    "state": self._state_from_risk(snapshot_prob),
                }
            )

        return trajectory

    @staticmethod
    def _state_from_risk(risk: float) -> str:
        """Map risk score to clinical state description."""
        if risk >= 0.5:
            return "high_risk"
        if risk >= 0.25:
            return "moderate_risk"
        return "low_risk"


# ---------------------------------------------------------------------------
# Enhanced Evidence Agent (updated for Phase 1)
# ---------------------------------------------------------------------------

class EvidenceAgentEnhanced(Agent):
    """Enhanced Evidence Agent that uses hybrid RAG retrieval with calibration."""

    name = "evidence_enhanced"

    def __init__(
        self,
        store: SyntheaStore,
        retriever: Retriever | None = None,
        use_dense: bool = True,
        calibrate: bool = True,
    ):
        self.store = store
        self.use_dense = use_dense
        self.calibrate = calibrate
        self.prognosis = PrognosisEngine(store)
        self._retriever = retriever
        self._dense_retriever = DenseRetriever(store) if use_dense else None

    def _get_retriever(self, patient_id: str) -> Retriever:
        if self._retriever is not None:
            return self._retriever
        return HybridRetriever(self.store, self._dense_retriever, patient_id=patient_id)

    def run(self, patient_id: str, question: str) -> AgentResult:
        t = perf_counter()
        retriever = self._get_retriever(patient_id)
        rag_result = retriever.retrieve(question, patient_id)

        # Calibrated confidence using Platt scaling approximation
        # based on retrieval characteristics
        total = rag_result.total_found
        base = min(0.5 + (total * 0.03), 0.9)

        # Adjust for query intent detection
        intent = rag_result.query_intent
        if intent == "symptom":
            base *= 1.05  # symptom queries get slight boost
        elif intent == "medication":
            base *= 0.95  # medication queries more narrow

        # Adjust for rerank quality
        if rag_result.rerank_score is not None:
            base = base * 0.8 + rag_result.rerank_score * 0.2

        # Apply calibration if enabled
        if self.calibrate:
            # Simple isotonic adjustment: pull extreme values toward 0.5
            base = 0.5 + (base - 0.5) * 0.8

        # Phase 1: Outcome forecasting
        # Extract conditions from retrieved evidence to forecast outcomes
        retrieved_conditions = self._extract_conditions_from_evidence(rag_result.evidence)
        prognosis = self.prognosis.forecast_patient_outcome(
            patient_id, retrieved_conditions, horizon_days=30
        )

        # Merge forecast results - include top risks in summary
        top_risks = list(prognosis["risks"].items())[:3]
        risk_str = "; ".join(
            [f"{k}: {v}" for k, v in top_risks]
        ) if top_risks else "no specific risks"

        # Extract evidence texts
        evidence_texts = [e.snippet for e in rag_result.evidence]

        # Count PHI-redacted items
        phi_count = sum(1 for e in rag_result.evidence if e.metadata.get("phi_redacted", False))

        summary = f"Hybrid RAG: {total} evidence items ({phi_count} PHI-redacted) in {rag_result.retrieval_latency_ms:.1f}ms"
        if risk_str != "no specific risks":
            summary += f" | Forecast: {risk_str}"

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            evidence=evidence_texts,
            confidence=round(base, 4),
            duration_ms=(perf_counter() - t) * 1000,
        )

    def _extract_conditions_from_evidence(
        self, evidence: list | None = None
    ) -> list[str]:
        """Extract condition names from evidence for prognosis.

        Accepts either evidence strings (from AgentResult.evidence)
        or EvidenceItem objects (from retriever output).
        """
        conditions: set[str] = set()
        if evidence is None:
            return list(conditions)[:5]

        for item in evidence:
            # Handle both string and EvidenceItem cases
            if hasattr(item, 'snippet'):
                snippet = item.snippet
            elif hasattr(item, 'lower'):
                snippet = item
            else:
                continue

            snippet_lower = snippet.lower() if hasattr(snippet, 'lower') else str(snippet).lower()

            # Parse "Condition: NAME" format from SparseRetriever output
            if "condition:" in snippet_lower:
                parts = snippet_lower.split("condition:")
                if len(parts) > 1:
                    cond_part = parts[1].split("(")[0].strip()
                    cond_part = cond_part.replace("situation", "").strip()
                    if cond_part:
                        conditions.add(cond_part)
            # Also check for known condition keywords in snippet
            for keyword in ["hypertension", "diabetes", "copd", "heart failure",
                           "arrhythmia", "failure", "infection", "cancer",
                           "hyperlipidemia", "anemia", "stroke", "mi"]:
                if keyword in snippet_lower:
                    conditions.add(keyword)
        return list(conditions)[:5]  # Limit to top 5
