from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from .models import AgentResult
from .store import SyntheaStore


class Agent(ABC):
    """Abstract base class for all investigation agents."""

    name: str = "base"

    def __init__(self, store: SyntheaStore):
        self.store = store

    @abstractmethod
    def run(self, patient_id: str, question: str) -> AgentResult:
        """Run the agent's investigation."""
        ...

    def _safe_rows(self, table: str, patient_id: str) -> list[dict[str, Any]]:
        """Safely get rows from the store, returning empty list on error."""
        try:
            return self.store.rows(table, patient_id)
        except Exception:
            return []


class TimelineAgent(Agent):
    """Agent that investigates patient timeline data."""

    name = "timeline"

    def run(self, patient_id: str, question: str) -> AgentResult:
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


class MedicationAgent(Agent):
    """Agent that investigates patient medication data."""

    name = "medication"

    def run(self, patient_id: str, question: str) -> AgentResult:
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


class EvidenceAgent(Agent):
    """Agent that collects evidence from patient records."""

    name = "evidence"

    def run(self, patient_id: str, question: str) -> AgentResult:
        t = perf_counter()

        # Collect evidence from multiple tables
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


class CriticAgent(Agent):
    """Agent that reviews and critiques investigation findings."""

    name = "critic"

    def run(self, patient_id: str, question: str) -> AgentResult:
        t = perf_counter()

        # Check for potential issues
        issues = []
        warnings = []

        # Check if patient exists
        patient = self.store.patient(patient_id)
        if not patient:
            issues.append("Patient not found in dataset")

        # Check for missing data
        conditions = self._safe_rows("conditions", patient_id)
        meds = self._safe_rows("medications", patient_id)

        if not conditions:
            warnings.append("No conditions recorded")
        if not meds:
            warnings.append("No medications recorded")

        # Build summary
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
