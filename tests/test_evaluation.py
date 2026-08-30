
import pytest

from aegis.evaluation import (
    AgentEvaluation,
    AgentEvaluator,
    EvaluationMetric,
    EvaluationScore,
    InvestigationTrace,
    TraceCollector,
)
from aegis.llm import LLMProvider, LLMResponse
from aegis.reasoning_agents import AgentConclusion, ReasoningStep


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
        return LLMResponse(content='{"score": 0.8, "explanation": "Good"}', model="mock-model")

    async def structured_output(self, system, user, response_model, temperature=0.0):
        return response_model()


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def evaluator(mock_llm):
    """Create an evaluator with mock LLM."""
    return AgentEvaluator(llm=mock_llm)


@pytest.fixture
def trace_collector():
    """Create a fresh trace collector."""
    return TraceCollector()


@pytest.fixture
def sample_conclusion():
    """Create a sample agent conclusion."""
    return AgentConclusion(
        summary="Patient has hypertension",
        key_findings=["High blood pressure", "On medication"],
        evidence=["Condition record", "Medication record"],
        confidence=0.8,
        uncertainties=["Need more lab data"],
        recommendations=["Monitor blood pressure"],
        reasoning_chain=[
            ReasoningStep(thought="Analyzing conditions", confidence=0.7),
            ReasoningStep(thought="Checking medications", confidence=0.8),
        ],
    )


class TestEvaluationScore:
    """Tests for EvaluationScore."""

    def test_creation(self):
        """Test creating an evaluation score."""
        score = EvaluationScore(
            metric=EvaluationMetric.GROUNDING,
            score=0.85,
            explanation="Well grounded in evidence",
            evidence=["Evidence 1", "Evidence 2"],
        )
        assert score.metric == EvaluationMetric.GROUNDING
        assert score.score == 0.85
        assert len(score.evidence) == 2


class TestAgentEvaluation:
    """Tests for AgentEvaluation."""

    def test_creation(self):
        """Test creating an agent evaluation."""
        evaluation = AgentEvaluation(
            agent_name="diagnostic",
            question="Test question",
            scores=[
                EvaluationScore(
                    metric=EvaluationMetric.GROUNDING,
                    score=0.8,
                    explanation="Good",
                ),
            ],
            overall_score=0.8,
            strengths=["Strong grounding"],
            weaknesses=["Weak completeness"],
        )
        assert evaluation.agent_name == "diagnostic"
        assert evaluation.overall_score == 0.8
        assert len(evaluation.strengths) == 1
        assert len(evaluation.weaknesses) == 1


class TestEvaluationMetric:
    """Tests for EvaluationMetric."""

    def test_values(self):
        """Test metric values."""
        assert EvaluationMetric.GROUNDING.value == "grounding"
        assert EvaluationMetric.COMPLETENESS.value == "completeness"
        assert EvaluationMetric.ACCURACY.value == "accuracy"
        assert EvaluationMetric.RELEVANCE.value == "relevance"
        assert EvaluationMetric.CONFIDENCE_CALIBRATION.value == "confidence_calibration"
        assert EvaluationMetric.REASONING_QUALITY.value == "reasoning_quality"
        assert EvaluationMetric.TOOL_EFFICIENCY.value == "tool_efficiency"


