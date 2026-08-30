from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReviewDecision(StrEnum):
    """Human review decision for an investigation report."""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MODIFICATION = "needs_modification"


class InvestigationRequest(BaseModel):
    """Request to start an investigation."""
    patient_id: str = Field(..., min_length=1, description="Synthea patient ID")
    question: str = Field(..., min_length=3, max_length=1000, description="Investigation question")

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, v: str) -> str:
        return v.strip()


class ReviewRequest(BaseModel):
    """Request to review an investigation report."""
    decision: ReviewDecision = Field(..., description="Review decision")
    reviewer_id: str = Field(..., min_length=1, max_length=100, description="Reviewer identifier")
    notes: str = Field(default="", max_length=2000, description="Review notes")


class AgentResult(BaseModel):
    """Result from a single agent execution."""
    agent: str = Field(..., description="Agent name")
    status: str = Field(..., description="Agent status (completed/failed)")
    summary: str = Field(..., description="Agent summary")
    evidence: list[str] = Field(default_factory=list, description="Evidence items")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    duration_ms: float = Field(default=0.0, ge=0.0, description="Execution duration in milliseconds")


class InvestigationReport(BaseModel):
    """Full investigation report with all agent results."""
    patient_id: str = Field(..., description="Patient ID")
    question: str = Field(..., description="Investigation question")
    conclusion: str = Field(..., description="Investigation conclusion")
    evidence: list[str] = Field(default_factory=list, description="All evidence items")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    review_required: bool = Field(default=True, description="Whether human review is required")
    trace_id: str = Field(..., description="Unique trace identifier")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    agent_results: list[AgentResult] = Field(default_factory=list, description="Individual agent results")

    # HITL review fields
    reviewed: bool = Field(default=False, description="Whether the report has been reviewed")
    review_decision: ReviewDecision | None = Field(default=None, description="Review decision")
    reviewer_id: str | None = Field(default=None, description="Reviewer identifier")
    review_notes: str | None = Field(default=None, description="Review notes")
    reviewed_at: datetime | None = Field(default=None, description="Review timestamp")

    @property
    def agent_count(self) -> int:
        """Number of agents that ran."""
        return len(self.agent_results)

    @property
    def successful_agents(self) -> int:
        """Number of agents that completed successfully."""
        return sum(1 for r in self.agent_results if r.status == "completed")

    @property
    def failed_agents(self) -> int:
        """Number of agents that failed."""
        return sum(1 for r in self.agent_results if r.status == "failed")

    @property
    def total_duration_ms(self) -> float:
        """Total duration across all agents."""
        return sum(r.duration_ms for r in self.agent_results)

    @property
    def evidence_count(self) -> int:
        """Number of evidence items."""
        return len(self.evidence)

    def to_summary(self) -> dict[str, Any]:
        """Return a summary dict for quick inspection."""
        return {
            "trace_id": self.trace_id,
            "patient_id": self.patient_id,
            "confidence": self.confidence,
            "review_required": self.review_required,
            "reviewed": self.reviewed,
            "agent_count": self.agent_count,
            "evidence_count": self.evidence_count,
            "total_duration_ms": self.total_duration_ms,
        }
