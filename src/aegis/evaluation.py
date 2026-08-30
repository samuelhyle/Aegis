from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# Evaluation Models
# ---------------------------------------------------------------------------

class EvaluationMetric(StrEnum):
    """Metrics for evaluating agent performance."""
    GROUNDING = "grounding"  # How well findings are grounded in evidence
    COMPLETENESS = "completeness"  # How complete the investigation is
    ACCURACY = "accuracy"  # How accurate the conclusions are
    RELEVANCE = "relevance"  # How relevant findings are to the question
    CONFIDENCE_CALIBRATION = "confidence_calibration"  # How well confidence matches accuracy
    REASONING_QUALITY = "reasoning_quality"  # Quality of reasoning chain
    TOOL_EFFICIENCY = "tool_efficiency"  # Efficiency of tool usage


@dataclass
class EvaluationScore:
    """A single evaluation score."""
    metric: EvaluationMetric
    score: float  # 0.0 to 1.0
    explanation: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class AgentEvaluation:
    """Evaluation of an agent's performance."""
    agent_name: str
    question: str
    evaluation_id: str = field(default_factory=lambda: str(uuid4())[:8])
    scores: list[EvaluationScore] = field(default_factory=list)
    overall_score: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InvestigationTrace:
    """Complete trace of an investigation for analysis."""
    trace_id: str = field(default_factory=lambda: str(uuid4())[:8])
    patient_id: str = ""
    question: str = ""
    agent_traces: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    reasoning_chains: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    debate_log: list[dict[str, Any]] = field(default_factory=list)
    final_conclusion: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class AgentEvaluator:
    """Evaluates agent performance on clinical investigations.

    Uses LLM-based evaluation to assess:
    - Grounding: Are findings supported by evidence?
    - Completeness: Were all relevant aspects covered?
    - Accuracy: Are conclusions clinically reasonable?
    - Relevance: Are findings relevant to the question?
    - Confidence calibration: Does confidence match quality?
    """

    def __init__(self, llm=None):
        from .llm import ProviderFactory
        self.llm = llm or ProviderFactory.from_env()

    async def evaluate_agent(
        self,
        agent_name: str,
        question: str,
        conclusion,
        evidence: list[str] | None = None,
    ) -> AgentEvaluation:
        """Evaluate an agent's performance."""
        evidence = evidence or conclusion.evidence[:10]

        scores = []

        # Evaluate grounding
        grounding = await self._evaluate_grounding(question, conclusion, evidence)
        scores.append(grounding)

        # Evaluate completeness
        completeness = await self._evaluate_completeness(question, conclusion)
        scores.append(completeness)

        # Evaluate relevance
        relevance = await self._evaluate_relevance(question, conclusion)
        scores.append(relevance)

        # Evaluate reasoning quality
        reasoning = await self._evaluate_reasoning(conclusion)
        scores.append(reasoning)

        # Calculate overall score
        overall = sum(s.score for s in scores) / len(scores) if scores else 0.0

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        for score in scores:
            if score.score >= 0.7:
                strengths.append(f"Strong {score.metric.value}: {score.explanation}")
            elif score.score < 0.4:
                weaknesses.append(f"Weak {score.metric.value}: {score.explanation}")

        return AgentEvaluation(
            agent_name=agent_name,
            question=question,
            scores=scores,
            overall_score=round(overall, 3),
            strengths=strengths,
            weaknesses=weaknesses,
        )

    async def _evaluate_grounding(
        self, question: str, conclusion, evidence: list[str]
    ) -> EvaluationScore:
        """Evaluate how well findings are grounded in evidence."""
        evidence_text = "\n".join(f"- {e[:200]}" for e in evidence[:5])

        prompt = f"""Evaluate how well the following conclusion is grounded in evidence.

QUESTION: {question}
CONCLUSION: {conclusion.summary[:500]}
KEY FINDINGS: {', '.join(conclusion.key_findings[:5])}
EVIDENCE:
{evidence_text}

Score from 0.0 to 1.0 where:
- 0.0 = Findings are not supported by evidence
- 0.5 = Findings are partially supported
- 1.0 = All findings are well-grounded in evidence

Respond with JSON: {{"score": 0.0-1.0, "explanation": "brief explanation"}}"""

        response = await self.llm.complete(
            system="You are a clinical evidence evaluator. Assess how well conclusions are supported by evidence.",
            user=prompt,
            temperature=0.1,
        )

        try:
            data = json.loads(response.content)
            return EvaluationScore(
                metric=EvaluationMetric.GROUNDING,
                score=data.get("score", 0.5),
                explanation=data.get("explanation", ""),
                evidence=evidence[:3],
            )
        except json.JSONDecodeError:
            return EvaluationScore(
                metric=EvaluationMetric.GROUNDING,
                score=0.5,
                explanation="Could not evaluate",
            )

    async def _evaluate_completeness(
        self, question: str, conclusion
    ) -> EvaluationScore:
        """Evaluate how complete the investigation is."""
        prompt = f"""Evaluate how completely the following conclusion addresses the question.

QUESTION: {question}
CONCLUSION: {conclusion.summary[:500]}
KEY FINDINGS: {', '.join(conclusion.key_findings[:5])}
UNCERTAINTIES: {', '.join(conclusion.uncertainties[:3])}

Score from 0.0 to 1.0 where:
- 0.0 = Question not addressed at all
- 0.5 = Question partially addressed
- 1.0 = Question fully addressed with comprehensive findings

Respond with JSON: {{"score": 0.0-1.0, "explanation": "brief explanation"}}"""

        response = await self.llm.complete(
            system="You are a clinical completeness evaluator. Assess how thoroughly questions are answered.",
            user=prompt,
            temperature=0.1,
        )

        try:
            data = json.loads(response.content)
            return EvaluationScore(
                metric=EvaluationMetric.COMPLETENESS,
                score=data.get("score", 0.5),
                explanation=data.get("explanation", ""),
            )
        except json.JSONDecodeError:
            return EvaluationScore(
                metric=EvaluationMetric.COMPLETENESS,
                score=0.5,
                explanation="Could not evaluate",
            )

    async def _evaluate_relevance(
        self, question: str, conclusion
    ) -> EvaluationScore:
        """Evaluate how relevant findings are to the question."""
        prompt = f"""Evaluate how relevant the findings are to the original question.

QUESTION: {question}
KEY FINDINGS: {', '.join(conclusion.key_findings[:5])}

Score from 0.0 to 1.0 where:
- 0.0 = Findings are completely irrelevant
- 0.5 = Findings are partially relevant
- 1.0 = All findings are directly relevant

Respond with JSON: {{"score": 0.0-1.0, "explanation": "brief explanation"}}"""

        response = await self.llm.complete(
            system="You are a clinical relevance evaluator. Assess how relevant findings are to the question.",
            user=prompt,
            temperature=0.1,
        )

        try:
            data = json.loads(response.content)
            return EvaluationScore(
                metric=EvaluationMetric.RELEVANCE,
                score=data.get("score", 0.5),
                explanation=data.get("explanation", ""),
            )
        except json.JSONDecodeError:
            return EvaluationScore(
                metric=EvaluationMetric.RELEVANCE,
                score=0.5,
                explanation="Could not evaluate",
            )

    async def _evaluate_reasoning(self, conclusion) -> EvaluationScore:
        """Evaluate the quality of reasoning."""
        reasoning_steps = len(conclusion.reasoning_chain)

        if reasoning_steps == 0:
            return EvaluationScore(
                metric=EvaluationMetric.REASONING_QUALITY,
                score=0.3,
                explanation="No reasoning chain recorded",
            )

        # Check for reasoning diversity
        unique_thoughts = len(set(
            step.thought[:50] for step in conclusion.reasoning_chain
        ))

        score = min(1.0, 0.3 + (unique_thoughts * 0.1) + (reasoning_steps * 0.05))

        return EvaluationScore(
            metric=EvaluationMetric.REASONING_QUALITY,
            score=round(score, 3),
            explanation=f"Reasoning chain with {reasoning_steps} steps and {unique_thoughts} unique insights",
        )