class TestAgentEvaluator:
    """Tests for AgentEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_reasoning_with_chain(self, evaluator, sample_conclusion):
        """Test evaluating reasoning quality with a reasoning chain."""
        score = await evaluator._evaluate_reasoning(sample_conclusion)
        assert score.metric == EvaluationMetric.REASONING_QUALITY
        assert score.score > 0.3  # Should be above base score

    @pytest.mark.asyncio
    async def test_evaluate_reasoning_without_chain(self, evaluator):
        """Test evaluating reasoning quality without a reasoning chain."""
        conclusion = AgentConclusion(
            summary="Test",
            reasoning_chain=[],
        )
        score = await evaluator._evaluate_reasoning(conclusion)
        assert score.metric == EvaluationMetric.REASONING_QUALITY
        assert score.score == 0.3  # Base score for no reasoning


class TestInvestigationTrace:
    """Tests for InvestigationTrace."""

    def test_creation(self):
        """Test creating an investigation trace."""
        trace = InvestigationTrace(
            patient_id="test-patient",
            question="Test question",
        )
        assert trace.patient_id == "test-patient"
        assert trace.question == "Test question"
        assert trace.trace_id is not None

    def test_tool_calls(self):
        """Test recording tool calls."""
        trace = InvestigationTrace()
        trace.tool_calls.append({
            "agent": "diagnostic",
            "tool": "get_patient_conditions",
            "args": {"patient_id": "test"},
            "result": "Found 3 conditions",
            "duration_ms": 10.0,
        })
        assert len(trace.tool_calls) == 1

    def test_reasoning_chains(self):
        """Test recording reasoning chains."""
        trace = InvestigationTrace()
        trace.reasoning_chains["diagnostic"] = [
            {"thought": "Step 1", "confidence": 0.7},
            {"thought": "Step 2", "confidence": 0.8},
        ]
        assert len(trace.reasoning_chains["diagnostic"]) == 2


class TestTraceCollector:
    """Tests for TraceCollector."""

    def test_start_trace(self, trace_collector):
        """Test starting a new trace."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        assert trace.patient_id == "test-patient"
        assert trace.question == "Test question"
        assert trace.trace_id in trace_collector.traces

    def test_record_tool_call(self, trace_collector):
        """Test recording a tool call."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        trace_collector.record_tool_call(
            trace_id=trace.trace_id,
            agent_name="diagnostic",
            tool_name="get_patient_conditions",
            args={"patient_id": "test"},
            result="Found 3 conditions",
            duration_ms=10.0,
        )
        assert len(trace.tool_calls) == 1
        assert trace.tool_calls[0]["agent"] == "diagnostic"

    def test_record_reasoning(self, trace_collector):
        """Test recording a reasoning step."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        trace_collector.record_reasoning(
            trace_id=trace.trace_id,
            agent_name="diagnostic",
            step={"thought": "Analyzing data", "confidence": 0.8},
        )
        assert "diagnostic" in trace.reasoning_chains
        assert len(trace.reasoning_chains["diagnostic"]) == 1

    def test_record_debate(self, trace_collector):
        """Test recording a debate round."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        trace_collector.record_debate(
            trace_id=trace.trace_id,
            round_number=1,
            positions=[{"agent": "diagnostic", "position": "test"}],
            consensus=["Agreement 1"],
            disagreements=["Disagreement 1"],
        )
        assert len(trace.debate_log) == 1
        assert trace.debate_log[0]["round"] == 1

    def test_get_trace(self, trace_collector):
        """Test getting a trace by ID."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        retrieved = trace_collector.get_trace(trace.trace_id)
        assert retrieved is not None
        assert retrieved.trace_id == trace.trace_id

    def test_get_trace_not_found(self, trace_collector):
        """Test getting a non-existent trace."""
        retrieved = trace_collector.get_trace("nonexistent")
        assert retrieved is None

    def test_get_recent_traces(self, trace_collector):
        """Test getting recent traces."""
        # Create multiple traces
        for i in range(5):
            trace_collector.start_trace(f"patient-{i}", f"Question {i}")

        recent = trace_collector.get_recent_traces(limit=3)
        assert len(recent) == 3

    def test_export_trace(self, trace_collector):
        """Test exporting a trace."""
        trace = trace_collector.start_trace("test-patient", "Test question")
        trace_collector.record_tool_call(
            trace_id=trace.trace_id,
            agent_name="diagnostic",
            tool_name="get_patient_conditions",
            args={"patient_id": "test"},
            result="Found 3 conditions",
            duration_ms=10.0,
        )

        exported = trace_collector.export_trace(trace.trace_id)
        assert exported["patient_id"] == "test-patient"
        assert exported["question"] == "Test question"
        assert len(exported["tool_calls"]) == 1

    def test_export_trace_not_found(self, trace_collector):
        """Test exporting a non-existent trace."""
        exported = trace_collector.export_trace("nonexistent")
        assert exported == {}
