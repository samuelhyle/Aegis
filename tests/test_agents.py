"""Comprehensive tests for the AEGIS agents module."""
from aegis.agents import CriticAgent, EvidenceAgent, MedicationAgent, TimelineAgent
from aegis.store import SyntheaStore


class TestTimelineAgent:
    """Tests for TimelineAgent."""

    def test_agent_name(self):
        """Test agent name."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = TimelineAgent(store)
        assert agent.name == "timeline"

    def test_run_with_valid_patient(self):
        """Test running with a valid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        agent = TimelineAgent(store)
        result = agent.run(first_patient, "Summarize timeline")
        assert result.agent == "timeline"
        assert result.status == "completed"
        assert result.confidence > 0
        assert result.duration_ms >= 0

    def test_run_with_invalid_patient(self):
        """Test running with an invalid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = TimelineAgent(store)
        result = agent.run("nonexistent-patient", "Summarize timeline")
        assert result.agent == "timeline"
        assert result.status == "completed"
        assert result.confidence < 0.5  # Low confidence for missing patient

    def test_evidence_format(self):
        """Test evidence format."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        agent = TimelineAgent(store)
        result = agent.run(first_patient, "Summarize timeline")
        for evidence in result.evidence:
            assert "=" in evidence  # Should be in format "key=value"


class TestMedicationAgent:
    """Tests for MedicationAgent."""

    def test_agent_name(self):
        """Test agent name."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = MedicationAgent(store)
        assert agent.name == "medication"

    def test_run_with_valid_patient(self):
        """Test running with a valid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        # Find a patient with medications
        for _, row in store.tables["patients"].head(20).iterrows():
            pid = row["Id"]
            meds = store.rows("medications", pid)
            if meds:
                agent = MedicationAgent(store)
                result = agent.run(pid, "List medications")
                assert result.agent == "medication"
                assert result.status == "completed"
                assert len(result.evidence) > 0
                break

    def test_run_with_no_medications(self):
        """Test running with a patient that has no medications."""
        store = SyntheaStore("data/synthea")
        store.load()
        # Find a patient without medications
        for _, row in store.tables["patients"].head(20).iterrows():
            pid = row["Id"]
            meds = store.rows("medications", pid)
            if not meds:
                agent = MedicationAgent(store)
                result = agent.run(pid, "List medications")
                assert result.agent == "medication"
                assert result.status == "completed"
                assert result.confidence < 0.5
                break


class TestEvidenceAgent:
    """Tests for EvidenceAgent."""

    def test_agent_name(self):
        """Test agent name."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = EvidenceAgent(store)
        assert agent.name == "evidence"

    def test_run_collects_evidence(self):
        """Test that evidence agent collects from multiple sources."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        agent = EvidenceAgent(store)
        result = agent.run(first_patient, "Collect evidence")
        assert result.agent == "evidence"
        assert result.status == "completed"
        assert len(result.evidence) > 0


class TestCriticAgent:
    """Tests for CriticAgent."""

    def test_agent_name(self):
        """Test agent name."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = CriticAgent(store)
        assert agent.name == "critic"

    def test_run_with_valid_patient(self):
        """Test running with a valid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient = store.tables["patients"]["Id"].iloc[0]
        agent = CriticAgent(store)
        result = agent.run(first_patient, "Review findings")
        assert result.agent == "critic"
        assert result.status == "completed"
        assert "safety_boundary" in result.evidence
        assert "human_review_required" in result.evidence

    def test_run_with_invalid_patient(self):
        """Test running with an invalid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        agent = CriticAgent(store)
        result = agent.run("nonexistent-patient", "Review findings")
        assert result.agent == "critic"
        assert result.status == "completed"
        assert any("issue:" in e for e in result.evidence)
