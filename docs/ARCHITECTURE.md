# AEGIS Architecture

## Logical architecture

```text
Next.js UI
   |
FastAPI API
   |
Orchestrator
   |
Task Graph / Event Bus
   |
+----------+----------+----------+
| Timeline | Medication | Evidence |
+----------+----------+----------+
              |
            Critic
              |
            Safety
              |
          Synthesis
              |
      Evaluation + Audit
```

## Data layer

Synthea CSV -> ingestion -> normalized relational model.

Later:
- PostgreSQL for transactional state
- pgvector/Qdrant for retrieval
- object storage for source documents

## AI layer

Use a model provider abstraction:

```text
LLMProvider
  |- OpenAIProvider
  |- LocalProvider
  |- MockProvider
```

Agents should depend on interfaces, not vendor-specific SDKs.

## Event schema

Every agent action should emit:

```json
{
  "trace_id": "...",
  "event_id": "...",
  "agent": "timeline",
  "event_type": "tool_call",
  "timestamp": "...",
  "input_ref": "...",
  "output_ref": "...",
  "latency_ms": 123,
  "token_usage": 0
}
```

## Security principles

- Synthetic data by default
- No real patient data in the repository
- Secrets only through environment variables
- Validate tool arguments
- Allow-list tools
- Log decisions, not sensitive prompts
- Human approval for high-risk actions

## Safety layer (Phase 4)

The `safety.py` module provides comprehensive safety gates:

```text
SafetyGate
  |- ConfidenceGate       # Tiered thresholds: high/medium/low/critical
  |- ContradictionDetector # Detects contradictions between agents and evidence
  |- PromptInjectionDefender # Blocks prompt injection attacks
  |- PIIDetector          # Detects and redacts PII in inputs/outputs
  |- HumanApprovalGate    # Enforces human review for risky outputs
  |- SafetyAuditLogger    # Hash-chained audit log with integrity verification
```

Safety checks are applied at:
1. **Input**: Prompt injection detection, PII detection, length validation
2. **Output**: Confidence gating, contradiction detection, PII redaction
3. **Audit**: All checks are logged with cryptographic chain integrity

## Evaluation layer (Phase 6)

Extended evaluation framework with persistence:

```text
EnhancedEvaluationManager
  |- ExtendedMetricsCalculator  # Factuality, hallucination, citations, cost
  |- AgentComparator            # A/B benchmarking across agents
  |- SyntheticBenchmarkGenerator # Generate cases from synthetic patients
  |- EvaluationStore            # SQLite persistence for history/trends
  |- EvaluationPipeline         # Automated evaluation with all metrics
```

API endpoints:
- `/v3/evaluation/extended-metrics` - Calculate extended metrics
- `/v3/evaluation/synthetic-benchmark` - Generate benchmark from patients
- `/v3/evaluation/history` - Persistent evaluation history
- `/v3/evaluation/trends` - Performance trends over time
- `/v3/evaluation/report/{id}` - Retrieve specific reports

## Frontend layer (Phase 7)

Next.js 16 + React 19 + Tailwind CSS 4 + Recharts:

```text
app/
  (dashboard)/
    dashboard/         # Overview stats, recent patients, alerts
    patients/          # Patient list, detail (10-tab view)
    investigations/    # Global list, [traceId] report view
    analytics/
      evaluation/      # Evaluation dashboard with charts
      risk/            # Risk analytics
      temporal/        # Temporal analytics
      graph-rag/       # Graph RAG explorer
```

Key components:
- `lib/store/patient.ts` - Zustand global patient context
- `lib/api/client.ts` - Typed API client (35+ endpoints)
- `lib/hooks/useQueries.ts` - 30+ React Query hooks
- `components/ui/` - Design system (Button, Card, Badge, Tabs, etc.)
- `components/layout/` - DashboardLayout, Sidebar, Header
