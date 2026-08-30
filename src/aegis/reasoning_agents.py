from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .llm import LLMProvider, ProviderFactory
from .prompts import PromptRegistry, initialize_default_prompts
from .tools import ToolRegistry, ToolResult, tool_registry

# Initialize default prompts on module load
initialize_default_prompts()


def _extract_json(text: str) -> dict[str, Any] | None:
    """Extract JSON from LLM response, handling markdown code blocks and chain-of-thought."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the content
    json_match = re.search(r'\{[^{}]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Reasoning Models
# ---------------------------------------------------------------------------

class ReasoningStep(BaseModel):
    """A single step in an agent's reasoning chain."""
    step_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    thought: str = Field(..., description="The agent's reasoning at this step")
    action: str | None = Field(default=None, description="Tool action taken")
    action_input: dict[str, Any] | None = Field(default=None, description="Input to the tool")
    observation: str | None = Field(default=None, description="Result from the tool")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentPlan(BaseModel):
    """An agent's investigation plan."""
    goal: str = Field(..., description="The overall investigation goal")
    steps: list[str] = Field(default_factory=list, description="Planned steps")
    current_step: int = Field(default=0)
    rationale: str = Field(..., description="Why this plan was chosen")


class AgentConclusion(BaseModel):
    """Structured conclusion from an agent."""
    summary: str = Field(..., description="Executive summary of findings")
    key_findings: list[str] = Field(default_factory=list, description="Main findings")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertainties: list[str] = Field(default_factory=list, description="Known uncertainties")
    recommendations: list[str] = Field(default_factory=list, description="Recommended actions")
    reasoning_chain: list[ReasoningStep] = Field(default_factory=list)


class AgentDebatePosition(BaseModel):
    """An agent's position in a multi-agent debate."""
    agent_name: str
    position: str = Field(..., description="The agent's position/claim")
    supporting_evidence: list[str] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rebuttals: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Reasoning Agent Base
# ---------------------------------------------------------------------------

