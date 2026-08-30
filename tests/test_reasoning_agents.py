
import pytest

from aegis.llm import LLMProvider, LLMResponse
from aegis.reasoning_agents import (
    AgentConclusion,
    AgentDebatePosition,
    AgentPlan,
    DiagnosticAgent,
    EvidenceSynthesisAgent,
    ReasoningStep,
    RiskAssessmentAgent,
    TimelineAgent,
    TreatmentAgent,
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
def diagnostic_agent(mock_llm):
    """Create a diagnostic agent with mock LLM."""
    return DiagnosticAgent(llm=mock_llm)


@pytest.fixture
def treatment_agent(mock_llm):
    """Create a treatment agent with mock LLM."""
    return TreatmentAgent(llm=mock_llm)


class TestReasoningStep:
    """Tests for ReasoningStep."""

    def test_creation(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(
            thought="Analyzing patient data",
            confidence=0.8,
        )
        assert step.thought == "Analyzing patient data"
        assert step.confidence == 0.8
        assert step.step_id is not None

    def test_with_action(self):
        """Test reasoning step with action."""
        step = ReasoningStep(
            thought="Need to check conditions",
            action="get_patient_conditions",
            action_input={"patient_id": "test"},
            observation="Found 3 conditions",
            confidence=0.9,
        )
        assert step.action == "get_patient_conditions"
        assert step.observation == "Found 3 conditions"


class TestAgentPlan:
    """Tests for AgentPlan."""

    def test_creation(self):
        """Test creating an agent plan."""
        plan = AgentPlan(
            goal="Investigate patient health",
            steps=["Step 1", "Step 2"],
            rationale="Need to gather data",
        )
        assert plan.goal == "Investigate patient health"
        assert len(plan.steps) == 2
        assert plan.current_step == 0


class TestAgentConclusion:
    """Tests for AgentConclusion."""

    def test_creation(self):
        """Test creating an agent conclusion."""
        conclusion = AgentConclusion(
            summary="Patient has hypertension",
            key_findings=["Hypertension diagnosed", "On medication"],
            evidence=["Condition record", "Medication record"],
            confidence=0.85,
            uncertainties=["Need more lab data"],
            recommendations=["Monitor blood pressure"],
        )
        assert conclusion.summary == "Patient has hypertension"
        assert len(conclusion.key_findings) == 2
        assert conclusion.confidence == 0.85

    def test_with_reasoning_chain(self):
        """Test conclusion with reasoning chain."""
        chain = [
            ReasoningStep(thought="Step 1", confidence=0.7),
            ReasoningStep(thought="Step 2", confidence=0.8),
        ]
        conclusion = AgentConclusion(
            summary="Test",
            reasoning_chain=chain,
        )
        assert len(conclusion.reasoning_chain) == 2


class TestAgentDebatePosition:
    """Tests for AgentDebatePosition."""

    def test_creation(self):
        """Test creating a debate position."""
        position = AgentDebatePosition(
            agent_name="diagnostic",
            position="Patient likely has diabetes",
            supporting_evidence=["High glucose", "Family history"],
            confidence=0.75,
        )
        assert position.agent_name == "diagnostic"
        assert len(position.supporting_evidence) == 2


class TestDiagnosticAgent:
    """Tests for DiagnosticAgent."""

    def test_name(self, diagnostic_agent):
        """Test agent name."""
        assert diagnostic_agent.name == "diagnostic"

    def test_role(self, diagnostic_agent):
        """Test agent role."""
        assert diagnostic_agent.role == "diagnostician"

    def test_system_prompt(self, diagnostic_agent):
        """Test system prompt."""
        prompt = diagnostic_agent.get_system_prompt()
        assert "diagnostician" in prompt.lower()
        assert "SYNTHETIC" in prompt

    def test_available_tools(self, diagnostic_agent):
        """Test available tools."""
        tools = diagnostic_agent.get_available_tools()
        assert "get_patient_record" in tools
        assert "get_patient_conditions" in tools
        assert "search_patient_evidence" in tools


class TestTreatmentAgent:
    """Tests for TreatmentAgent."""

    def test_name(self, treatment_agent):
        """Test agent name."""
        assert treatment_agent.name == "treatment"

    def test_role(self, treatment_agent):
        """Test agent role."""
        assert treatment_agent.role == "clinical pharmacologist"

    def test_system_prompt(self, treatment_agent):
        """Test system prompt."""
        prompt = treatment_agent.get_system_prompt()
        assert "pharmacologist" in prompt.lower()

    def test_available_tools(self, treatment_agent):
        """Test available tools."""
        tools = treatment_agent.get_available_tools()
        assert "get_patient_medications" in tools
        assert "check_drug_interactions" in tools


class TestRiskAssessmentAgent:
    """Tests for RiskAssessmentAgent."""

    def test_name(self):
        """Test agent name."""
        agent = RiskAssessmentAgent()
        assert agent.name == "risk_assessment"

    def test_available_tools(self):
        """Test available tools."""
        agent = RiskAssessmentAgent()
        tools = agent.get_available_tools()
        assert "assess_patient_risks" in tools
        assert "forecast_patient_outcome" in tools


class TestTimelineAgent:
    """Tests for TimelineAgent."""

    def test_name(self):
        """Test agent name."""
        agent = TimelineAgent()
        assert agent.name == "timeline"

    def test_available_tools(self):
        """Test available tools."""
        agent = TimelineAgent()
        tools = agent.get_available_tools()
        assert "get_patient_encounters" in tools
        assert "get_patient_conditions" in tools


class TestEvidenceSynthesisAgent:
    """Tests for EvidenceSynthesisAgent."""

    def test_name(self):
        """Test agent name."""
        agent = EvidenceSynthesisAgent()
        assert agent.name == "evidence_synthesis"

    def test_available_tools(self):
        """Test available tools."""
        agent = EvidenceSynthesisAgent()
        tools = agent.get_available_tools()
        assert "search_patient_evidence" in tools
        assert "get_patient_clinical_graph" in tools
