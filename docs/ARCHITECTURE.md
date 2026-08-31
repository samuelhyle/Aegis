# AEGIS Architecture

> **🔴 Live deployment**: [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)
> Backend: [backend-three-tan-79.vercel.app](https://backend-three-tan-79.vercel.app)

## System Overview

AEGIS is deployed as **two Vercel projects**:
- **Frontend** (`web/`) — Next.js 16, deployed as `aegis-beta` project
- **Backend** (`backend/`) — Python 3.12 / FastAPI, deployed as `backend` project

They communicate via a Next.js rewrite rule that forwards `/api/proxy/*` to the backend.

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                         │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vercel Edge CDN — Next.js Frontend                             │
│  https://aegis-beta-bice.vercel.app                             │
│                                                                   │
│  ┌────────────────────┐    ┌─────────────────────────────────┐  │
│  │  React 19          │    │  Next.js API Routes              │  │
│  │  Server Components │    │  • /api/proxy/[...path]         │  │
│  │  TanStack Query    │    │    (catch-all → backend)        │  │
│  │  Zustand stores    │    │  • /api/health                   │  │
│  │  shadcn UI         │    │  • /api/v1/* (mock fallback)     │  │
│  └────────────────────┘    └─────────────────────────────────┘  │
│                                                                   │
│  next.config.ts rewrites:                                        │
│    /api/proxy/:path* → https://backend-three-tan-79.vercel.app/:path* │
└──────────────┬──────────────────────────────────────────────────┘
               │ HTTPS
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vercel Functions — Python 3.12                                  │
│  https://backend-three-tan-79.vercel.app                        │
│                                                                   │
│  app.py  →  Mangum(app)  →  FastAPI ASGI handler                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI App (aegis.api:app)                               │  │
│  │                                                             │  │
│  │  Middleware:                                                │  │
│  │    • Tracing → Opentelemetry spans                          │  │
│  │    • Input validation                                       │  │
│  │    • Compression (gzip)                                     │  │
│  │    • Request logging                                       │  │
│  │    • Error handling                                        │  │
│  │    • Rate limiting                                          │  │
│  │                                                             │  │
│  │  Routers:                                                   │  │
│  │    /health, /metrics, /docs                                 │  │
│  │    /v1/patients/*, /v1/investigations/*, /v1/traces/*      │  │
│  │    /v2/agents, /v2/tools, /v2/investigations               │  │
│  │    /v2/graph-rag/*, /v2/temporal/*, /v2/evaluation/*       │  │
│  │    /v3/evaluation/*                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────────────┘
               │ HTTPS
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  MiniMax-M3 LLM (OpenAI-compatible)                             │
│  https://api.minimax.io/v1                                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Logical Architecture (Backend Internals)

```
                    Next.js UI
                        |
                    FastAPI API
                        |
                  Orchestrator
                        |
                  Task Graph / Event Bus
                        |
        +----------+----------+----------+
        | Timeline | Medication| Evidence |
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

---

## Backend Modules

### Core Orchestration
- **`api.py`** — FastAPI app, all route handlers, middleware
- **`orchestrator.py`** — Coordinates agent execution for investigations
- **`streaming.py`** — SSE streaming for real-time investigation updates
- **`llm.py`** — LLM provider abstraction (MiniMax, OpenAI, local, mock)

### Agents (`reasoning_agents.py`)
- **DiagnosticAgent** — Differential diagnosis, evidence evaluation
- **TreatmentAgent** — Medication review, drug interactions
- **RiskAssessmentAgent** — Risk stratification, outcome prediction
- **TimelineAgent** — Temporal pattern analysis

### Multi-Agent Protocol
- **`debate.py`** — Multi-agent debate for consensus
- **`safety.py`** — Input/output safety gates
- **`evidence.py`** — Evidence tracking with patient journey
- **`evaluation.py`** — Agent evaluation framework

### Advanced Capabilities
- **`graph_rag.py`** — Knowledge graph RAG beyond vector search
- **`temporal.py`** — Time-series analysis, predictions, anomalies
- **`predictive.py`** — Risk prediction, outcome modeling
- **`drug_interactions.py`** — Polypharmacy analysis
- **`clinical_trials.py`** — Clinical trial matching

### Infrastructure
- **`store.py`** — Synthea data store (CSV → pandas DataFrames)
- **`db.py`** — SQLAlchemy ORM, migrations
- **`auth.py`** — JWT auth, role-based access control
- **`cache.py`** — Query caching
- **`tracing.py`** — OpenTelemetry tracing
- **`monitoring.py`** — Metrics, structured logging
- **`rate_limit.py`** — Token bucket rate limiting

---

## Frontend Modules

### Pages (`web/app/`)
```
(dashboard)/
├── dashboard/              # Overview + system stats
├── patients/               # Patient list + details
│   └── [id]/               # Patient detail page
├── investigations/         # Investigations + streaming
│   └── [traceId]/          # Investigation detail
├── analytics/
│   ├── graph-rag/          # Graph RAG visualization
│   ├── temporal/           # Temporal analysis
│   ├── risk/               # Risk assessment
│   ├── evaluation/         # Agent evaluation
│   └── benchmark/          # Benchmark results
├── drug-interactions/      # Drug interaction analysis
├── clinical-trials/        # Clinical trial search
├── search/                 # Vector search
└── settings/               # User settings
```

### State Management
- **TanStack Query** — Server state, caching, refetching
- **Zustand** — Client state (active patient, UI state)
- **React Hook Form** — Form state with Zod validation

### Components
- **shadcn-style UI** — Accessible, themeable primitives
- **Recharts** — Data visualization
- **React Window** — Virtualized lists for large datasets
- **Socket.io client** — Real-time investigation streaming

---

## Data Layer

### Current (MVP)
- **Synthea CSV** → pandas DataFrames loaded into memory
- **SQLite** for traces, reviews, evaluation history
- **In-memory** for investigation reports (TTL cache)

### Production-Ready (Configured)
- **PostgreSQL** + pgvector for transactional + vector data
- **Redis** for distributed caching
- **Object storage** for source documents

```text
Synthea CSV → ingestion → normalized relational model
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              PostgreSQL           pgvector
           (transactions)        (embeddings)
```

---

## AI Layer

Model provider abstraction allows swapping LLMs without code changes:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> LLMResponse: ...
    @abstractmethod
    async def structured_output(self, ...) -> BaseModel: ...

class ProviderFactory:
    _providers = {
        "mock":    MockProvider,
        "openai":  OpenAIProvider,
        "local":   LocalProvider,    # Ollama
        "mlx":     MLXProvider,      # Apple Silicon
        "minimax": MiniMaxProvider,  # ← default in production
    }
```

**Production LLM**: MiniMax-M3 via OpenAI-compatible API at `https://api.minimax.io/v1`

**Agent dependency rule**: Agents depend on the `LLMProvider` interface, not vendor SDKs.

---

## Event Schema

```json
{
  "trace_id": "uuid",
  "patient_id": "string",
  "events": [
    {
      "type": "investigation_started|agent_started|agent_completed|investigation_completed",
      "agent": "diagnostic|treatment|risk_assessment|timeline",
      "timestamp": "iso8601",
      "result": { "summary": "...", "confidence": 0.85 }
    }
  ]
}
```

---

## Safety Architecture

```
User input → Input Safety Gate → Orchestrator → Agents → Output Safety Gate → User
                                       ↓
                                  Evidence Tracker
                                       ↓
                              Critic Review (always)
                                       ↓
                          Human-in-the-Loop (when needed)
```

**Safety rules**:
1. Reject any output claiming diagnosis/treatment as authoritative
2. Detect missing evidence for claims
3. Enforce `review_required=true` on clinical recommendations
4. Block unsafe queries (injection, PII extraction attempts)

---

## Deployment Topology (Production)

```
                Cloudflare/Vercel Edge
                          │
                          ▼
            ┌─────────────────────────┐
            │  Vercel CDN + Edge      │
            │  • Static assets        │
            │  • Next.js SSR         │
            │  • /api/proxy rewrite  │
            └──────────┬──────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │  Vercel Functions       │
            │  (Python 3.12)          │
            │  • Cold start: ~2s      │
            │  • Warm: ~50ms          │
            │  • 50+ endpoints        │
            └──────────┬──────────────┘
                       │
                       ▼
            ┌─────────────────────────┐
            │  MiniMax-M3 LLM         │
            │  • 1M context           │
            │  • 100+ tps             │
            └─────────────────────────┘
```

---

## See Also

- **[DEPLOYMENT.md](../DEPLOYMENT.md)** — Deployment guide
- **[../README.md](../README.md)** — Project overview
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** — MVP planning
- **[AGENTS.md](AGENTS.md)** — Agent specification
- **[EVALUATION.md](EVALUATION.md)** — Evaluation methodology