class ReasoningAgent(ABC):
    """Base class for LLM-powered reasoning agents.

    This is the foundation of the revolutionary agentic system. Each agent:
    1. Receives an investigation question
    2. Creates a plan using LLM reasoning
    3. Executes tools to gather evidence
    4. Reasons about the evidence using chain-of-thought
    5. Produces a structured conclusion

    The key innovation is that agents actually REASON about clinical data
    rather than just counting records.
    """

    name: str = "base_reasoning"
    role: str = "clinical investigator"
    description: str = "A reasoning agent that investigates clinical questions"

    def __init__(
        self,
        llm: LLMProvider | None = None,
        tools: ToolRegistry | None = None,
        max_reasoning_steps: int = 10,
        max_tool_calls: int = 5,
        prompt_registry: PromptRegistry | None = None,
    ):
        self.llm = llm or ProviderFactory.from_env()
        self.tools = tools or tool_registry
        self.max_reasoning_steps = max_reasoning_steps
        self.max_tool_calls = max_tool_calls
        self.prompt_registry = prompt_registry or globals().get("prompt_registry") or PromptRegistry()
        self._reasoning_chain: list[ReasoningStep] = []
        self._tool_call_count = 0

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        ...

    @abstractmethod
    def get_available_tools(self) -> list[str]:
        """Get list of tool names this agent can use."""
        ...

    def _build_tool_descriptions(self) -> str:
        """Build formatted tool descriptions for the prompt."""
        available = self.get_available_tools()
        definitions = [
            self.tools.get_definition(name)
            for name in available
            if self.tools.get_definition(name) is not None
        ]

        parts = []
        for defn in definitions:
            params = []
            for p in defn.parameters:
                req = "required" if p.required else "optional"
                params.append(f"    - {p.name} ({p.type}, {req}): {p.description}")

            part = f"""### {defn.name}
{defn.description}
Parameters:
{chr(10).join(params) if params else "    None"}
Returns: {defn.returns}"""
            parts.append(part)

        return "\n\n".join(parts)

    async def plan(self, patient_id: str, question: str) -> AgentPlan:
        """Create an investigation plan using LLM reasoning."""
        prompt = self.prompt_registry.render(
            "plan_template",
            {
                "role": self.role,
                "patient_id": patient_id,
                "question": question,
                "tools": self._build_tool_descriptions(),
            },
        )

        response = await self.llm.complete(
            system=self.get_system_prompt(),
            user=prompt,
            temperature=0.2,
        )

        try:
            plan_data = _extract_json(response.content)
            if plan_data:
                return AgentPlan(
                    goal=plan_data.get("goal", question),
                    steps=plan_data.get("steps", []),
                    rationale=plan_data.get("rationale", ""),
                )
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: create a basic plan
        return AgentPlan(
            goal=question,
            steps=[
                    "Gather patient demographic information",
                    "Retrieve relevant clinical data",
                    "Analyze findings and synthesize conclusion",
                ],
                rationale="Default investigation plan",
            )

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool and record the call."""
        if self._tool_call_count >= self.max_tool_calls:
            return ToolResult(
                success=False,
                data=None,
                error=f"Maximum tool calls ({self.max_tool_calls}) reached",
            )

        self._tool_call_count += 1
        result = await self.tools.execute(tool_name, **kwargs)

        # Record in reasoning chain
        self._reasoning_chain.append(ReasoningStep(
            thought=f"Calling tool: {tool_name}",
            action=tool_name,
            action_input=kwargs,
            observation=str(result.data)[:500] if result.success else f"Error: {result.error}",
            confidence=0.9 if result.success else 0.1,
        ))

        return result

    async def reason(self, observation: str, context: str = "") -> ReasoningStep:
        """Perform a reasoning step using the LLM."""
        prompt = self.prompt_registry.render(
            "reasoning_template",
            {
                "observation": observation,
                "context": context,
            },
        )

        response = await self.llm.complete(
            system=self.get_system_prompt(),
            user=prompt,
            temperature=0.3,
        )

        try:
            reasoning = _extract_json(response.content)
            if reasoning:
                step = ReasoningStep(
                    thought=reasoning.get("thought", ""),
                    confidence=reasoning.get("confidence", 0.5),
                )
            else:
                step = ReasoningStep(
                    thought=response.content[:200],
                    confidence=0.5,
                )
        except (json.JSONDecodeError, ValueError):
            step = ReasoningStep(
                thought=response.content[:200],
                confidence=0.5,
            )

        self._reasoning_chain.append(step)
        return step

    async def conclude(self, question: str, evidence: list[str]) -> AgentConclusion:
        """Generate a structured conclusion from the investigation."""
        evidence_text = "\n".join(f"- {e}" for e in evidence[:20])

        prompt = self.prompt_registry.render(
            "conclusion_template",
            {
                "question": question,
                "evidence": evidence_text,
                "reasoning_chain": self._format_reasoning_chain(),
            },
        )

        response = await self.llm.complete(
            system=self.get_system_prompt(),
            user=prompt,
            temperature=0.2,
        )

        try:
            conclusion_data = _extract_json(response.content)
            if conclusion_data:
                return AgentConclusion(
                    summary=conclusion_data.get("summary", ""),
                    key_findings=conclusion_data.get("key_findings", []),
                    evidence=conclusion_data.get("evidence", evidence[:5]),
                    confidence=conclusion_data.get("confidence", 0.5),
                    uncertainties=conclusion_data.get("uncertainties", []),
                    recommendations=conclusion_data.get("recommendations", []),
                    reasoning_chain=self._reasoning_chain,
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return AgentConclusion(
            summary=response.content[:300],
            evidence=evidence[:5],
            confidence=0.4,
            reasoning_chain=self._reasoning_chain,
        )

    def _format_reasoning_chain(self) -> str:
        """Format the reasoning chain for prompts."""
        parts = []
        for i, step in enumerate(self._reasoning_chain[-5:], 1):
            parts.append(f"{i}. Thought: {step.thought}")
            if step.action:
                parts.append(f"   Action: {step.action}({step.action_input})")
            if step.observation:
                parts.append(f"   Result: {step.observation[:200]}")
        return "\n".join(parts) if parts else "No reasoning steps yet."

    async def investigate(self, patient_id: str, question: str) -> AgentConclusion:
        """Run a full investigation on a patient question.

        This is the main entry point for an agent. It:
        1. Creates an investigation plan
        2. Executes the plan step by step
        3. Uses tools to gather evidence
        4. Reasons about the evidence
        5. Produces a structured conclusion
        """
        start_time = perf_counter()
        self._reasoning_chain = []
        self._tool_call_count = 0

        # Step 1: Plan
        plan = await self.plan(patient_id, question)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Investigation plan: {plan.rationale}",
            confidence=0.8,
        ))

        # Step 2: Execute plan and gather evidence
        evidence = []
        context = f"Patient ID: {patient_id}\nQuestion: {question}"

        for step_desc in plan.steps[:self.max_reasoning_steps]:
            # Reason about what to do next
            await self.reason(
                observation=f"Current step: {step_desc}",
                context=context,
            )

            # Determine which tool to call based on the step
            tool_call = await self._decide_tool_call(step_desc, context, evidence)

            if tool_call:
                tool_name, tool_args = tool_call
                result = await self.execute_tool(tool_name, **tool_args)

                if result.success and result.data:
                    evidence.append(str(result.data)[:500])
                    context += f"\n\nTool {tool_name} returned: {str(result.data)[:300]}"

        # Step 3: Generate conclusion
        conclusion = await self.conclude(question, evidence)

        # Add timing metadata
        duration_ms = (perf_counter() - start_time) * 1000
        conclusion.reasoning_chain.insert(0, ReasoningStep(
            thought=f"Investigation completed in {duration_ms:.0f}ms with {len(evidence)} evidence items",
            confidence=1.0,
        ))

        return conclusion

    async def _decide_tool_call(
        self,
        step_desc: str,
        context: str,
        current_evidence: list[str],
    ) -> tuple[str, dict[str, Any]] | None:
        """Use LLM to decide which tool to call for a given step."""
        available_tools = self.get_available_tools()
        tool_list = ", ".join(available_tools)

        prompt = self.prompt_registry.render(
            "tool_decision_template",
            {
                "step_desc": step_desc,
                "context": context[:500],
                "tool_list": tool_list,
            },
        )

        response = await self.llm.complete(
            system="You are a clinical investigation assistant. Decide which tools to call to gather evidence.",
            user=prompt,
            temperature=0.1,
        )

        try:
            decision = _extract_json(response.content)
            if decision:
                tool_name = decision.get("tool")
                if tool_name and tool_name in available_tools:
                    return tool_name, decision.get("args", {})
        except (json.JSONDecodeError, ValueError):
            pass

        return None


# ---------------------------------------------------------------------------
# Specialized Clinical Agents
# ---------------------------------------------------------------------------

class DiagnosticAgent(ReasoningAgent):
    """Agent specialized in diagnostic reasoning.

    Focuses on:
    - Identifying possible diagnoses
    - Differential diagnosis reasoning
    - Evidence for/against diagnoses
    - Diagnostic confidence assessment
    """

    name = "diagnostic"
    role = "diagnostician"
    description = "Analyzes patient data to identify and evaluate potential diagnoses"

    def get_system_prompt(self) -> str:
        return self.prompt_registry.render("diagnostic_system", {})

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_observations",
            "get_patient_medications",
            "get_patient_allergies",
            "search_patient_evidence",
            "find_related_conditions",
            "get_lab_analysis",
            "calculate_age",
        ]


class TreatmentAgent(ReasoningAgent):
    """Agent specialized in treatment analysis.

    Focuses on:
    - Current medication review
    - Treatment effectiveness assessment
    - Drug interaction checking
    - Treatment optimization recommendations
    """

    name = "treatment"
    role = "clinical pharmacologist"
    description = "Analyzes treatment plans, medications, and therapeutic effectiveness"

    def get_system_prompt(self) -> str:
        return self.prompt_registry.render("treatment_system", {})

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_medications",
            "get_patient_allergies",
            "check_drug_interactions",
            "find_condition_medication_correlations",
            "search_patient_evidence",
            "get_condition_duration",
        ]


class RiskAssessmentAgent(ReasoningAgent):
    """Agent specialized in risk assessment.

    Focuses on:
    - Disease risk scoring
    - Readmission risk
    - Complication risk
    - Preventive recommendations
    """

    name = "risk_assessment"
    role = "risk stratification specialist"
    description = "Assesses patient risks and predicts outcomes"

    def get_system_prompt(self) -> str:
        return self.prompt_registry.render("risk_system", {})

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_observations",
            "get_patient_medications",
            "assess_patient_risks",
            "forecast_patient_outcome",
            "get_lab_analysis",
            "calculate_age",
            "search_patient_evidence",
        ]


class TimelineAgent(ReasoningAgent):
    """Agent specialized in temporal analysis.

    Focuses on:
    - Disease progression over time
    - Treatment timeline analysis
    - Temporal pattern detection
    - Longitudinal trends
    """

    name = "timeline"
    role = "clinical timeline analyst"
    description = "Analyzes temporal patterns in patient health data"

    def get_system_prompt(self) -> str:
        return self.prompt_registry.render("timeline_system", {})

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_encounters",
            "get_patient_observations",
            "get_patient_procedures",
            "get_patient_careplans",
            "get_condition_duration",
            "forecast_patient_outcome",
            "search_patient_evidence",
        ]


class EvidenceSynthesisAgent(ReasoningAgent):
    """Agent specialized in synthesizing evidence from other agents.

    Focuses on:
    - Integrating findings from multiple agents
    - Resolving conflicting conclusions
    - Producing comprehensive reports
    - Confidence calibration
    """

    name = "evidence_synthesis"
    role = "evidence synthesis specialist"
    description = "Synthesizes findings from multiple agents into coherent conclusions"

    def get_system_prompt(self) -> str:
        return self.prompt_registry.render("synthesis_system", {})

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "search_patient_evidence",
            "get_patient_clinical_graph",
        ]

    async def synthesize(
        self,
        patient_id: str,
        question: str,
        agent_findings: dict[str, AgentConclusion],
    ) -> AgentConclusion:
        """Synthesize findings from multiple agents into a unified conclusion."""
        findings_text = []
        for agent_name, conclusion in agent_findings.items():
            findings_text.append(f"""## {agent_name.upper()} AGENT
Summary: {conclusion.summary}
Key Findings: {', '.join(conclusion.key_findings)}
Confidence: {conclusion.confidence}
Uncertainties: {', '.join(conclusion.uncertainties)}""")

        findings_str = "\n\n".join(findings_text)

        prompt = self.prompt_registry.render(
            "synthesis_template",
            {
                "patient_id": patient_id,
                "question": question,
                "findings": findings_str,
            },
        )

        response = await self.llm.complete(
            system=self.get_system_prompt(),
            user=prompt,
            temperature=0.2,
        )

        try:
            data = _extract_json(response.content)
            if data:
                return AgentConclusion(
                    summary=data.get("summary", ""),
                    key_findings=data.get("key_findings", []),
                    evidence=data.get("evidence", []),
                    confidence=data.get("confidence", 0.5),
                    uncertainties=data.get("uncertainties", []),
                    recommendations=data.get("recommendations", []),
                    reasoning_chain=self._reasoning_chain,
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return AgentConclusion(
            summary=response.content[:500],
            confidence=0.4,
            reasoning_chain=self._reasoning_chain,
        )
