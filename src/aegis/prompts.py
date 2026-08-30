from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PromptVersion:
    """A versioned prompt with metadata."""

    version: str
    template: str
    description: str = ""
    author: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "template": self.template,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptVersion:
        return cls(
            version=data["version"],
            template=data["template"],
            description=data.get("description", ""),
            author=data.get("author", "system"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now(timezone.utc)),
            tags=data.get("tags", []),
            variables=data.get("variables", []),
        )


class PromptRegistry:
    """Registry for managing versioned prompts.

    Features:
    - Version tracking with semantic versioning
    - Template variable extraction
    - Persistence to disk
    - Rollback to previous versions
    - A/B testing support
    """

    def __init__(self, storage_path: str | None = None):
        self._prompts: dict[str, list[PromptVersion]] = {}
        self._storage_path = Path(storage_path) if storage_path else Path("prompts")
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        name: str,
        template: str,
        version: str | None = None,
        description: str = "",
        author: str = "system",
        tags: list[str] | None = None,
    ) -> PromptVersion:
        """Register a new prompt version."""
        if name not in self._prompts:
            self._prompts[name] = []

        # Auto-generate version if not provided
        if version is None:
            existing_versions = [pv.version for pv in self._prompts[name]]
            version = self._next_version(existing_versions)

        # Extract variables from template
        variables = self._extract_variables(template)

        prompt_version = PromptVersion(
            version=version,
            template=template,
            description=description,
            author=author,
            tags=tags or [],
            variables=variables,
        )

        self._prompts[name].append(prompt_version)
        self._save_prompt(name, prompt_version)
        return prompt_version

    def get(self, name: str, version: str | None = None) -> PromptVersion | None:
        """Get a prompt by name and optional version (latest if not specified)."""
        if name not in self._prompts:
            self._load_prompt(name)
            if name not in self._prompts:
                return None

        versions = self._prompts[name]
        if not versions:
            return None

        if version is None:
            return versions[-1]  # Latest version

        for pv in versions:
            if pv.version == version:
                return pv
        return None

    def get_latest(self, name: str) -> PromptVersion | None:
        """Get the latest version of a prompt."""
        return self.get(name)

    def list_versions(self, name: str) -> list[PromptVersion]:
        """List all versions of a prompt."""
        if name not in self._prompts:
            self._load_prompt(name)
        return self._prompts.get(name, [])

    def list_all(self) -> dict[str, list[PromptVersion]]:
        """List all prompts and their versions."""
        for name in list(self._prompts.keys()):
            self._load_prompt(name)
        return self._prompts

    def render(self, name: str, variables: dict[str, Any], version: str | None = None) -> str:
        """Render a prompt with variables."""
        prompt_version = self.get(name, version)
        if not prompt_version:
            raise ValueError(f"Prompt not found: {name}@{version or 'latest'}")

        # Check for missing required variables
        missing = set(prompt_version.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required variables for {name}: {missing}")

        # Simple template rendering
        rendered = prompt_version.template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))

        return rendered

    def _extract_variables(self, template: str) -> list[str]:
        """Extract template variables from {variable} patterns."""
        import re
        return list(set(re.findall(r"\{(\w+)\}", template)))

    def _next_version(self, existing: list[str]) -> str:
        """Generate next semantic version."""
        if not existing:
            return "1.0.0"

        # Parse versions and find latest
        def parse_version(v: str) -> tuple[int, int, int]:
            parts = v.split(".")
            return (int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) == 3 else (0, 0, 0)

        latest = max(existing, key=parse_version)
        major, minor, patch = parse_version(latest)
        return f"{major}.{minor}.{patch + 1}"

    def _save_prompt(self, name: str, prompt_version: PromptVersion) -> None:
        """Save prompt to disk."""
        file_path = self._storage_path / f"{name}.json"
        data = {
            "name": name,
            "versions": [pv.to_dict() for pv in self._prompts[name]],
        }
        file_path.write_text(json.dumps(data, indent=2))

    def _load_prompt(self, name: str) -> bool:
        """Load prompt from disk."""
        file_path = self._storage_path / f"{name}.json"
        if not file_path.exists():
            return False

        try:
            data = json.loads(file_path.read_text())
            versions = [PromptVersion.from_dict(v) for v in data.get("versions", [])]
            self._prompts[name] = versions
            return True
        except Exception:
            return False


