"""Comprehensive tests for the AEGIS orchestrator module."""
from aegis.orchestrator import Orchestrator
from aegis.store import SyntheaStore


class TestOrchestrator:
    """Tests for Orchestrator."""

    def test_investigate_with_valid_patient(self):
        """Test investigation with a valid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate(first_patient, "Summarize health")
        assert report.patient_id == first_patient
        assert report.question == "Summarize health"
        assert report.trace_id
        assert report.generated_at
        assert report.review_required is True
        assert 0 <= report.confidence <= 1
        assert len(report.agent_results) == 4

    def test_investigate_with_invalid_patient(self):
        """Test investigation with an invalid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate("nonexistent-patient", "Summarize health")
        assert report.patient_id == "nonexistent-patient"
        assert report.review_required is True
        assert report.confidence < 0.5

    def test_investigate_generates_unique_trace_ids(self):
        """Test that each investigation gets a unique trace ID."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report1 = orchestrator.investigate(first_patient, "Question 1")
        report2 = orchestrator.investigate(first_patient, "Question 2")
        assert report1.trace_id != report2.trace_id

    def test_investigate_conclusion_contains_patient_info(self):
        """Test that conclusion contains patient information."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate(first_patient, "Test question")
        assert first_patient in report.conclusion
        assert "Test question" in report.conclusion

    def test_investigate_all_agents_run(self):
        """Test that all agents run successfully."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate(first_patient, "Test question")
        agent_names = [r.agent for r in report.agent_results]
        assert "timeline" in agent_names
        assert "medication" in agent_names
        assert "evidence" in agent_names
        assert "critic" in agent_names

    def test_investigate_evidence_collected(self):
        """Test that evidence is collected from agents."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate(first_patient, "Test question")
        assert len(report.evidence) > 0

    def test_investigate_confidence_calculation(self):
        """Test that confidence is calculated correctly."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        orchestrator = Orchestrator(store)
        report = orchestrator.investigate(first_patient, "Test question")
        # Confidence should be average of agent confidences
        expected = sum(r.confidence for r in report.agent_results) / len(report.agent_results)
        assert abs(report.confidence - expected) < 0.01
