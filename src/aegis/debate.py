from __future__ import annotations

import json
from uuid import uuid4

from pydantic import BaseModel, Field

from .llm import LLMProvider, ProviderFactory
from .reasoning_agents import (
    AgentConclusion,
    AgentDebatePosition,
    DiagnosticAgent,
    EvidenceSynthesisAgent,
    ReasoningAgent,
    RiskAssessmentAgent,
    TimelineAgent,
    TreatmentAgent,
)

# ---------------------------------------------------------------------------
# Debate Models
# ---------------------------------------------------------------------------

class DebateRound(BaseModel):
    """A single round of multi-agent debate."""
    round_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    round_number: int
    positions: list[AgentDebatePosition] = Field(default_factory=list)
    consensus_points: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    moderator_notes: str = ""


class DebateResult(BaseModel):
    """Result of a multi-agent debate."""
    debate_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    question: str
    rounds: list[DebateRound] = Field(default_factory=list)
    final_consensus: str = ""
    key_agreements: list[str] = Field(default_factory=list)
    key_disagreements: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning_summary: str = ""


class InvestigationResult(BaseModel):
    """Complete result of a multi-agent investigation."""
    investigation_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    patient_id: str
    question: str
    agent_conclusions: dict[str, AgentConclusion] = Field(default_factory=dict)
    debate_result: DebateResult | None = None
    final_conclusion: AgentConclusion | None = None
    total_duration_ms: float = 0.0
    total_tool_calls: int = 0
    total_reasoning_steps: int = 0


# ---------------------------------------------------------------------------
# Debate Moderator
# ---------------------------------------------------------------------------

