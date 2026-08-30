
import pytest

from aegis.debate import (
    DebateModerator,
    DebateResult,
    DebateRound,
    InvestigationResult,
    MultiAgentOrchestrator,
)
from aegis.llm import LLMProvider, LLMResponse
from aegis.reasoning_agents import (
    AgentConclusion,
    AgentDebatePosition,
)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0

    @property
    def name(self):
        return "mock"

    @property
    def model_name(self):
        return "mock-model"

    async def complete(self, system, user, temperature=0.0):
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return LLMResponse(content=response, model="mock-model")
        return LLMResponse(content='{"thought": "default", "confidence": 0.5}', model="mock-model")

    async def structured_output(self, system, user, response_model, temperature=0.0):
        return response_model()


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def moderator(mock_llm):
    """Create a debate moderator with mock LLM."""
    return DebateModerator(llm=mock_llm)


@pytest.fixture
def sample_conclusions():
    """Create sample agent conclusions."""
    return {
        "diagnostic": AgentConclusion(
            summary="Patient has hypertension",
            key_findings=["High blood pressure", "On medication"],
            confidence=0.8,
            uncertainties=["Need more data"],
        ),
        "treatment": AgentConclusion(
            summary="Current treatment is appropriate",
            key_findings=["On ACE inhibitor", "Blood pressure controlled"],
            confidence=0.75,
        ),
        "risk_assessment": AgentConclusion(
            summary="Moderate cardiovascular risk",
            key_findings=["Age factor", "Hypertension"],
            confidence=0.7,
        ),
    }


class TestDebateRound:
    """Tests for DebateRound."""

    def test_creation(self):
        """Test creating a debate round."""
        round = DebateRound(
            round_number=1,
            positions=[
                AgentDebatePosition(
                    agent_name="test",
                    position="Test position",
                    confidence=0.8,
                ),
            ],
            consensus_points=["Agreement 1"],
            disagreements=["Disagreement 1"],
        )
        assert round.round_number == 1
        assert len(round.positions) == 1
        assert len(round.consensus_points) == 1
        assert len(round.disagreements) == 1


class TestDebateResult:
    """Tests for DebateResult."""

    def test_creation(self):
        """Test creating a debate result."""
        result = DebateResult(
            question="Test question",
            final_consensus="Test consensus",
            key_agreements=["Agreement 1"],
            key_disagreements=["Disagreement 1"],
            confidence=0.8,
        )
        assert result.question == "Test question"
        assert result.final_consensus == "Test consensus"
        assert result.confidence == 0.8


class TestDebateModerator:
    """Tests for DebateModerator."""

    @pytest.mark.asyncio
    async def test_collect_positions(self, moderator, sample_conclusions):
        """Test collecting positions from agent conclusions."""
        positions = await moderator.collect_positions("Test question", sample_conclusions)
        assert len(positions) == 3
        assert any(p.agent_name == "diagnostic" for p in positions)
        assert any(p.agent_name == "treatment" for p in positions)

    def test_calculate_consensus_confidence(self, moderator):
        """Test calculating consensus confidence."""
        positions = [
            AgentDebatePosition(agent_name="a", position="test", confidence=0.8),
            AgentDebatePosition(agent_name="b", position="test", confidence=0.7),
        ]
        confidence = moderator._calculate_consensus_confidence(positions)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be above average due to agreement


class TestInvestigationResult:
    """Tests for InvestigationResult."""

    def test_creation(self):
        """Test creating an investigation result."""
        result = InvestigationResult(
            patient_id="test-patient",
            question="Test question",
            agent_conclusions={
                "diagnostic": AgentConclusion(summary="Test", confidence=0.8),
            },
            total_duration_ms=1000.0,
            total_tool_calls=5,
            total_reasoning_steps=10,
        )
        assert result.patient_id == "test-patient"
        assert result.total_duration_ms == 1000.0
        assert result.total_tool_calls == 5


class TestMultiAgentOrchestrator:
    """Tests for MultiAgentOrchestrator."""

    def test_initialization(self, mock_llm):
        """Test orchestrator initialization."""
        orchestrator = MultiAgentOrchestrator(llm=mock_llm)
        assert "diagnostic" in orchestrator.agents
        assert "treatment" in orchestrator.agents
        assert "risk_assessment" in orchestrator.agents
        assert "timeline" in orchestrator.agents

    def test_agents_list(self, mock_llm):
        """Test that all expected agents are present."""
        orchestrator = MultiAgentOrchestrator(llm=mock_llm)
        agents = list(orchestrator.agents.keys())
        assert len(agents) == 4
        assert "diagnostic" in agents
        assert "treatment" in agents
        assert "risk_assessment" in agents
        assert "timeline" in agents