# ---------------------------------------------------------------------------
# Trace Collector
# ---------------------------------------------------------------------------

class TraceCollector:
    """Collects and stores investigation traces for analysis."""

    def __init__(self):
        self.traces: dict[str, InvestigationTrace] = {}

    def start_trace(self, patient_id: str, question: str) -> InvestigationTrace:
        """Start a new investigation trace."""
        trace = InvestigationTrace(
            patient_id=patient_id,
            question=question,
        )
        self.traces[trace.trace_id] = trace
        return trace

    def record_tool_call(
        self,
        trace_id: str,
        agent_name: str,
        tool_name: str,
        args: dict[str, Any],
        result: Any,
        duration_ms: float,
    ):
        """Record a tool call in the trace."""
        trace = self.traces.get(trace_id)
        if not trace:
            return

        trace.tool_calls.append({
            "agent": agent_name,
            "tool": tool_name,
            "args": args,
            "result": str(result)[:500],
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_reasoning(
        self,
        trace_id: str,
        agent_name: str,
        step: dict[str, Any],
    ):
        """Record a reasoning step in the trace."""
        trace = self.traces.get(trace_id)
        if not trace:
            return

        if agent_name not in trace.reasoning_chains:
            trace.reasoning_chains[agent_name] = []

        trace.reasoning_chains[agent_name].append({
            **step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_debate(
        self,
        trace_id: str,
        round_number: int,
        positions: list[dict[str, Any]],
        consensus: list[str],
        disagreements: list[str],
    ):
        """Record a debate round in the trace."""
        trace = self.traces.get(trace_id)
        if not trace:
            return

        trace.debate_log.append({
            "round": round_number,
            "positions": positions,
            "consensus": consensus,
            "disagreements": disagreements,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_trace(self, trace_id: str) -> InvestigationTrace | None:
        """Get a trace by ID."""
        return self.traces.get(trace_id)

    def get_recent_traces(self, limit: int = 10) -> list[InvestigationTrace]:
        """Get recent traces."""
        traces = sorted(
            self.traces.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        return traces[:limit]

    def export_trace(self, trace_id: str) -> dict[str, Any]:
        """Export a trace as a dictionary."""
        trace = self.traces.get(trace_id)
        if not trace:
            return {}

        return {
            "trace_id": trace.trace_id,
            "patient_id": trace.patient_id,
            "question": trace.question,
            "tool_calls": trace.tool_calls,
            "reasoning_chains": trace.reasoning_chains,
            "debate_log": trace.debate_log,
            "final_conclusion": trace.final_conclusion,
            "timing": trace.timing,
            "created_at": trace.created_at.isoformat(),
        }


# Global instances
evaluator = AgentEvaluator()
trace_collector = TraceCollector()