# Built-in clinical prompts
CLINICAL_PROMPTS = {
    "diagnostic_system": """You are an expert diagnostician analyzing clinical data. Your role is to:

1. Identify potential diagnoses based on patient data
2. Reason through differential diagnoses systematically
3. Evaluate evidence for and against each diagnosis
4. Assess diagnostic confidence
5. Recommend additional workup if needed

Key principles:
- Use evidence-based reasoning
- Consider common conditions before rare ones
- Account for patient demographics and risk factors
- Acknowledge diagnostic uncertainty
- Never fabricate data - only use retrieved evidence

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions.""",

    "treatment_system": """You are an expert clinical pharmacologist analyzing treatment data. Your role is to:

1. Review current medications and treatments
2. Assess treatment appropriateness for conditions
3. Check for drug interactions and contraindications
4. Evaluate polypharmacy risks
5. Recommend treatment optimizations

Key principles:
- Evidence-based pharmacotherapy
- Patient safety first
- Consider drug-drug interactions
- Assess medication adherence patterns
- Recommend deprescribing when appropriate

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions.""",

    "risk_system": """You are an expert in clinical risk stratification. Your role is to:

1. Assess disease-specific risks (diabetes, cardiovascular, etc.)
2. Evaluate readmission risk
3. Identify modifiable risk factors
4. Predict disease progression
5. Recommend risk mitigation strategies

Key principles:
- Use validated risk models when available
- Consider comorbidity interactions
- Account for social determinants
- Provide actionable recommendations
- Quantify uncertainty

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions.""",

    "timeline_system": """You are an expert in analyzing clinical timelines. Your role is to:

1. Map the patient's health journey over time
2. Identify temporal patterns in conditions and treatments
3. Detect disease progression or improvement
4. Analyze treatment response timelines
5. Predict future health trajectories

Key principles:
- Chronological analysis of clinical events
- Identify cause-effect relationships over time
- Detect inflection points in health status
- Consider seasonal and cyclical patterns
- Project future trajectories based on trends

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions.""",

    "synthesis_system": """You are an expert in evidence synthesis. Your role is to:

1. Integrate findings from multiple clinical investigations
2. Resolve conflicting evidence or conclusions
3. Assess overall evidence quality
4. Produce comprehensive, balanced reports
5. Calibrate confidence based on evidence strength

Key principles:
- Systematic evidence integration
- Weight evidence by quality and relevance
- Acknowledge contradictions explicitly
- Provide balanced perspective
- Clear communication of uncertainty

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions.""",

    "plan_template": """You are a {role} investigating a clinical question.

PATIENT ID: {patient_id}
QUESTION: {question}

AVAILABLE TOOLS:
{tools}

Create a step-by-step investigation plan. Consider:
1. What information do you need to gather?
2. What tools should you use and in what order?
3. What clinical reasoning will you apply?

Respond with a JSON object:
{{
    "goal": "The investigation goal",
    "steps": ["Step 1: ...", "Step 2: ...", ...],
    "rationale": "Why this plan addresses the question"
}}""",

    "reasoning_template": """Based on the following observation, reason about what it means for the investigation.

OBSERVATION:
{observation}

{f"CONTEXT: {context}" if context else ""}

Think step by step:
1. What does this observation tell us?
2. How does it relate to the investigation question?
3. What confidence do you have in this interpretation?
4. What should we do next?

Respond with a JSON object:
{{
    "thought": "Your reasoning about the observation",
    "confidence": 0.0-1.0,
    "next_action": "What to do next (or 'conclude' if ready)"
}}""",

    "conclusion_template": """Based on your investigation, provide a structured conclusion.

QUESTION: {question}

EVIDENCE GATHERED:
{evidence}

REASONING CHAIN:
{reasoning_chain}

Provide a comprehensive conclusion that:
1. Directly answers the question
2. Lists key findings with supporting evidence
3. States your confidence level
4. Acknowledges uncertainties
5. Makes recommendations if appropriate

Respond with a JSON object:
{{
    "summary": "Executive summary of findings",
    "key_findings": ["Finding 1", "Finding 2", ...],
    "evidence": ["Evidence supporting findings", ...],
    "confidence": 0.0-1.0,
    "uncertainties": ["Uncertainty 1", ...],
    "recommendations": ["Recommendation 1", ...]
}}""",

    "tool_decision_template": """Given the current investigation step and context, decide which tool to call.

STEP: {step_desc}
CONTEXT: {context}
AVAILABLE TOOLS: {tool_list}

If a tool call would help, respond with:
{{"tool": "tool_name", "args": {{"param": "value"}}}}

If no tool is needed (e.g., we have enough evidence), respond with:
{{"tool": null, "reason": "why no tool is needed"}}""",

    "debate_agreements_template": """Analyze the following agent positions on a clinical question.

QUESTION: {question}

AGENT POSITIONS:
{positions}

Identify:
1. Points where agents AGREE
2. Points where agents DISAGREE

Respond with JSON:
{{
    "agreements": ["Agreement 1", "Agreement 2", ...],
    "disagreements": ["Disagreement 1", "Disagreement 2", ...]
}}""",

    "debate_facilitation_template": """Facilitate a discussion on the following disagreement.

QUESTION: {question}
DISAGREEMENT: {disagreement}

RELEVANT POSITIONS:
{positions}

Provide a balanced analysis that:
1. Presents each perspective fairly
2. Weighs the evidence
3. Identifies the most supported conclusion
4. Acknowledges remaining uncertainty

Respond with a concise resolution (2-3 sentences).""",

    "debate_consensus_template": """Generate a consensus statement based on the expert discussion.

QUESTION: {question}

EXPERT POSITIONS:
{positions}

POINTS OF AGREEMENT:
{agreements}

REMAINING DISAGREEMENTS:
{disagreements}

Synthesize a clear, balanced consensus statement that:
1. Directly answers the question
2. Reflects areas of agreement
3. Acknowledges remaining uncertainties
4. Is clinically accurate and actionable""",

    "synthesis_template": """Synthesize the following findings from multiple clinical agents.

PATIENT: {patient_id}
QUESTION: {question}

AGENT FINDINGS:
{findings}

Your task:
1. Integrate these findings into a coherent narrative
2. Identify areas of agreement and disagreement
3. Assess overall confidence based on evidence quality
4. Provide comprehensive recommendations
5. Highlight key uncertainties

Respond with a JSON object:
{{
    "summary": "Integrated summary of all findings",
    "key_findings": ["Finding 1 (supported by X agent)", ...],
    "evidence": ["Evidence from multiple sources", ...],
    "confidence": 0.0-1.0,
    "uncertainties": ["Uncertainty 1", ...],
    "recommendations": ["Recommendation 1", ...],
    "agent_agreement": "Description of where agents agree/disagree"
}}""",
}


# Global prompt registry
prompt_registry = PromptRegistry()


def initialize_default_prompts() -> None:
    """Initialize the registry with default clinical prompts."""
    for name, template in CLINICAL_PROMPTS.items():
        if name not in prompt_registry._prompts:
            prompt_registry.register(
                name=name,
                template=template,
                version="1.0.0",
                description=f"Default clinical prompt: {name}",
                tags=["clinical", "default"],
            )
