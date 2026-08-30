from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from .agents import (
    Agent,
    AgentResult,
    CriticAgent,
    EvidenceAgent,
    MedicationAgent,
    TimelineAgent,
)
from .models import InvestigationReport
from .monitoring import metrics, structured_logger
from .store import SyntheaStore


class Orchestrator:
    """Orchestrates multi-agent investigations of patient records."""

    def __init__(self, store: SyntheaStore | None = None):
        self.store = store or SyntheaStore()
        self.agents: list[Agent] = [
            TimelineAgent(self.store),
            MedicationAgent(self.store),
            EvidenceAgent(self.store),
            CriticAgent(self.store),
        ]

    def investigate(self, patient_id: str, question: str) -> InvestigationReport:
        """Run a full investigation with all agents."""
        start_time = perf_counter()
        trace_id = str(uuid4())

        # Run all agents
        results = []
        for agent in self.agents:
            try:
                result = agent.run(patient_id, question)
                results.append(result)

                # Log agent execution
                structured_logger.log_agent_execution(
                    agent_name=agent.name,
                    patient_id=patient_id,
                    confidence=result.confidence,
                    duration_ms=result.duration_ms,
                    evidence_count=len(result.evidence),
                )
            except Exception as e:
                # Log error but continue with other agents
                structured_logger.log_error(e, {
                    "agent": agent.name,
                    "patient_id": patient_id,
                    "trace_id": trace_id,
                })
                # Create a failed result
                results.append(
                    self._create_failed_result(agent.name, str(e))
                )

        # Calculate overall confidence
        if results:
            confidence = sum(r.confidence for r in results) / len(results)
        else:
            confidence = 0.0

        # Collect all evidence
        evidence = [item for r in results for item in r.evidence]

        # Generate conclusion
        conclusion = self._generate_conclusion(results, patient_id, question)

        # Determine if review is required
        review_required = self._determine_review_required(results, confidence)

        # Create report
        report = InvestigationReport(
            patient_id=patient_id,
            question=question,
            conclusion=conclusion,
            evidence=evidence,
            confidence=confidence,
            review_required=review_required,
            trace_id=trace_id,
            generated_at=datetime.now(timezone.utc),
            agent_results=results,
        )

        # Record metrics
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.inc_counter("investigations_total")
        metrics.observe_histogram("investigation_duration_ms", duration_ms)
        metrics.set_gauge("investigation_confidence", confidence)

        return report

    def _generate_conclusion(
        self,
        results: list,
        patient_id: str,
        question: str,
    ) -> str:
        """Generate a conclusion based on agent results."""
        # Count successful vs failed agents
        successful = sum(1 for r in results if r.status == "completed")
        failed = len(results) - successful

        # Get patient info
        patient = self.store.patient(patient_id)
        patient_name = ""
        if patient:
            first = patient.get("FIRST", "")
            last = patient.get("LAST", "")
            patient_name = f"{first} {last}".strip()

        # Build conclusion
        parts = []

        if patient_name:
            parts.append(f"Investigation for patient {patient_name} (ID: {patient_id}).")
        else:
            parts.append(f"Investigation for patient ID: {patient_id}.")

        parts.append(f"Question: {question}")

        if successful > 0:
            parts.append(f"Completed {successful}/{len(results)} agent analyses.")

        if failed > 0:
            parts.append(f"Warning: {failed} agent(s) encountered errors.")

        # Add agent summaries
        for result in results:
            if result.status == "completed":
                parts.append(f"- {result.agent.title()}: {result.summary}")

        parts.append(
            "This investigation uses synthetic patient data and does not constitute "
            "medical advice. All findings should be reviewed by a qualified healthcare "
            "professional before any clinical decisions."
        )

        return " ".join(parts)

    def _determine_review_required(
        self,
        results: list,
        confidence: float,
    ) -> bool:
        """Determine if human review is required."""
        # Always require review for low confidence
        if confidence < 0.7:
            return True

        # Check if any agent flagged issues
        for result in results:
            if result.agent == "critic" and result.confidence < 0.5:
                return True
            if any("issue:" in e for e in result.evidence):
                return True

        # Always require review for medical investigations
        return True

    def _create_failed_result(self, agent_name: str, error: str) -> AgentResult:
        """Create a failed agent result."""
        return AgentResult(
            agent=agent_name,
            status="failed",
            summary=f"Agent failed: {error}",
            evidence=[f"error:{error}"],
            confidence=0.0,
            duration_ms=0.0,
        )