class DebateModerator:
    """Moderates multi-agent debates to reach consensus.

    The moderator:
    1. Collects positions from each agent
    2. Identifies agreements and disagreements
    3. Facilitates discussion on disagreements
    4. Guides agents toward consensus
    5. Produces a final synthesized conclusion
    """

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm or ProviderFactory.from_env()

    async def collect_positions(
        self,
        question: str,
        agent_conclusions: dict[str, AgentConclusion],
    ) -> list[AgentDebatePosition]:
        """Collect debate positions from agent conclusions."""
        positions = []

        for agent_name, conclusion in agent_conclusions.items():
            position = AgentDebatePosition(
                agent_name=agent_name,
                position=conclusion.summary,
                supporting_evidence=conclusion.key_findings[:3],
                confidence=conclusion.confidence,
            )
            positions.append(position)

        return positions

    async def identify_agreements_disagreements(
        self,
        question: str,
        positions: list[AgentDebatePosition],
    ) -> tuple[list[str], list[str]]:
        """Identify points of agreement and disagreement between agents."""
        positions_text = "\n".join(
            f"- {p.agent_name} (confidence: {p.confidence}): {p.position}"
            for p in positions
        )

        prompt = f"""Analyze the following agent positions on a clinical question.

QUESTION: {question}

AGENT POSITIONS:
{positions_text}

Identify:
1. Points where agents AGREE
2. Points where agents DISAGREE

Respond with JSON:
{{
    "agreements": ["Agreement 1", "Agreement 2", ...],
    "disagreements": ["Disagreement 1", "Disagreement 2", ...]
}}"""

        response = await self.llm.complete(
            system="You are a clinical debate moderator. Identify agreements and disagreements between experts.",
            user=prompt,
            temperature=0.2,
        )

        try:
            data = json.loads(response.content)
            return data.get("agreements", []), data.get("disagreements", [])
        except json.JSONDecodeError:
            return [], []

    async def facilitate_discussion(
        self,
        question: str,
        disagreement: str,
        positions: list[AgentDebatePosition],
    ) -> str:
        """Facilitate discussion on a specific disagreement."""
        relevant_positions = [
            p for p in positions
            if any(
                keyword.lower() in p.position.lower()
                for keyword in disagreement.split()[:3]
            )
        ]

        if not relevant_positions:
            relevant_positions = positions[:2]

        positions_text = "\n".join(
            f"- {p.agent_name}: {p.position}"
            for p in relevant_positions
        )

        prompt = f"""Facilitate a discussion on the following disagreement.

QUESTION: {question}
DISAGREEMENT: {disagreement}

RELEVANT POSITIONS:
{positions_text}

Provide a balanced analysis that:
1. Presents each perspective fairly
2. Weighs the evidence
3. Identifies the most supported conclusion
4. Acknowledges remaining uncertainty

Respond with a concise resolution (2-3 sentences)."""

        response = await self.llm.complete(
            system="You are an expert clinical mediator. Help resolve disagreements between specialists.",
            user=prompt,
            temperature=0.3,
        )

        return response.content

    async def run_debate(
        self,
        question: str,
        agent_conclusions: dict[str, AgentConclusion],
        max_rounds: int = 2,
    ) -> DebateResult:
        """Run a multi-agent debate to reach consensus."""
        rounds = []

        # Collect initial positions
        positions = await self.collect_positions(question, agent_conclusions)

        # Round 1: Identify agreements and disagreements
        agreements, disagreements = await self.identify_agreements_disagreements(
            question, positions
        )

        round1 = DebateRound(
            round_number=1,
            positions=positions,
            consensus_points=agreements,
            disagreements=disagreements,
        )
        rounds.append(round1)

        # Round 2: Discuss disagreements (if any)
        if disagreements and max_rounds >= 2:
            resolutions = []
            for disagreement in disagreements[:3]:  # Limit to top 3
                resolution = await self.facilitate_discussion(
                    question, disagreement, positions
                )
                resolutions.append(resolution)

            round2 = DebateRound(
                round_number=2,
                positions=positions,
                consensus_points=agreements + resolutions,
                disagreements=[],  # Resolved
                moderator_notes="Disagreements discussed and resolved",
            )
            rounds.append(round2)

        # Generate final consensus
        final_consensus = await self._generate_consensus(
            question, positions, agreements, disagreements
        )

        return DebateResult(
            question=question,
            rounds=rounds,
            final_consensus=final_consensus,
            key_agreements=agreements,
            key_disagreements=disagreements,
            confidence=self._calculate_consensus_confidence(positions),
        )

    async def _generate_consensus(
        self,
        question: str,
        positions: list[AgentDebatePosition],
        agreements: list[str],
        disagreements: list[str],
    ) -> str:
        """Generate a final consensus statement."""
        positions_text = "\n".join(
            f"- {p.agent_name} (confidence: {p.confidence}): {p.position}"
            for p in positions
        )

        prompt = f"""Generate a consensus statement based on the expert discussion.

QUESTION: {question}

EXPERT POSITIONS:
{positions_text}

POINTS OF AGREEMENT:
{chr(10).join(f'- {a}' for a in agreements)}

REMAINING DISAGREEMENTS:
{chr(10).join(f'- {d}' for d in disagreements)}

Synthesize a clear, balanced consensus statement that:
1. Directly answers the question
2. Reflects areas of agreement
3. Acknowledges remaining uncertainties
4. Is clinically accurate and actionable"""

        response = await self.llm.complete(
            system="You are a clinical consensus builder. Synthesize expert opinions into clear conclusions.",
            user=prompt,
            temperature=0.2,
        )

        return response.content

    def _calculate_consensus_confidence(
        self, positions: list[AgentDebatePosition]
    ) -> float:
        """Calculate confidence based on agent agreement."""
        if not positions:
            return 0.0

        # Average confidence weighted by agreement
        confidences = [p.confidence for p in positions]
        avg_confidence = sum(confidences) / len(confidences)

        # Bonus for agreement (agents with similar confidence agree more)
        if len(confidences) > 1:
            variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
            agreement_bonus = max(0, 0.1 - variance)  # Lower variance = higher bonus
            avg_confidence = min(1.0, avg_confidence + agreement_bonus)

        return round(avg_confidence, 3)


