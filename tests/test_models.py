"""Comprehensive tests for the AEGIS models module."""
from datetime import datetime, timezone

import pytest

from aegis.models import (
    AgentResult,
    InvestigationReport,
    InvestigationRequest,
    ReviewDecision,
    ReviewRequest,
)


class TestInvestigationRequest:
    """Tests for InvestigationRequest."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = InvestigationRequest(patient_id="test-123", question="Summarize health")
        assert request.patient_id == "test-123"
        assert request.question == "Summarize health"

    def test_patient_id_stripped(self):
        """Test that patient_id is stripped."""
        request = InvestigationRequest(patient_id="  test-123  ", question="Summarize health")
        assert request.patient_id == "test-123"

    def test_question_too_short(self):
        """Test that question must be at least 3 characters."""
        with pytest.raises(Exception):
            InvestigationRequest(patient_id="test-123", question="ab")

    def test_patient_id_empty(self):
        """Test that patient_id cannot be empty."""
        with pytest.raises(Exception):
            InvestigationRequest(patient_id="", question="Summarize health")


class TestReviewRequest:
    """Tests for ReviewRequest."""

    def test_valid_review(self):
        """Test valid review creation."""
        review = ReviewRequest(
            decision=ReviewDecision.APPROVED,
            reviewer_id="dr-smith",
            notes="Looks good"
        )
        assert review.decision == ReviewDecision.APPROVED
        assert review.reviewer_id == "dr-smith"
        assert review.notes == "Looks good"

    def test_review_without_notes(self):
        """Test review without notes."""
        review = ReviewRequest(
            decision=ReviewDecision.REJECTED,
            reviewer_id="dr-jones"
        )
        assert review.notes == ""


class TestAgentResult:
    """Tests for AgentResult."""

    def test_valid_result(self):
        """Test valid result creation."""
        result = AgentResult(
            agent="timeline",
            status="completed",
            summary="Found 10 encounters",
            evidence=["encounters=10"],
            confidence=0.8,
            duration_ms=15.5
        )
        assert result.agent == "timeline"
        assert result.confidence == 0.8

    def test_default_values(self):
        """Test default values."""
        result = AgentResult(agent="test", status="completed", summary="test")
        assert result.evidence == []
        assert result.confidence == 0.0
        assert result.duration_ms == 0.0


class TestInvestigationReport:
    """Tests for InvestigationReport."""

    def test_valid_report(self):
        """Test valid report creation."""
        now = datetime.now(timezone.utc)
        report = InvestigationReport(
            patient_id="test-123",
            question="Summarize health",
            conclusion="Test conclusion",
            evidence=["evidence1"],
            confidence=0.8,
            review_required=True,
            trace_id="trace-123",
            generated_at=now,
            agent_results=[]
        )
        assert report.patient_id == "test-123"
        assert report.review_required is True
        assert report.reviewed is False

    def test_report_properties(self):
        """Test report properties."""
        now = datetime.now(timezone.utc)
        agent_results = [
            AgentResult(agent="timeline", status="completed", summary="test", confidence=0.8, duration_ms=10.0),
            AgentResult(agent="medication", status="completed", summary="test", confidence=0.7, duration_ms=15.0),
        ]
        report = InvestigationReport(
            patient_id="test-123",
            question="Summarize health",
            conclusion="Test conclusion",
            evidence=["evidence1", "evidence2"],
            confidence=0.75,
            review_required=True,
            trace_id="trace-123",
            generated_at=now,
            agent_results=agent_results
        )
        assert report.agent_count == 2
        assert report.successful_agents == 2
        assert report.failed_agents == 0
        assert report.total_duration_ms == 25.0
        assert report.evidence_count == 2

    def test_to_summary(self):
        """Test to_summary method."""
        now = datetime.now(timezone.utc)
        report = InvestigationReport(
            patient_id="test-123",
            question="Summarize health",
            conclusion="Test conclusion",
            evidence=["evidence1"],
            confidence=0.8,
            review_required=True,
            trace_id="trace-123",
            generated_at=now,
            agent_results=[]
        )
        summary = report.to_summary()
        assert summary["trace_id"] == "trace-123"
        assert summary["patient_id"] == "test-123"
        assert summary["confidence"] == 0.8


class TestReviewDecision:
    """Tests for ReviewDecision enum."""

    def test_values(self):
        """Test enum values."""
        assert ReviewDecision.APPROVED.value == "approved"
        assert ReviewDecision.REJECTED.value == "rejected"
        assert ReviewDecision.NEEDS_MODIFICATION.value == "needs_modification"
