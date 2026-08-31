# Agent Specification

> **🚀 Live**: See agents in action at [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)
> Implementation: `src/aegis/reasoning_agents.py`

## Agent contract

Every agent must have:
- name
- purpose
- allowed tools
- input schema
- output schema
- confidence
- evidence
- failure mode
- timeout
- observability events

## Orchestrator

**Input**: user investigation request
**Output**: task graph + InvestigationReport

**Implementation**: `src/aegis/orchestrator.py`

Rules:
1. Never allow an agent to invent patient data
2. Patient facts must originate from the data layer (Synthea CSVs)
3. Medical knowledge claims must reference retrieved evidence
4. Conflicting evidence triggers critic review
5. Clinical recommendations require human review (`review_required=true`)

## Implemented Agents (v2)

### Diagnostic Agent
**File**: `reasoning_agents.py:DiagnosticAgent`
**Purpose**: Differential diagnosis and diagnostic confidence assessment
**Tools**:
- `get_patient`
- `get_conditions`
- `get_observations`
- `graph_rag_query`

**Output**: Differential diagnoses ranked by confidence + supporting evidence

### Treatment Agent
**File**: `reasoning_agents.py:TreatmentAgent`
**Purpose**: Treatment regimen review and optimization
**Tools**:
- `get_medications`
- `get_allergies`
- `check_drug_interactions`

**Output**: Treatment plan summary + recommendations

### Risk Assessment Agent
**File**: `reasoning_agents.py:RiskAssessmentAgent`
**Purpose**: Patient risk stratification and outcome prediction
**Tools**:
- `get_patient`
- `get_conditions`
- `get_observations`
- `calculate_risk_score`

**Output**: Risk scores per category + contributing factors

### Timeline Agent
**File**: `reasoning_agents.py:TimelineAgent`
**Purpose**: Temporal pattern analysis and disease progression
**Tools**:
- `get_patient`
- `get_encounters`
- `get_conditions`
- `get_observations`
- `temporal_analysis`

**Output**: Chronological event timeline + progression patterns

## Critic Agent

**Implementation**: `src/aegis/debate.py`

Responsibilities:
- Claim/evidence matching
- Contradiction detection between agents
- Uncertainty calibration
- Multi-agent debate orchestration for consensus

## Safety Agent

**Implementation**: `src/aegis/safety.py`

Responsibilities:
- Reject diagnosis/treatment claims as authoritative
- Detect missing evidence
- Enforce `review_required=true` on clinical recommendations
- Block prompt injection attempts
- Flag PII extraction attempts
- Detect hallucinated patient data

## Synthesis Agent

**Implementation**: `src/aegis/orchestrator.py` (final stage)

Output (`InvestigationReport`):

```json
{
  "trace_id": "uuid",
  "patient_id": "string",
  "question": "string",
  "conclusion": "string",
  "evidence": ["string"],
  "confidence": 0.85,
  "review_required": true,
  "reviewed": false,
  "agent_results": [
    {
      "agent": "diagnostic|treatment|risk_assessment|timeline",
      "status": "completed|failed",
      "summary": "string",
      "evidence": ["string"],
      "confidence": 0.87
    }
  ],
  "generated_at": "iso8601"
}
```

## Multi-Agent Debate

When `enable_debate=True` (default for v2 endpoint `/v2/investigations`):
1. Each agent produces initial conclusion
2. Agents see each other's conclusions
3. Iterative refinement (up to N rounds)
4. Consensus or majority opinion extracted
5. Disagreements explicitly logged

See `src/aegis/debate.py` for protocol details.

## Agent Evaluation

Each agent is scored on:
- **Accuracy** — findings match expected results
- **Completeness** — coverage of expected findings
- **Grounding** — conclusions supported by evidence
- **Relevance** — findings relevant to question
- **Confidence calibration** — confidence matches actual accuracy
- **Reasoning quality** — chain-of-logic soundness
- **Tool efficiency** — appropriate tool usage
- **Latency** — response time
- **Safety** — compliance with safety rules

See `src/aegis/evaluation.py` and `docs/EVALUATION.md` for details.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/investigations` | Basic investigation (MVP orchestrator) |
| `POST /v2/investigations` | Multi-agent with debate + evaluation |
| `POST /v1/investigations/stream` | SSE streaming version |
| `WS /ws/investigations` | WebSocket streaming |
| `GET /v2/agents` | List available agents |
| `GET /v2/tools` | List available tools |
| `POST /v2/evaluation/run` | Run benchmark evaluation |
| `GET /v2/evaluation/history` | Past evaluations |
| `GET /v2/evaluation/report/{id}` | Detailed report |

See [DEPLOYMENT.md](../DEPLOYMENT.md) for the live API.