# ---------------------------------------------------------------------------
# Multi-Agent Orchestrator
# ---------------------------------------------------------------------------

class MultiAgentOrchestrator:
    """Orchestrates multi-agent investigations with debate.

    This is the revolutionary orchestrator that:
    1. Runs multiple specialized agents in parallel
    2. Facilitates multi-agent debate
    3. Synthesizes findings into a unified conclusion
    4. Tracks reasoning chains and tool usage
    """

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm or ProviderFactory.from_env()
        self.moderator = DebateModerator(self.llm)

        # Initialize specialized agents
        self.agents: dict[str, ReasoningAgent] = {
            "diagnostic": DiagnosticAgent(self.llm),
            "treatment": TreatmentAgent(self.llm),
            "risk_assessment": RiskAssessmentAgent(self.llm),
            "timeline": TimelineAgent(self.llm),
        }

        self.synthesizer = EvidenceSynthesisAgent(self.llm)

    async def investigate(
        self,
        patient_id: str,
        question: str,
        agents_to_use: list[str] | None = None,
        enable_debate: bool = True,
    ) -> InvestigationResult:
        """Run a multi-agent investigation with optional debate.

        Args:
            patient_id: The patient to investigate
            question: The clinical question to answer
            agents_to_use: Specific agents to use (None = all)
            enable_debate: Whether to run multi-agent debate
        """
        import time
        start_time = time.perf_counter()

        # Select agents
        active_agents = {
            name: agent
            for name, agent in self.agents.items()
            if agents_to_use is None or name in agents_to_use
        }

        # Run agents (sequentially for now, could be parallelized)
        agent_conclusions: dict[str, AgentConclusion] = {}
        total_tool_calls = 0
        total_reasoning_steps = 0

        # Run agents in parallel for speed
        import asyncio
        agent_names = list(active_agents.keys())

        async def run_agent(name: str) -> tuple[str, AgentConclusion]:
            agent = active_agents[name]
            try:
                conclusion = await agent.investigate(patient_id, question)
                return name, conclusion
            except Exception as e:
                return name, AgentConclusion(
                    summary=f"Agent {name} failed: {str(e)[:200]}",
                    confidence=0.0,
                    uncertainties=[f"Agent error: {str(e)[:200]}"],
                )

        # Execute all agents concurrently
        results = await asyncio.gather(
            *[run_agent(name) for name in agent_names],
            return_exceptions=False,
        )

        for name, conclusion in results:
            agent_conclusions[name] = conclusion
            try:
                total_tool_calls += active_agents[name]._tool_call_count
                total_reasoning_steps += len(active_agents[name]._reasoning_chain)
            except Exception:
                pass

        # Run debate if enabled and multiple agents
        debate_result = None
        if enable_debate and len(agent_conclusions) > 1:
            debate_result = await self.moderator.run_debate(
                question, agent_conclusions
            )

        # Synthesize final conclusion
        final_conclusion = await self.synthesizer.synthesize(
            patient_id, question, agent_conclusions
        )

        # If debate occurred, incorporate debate consensus
        if debate_result:
            final_conclusion.summary = f"{final_conclusion.summary}\n\nDebate Consensus: {debate_result.final_consensus}"
            final_conclusion.confidence = (
                final_conclusion.confidence * 0.6 + debate_result.confidence * 0.4
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return InvestigationResult(
            patient_id=patient_id,
            question=question,
            agent_conclusions=agent_conclusions,
            debate_result=debate_result,
            final_conclusion=final_conclusion,
            total_duration_ms=duration_ms,
            total_tool_calls=total_tool_calls,
            total_reasoning_steps=total_reasoning_steps,
        )

    async def investigate_single_agent(
        self,
        patient_id: str,
        question: str,
        agent_name: str,
    ) -> AgentConclusion:
        """Run investigation with a single specialized agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}")

        agent = self.agents[agent_name]
        return await agent.investigate(patient_id, question)
