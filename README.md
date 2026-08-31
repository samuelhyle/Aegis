# AEGIS — Agentic Clinical Intelligence Environment

[![Live](https://img.shields.io/badge/LIVE-aegis--beta--bice.vercel.app-0070f3?style=flat-square&logo=vercel)](https://aegis-beta-bice.vercel.app)
[![Backend](https://img.shields.io/badge/API-backend--three--tan--79.vercel.app-0070f3?style=flat-square&logo=vercel)](https://backend-three-tan-79.vercel.app)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)

> **🔴 Live in production**: [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)
> A portfolio-grade, safety-oriented agentic AI environment for investigating **sYNTHETIC** patient records.
> Research/engineering demonstration only. Not a medical device and not for clinical decision-making.

---

## What is AEGIS?

AEGIS is a **multi-agent clinical intelligence platform** that orchestrates specialized AI agents to investigate synthetic patient records from [Synthea](https://github.com/synthetichealth/synthea). It demonstrates production-grade patterns for agentic AI systems: tool use, retrieval-augmented reasoning, multi-agent debate, evaluation, human-in-the-loop review, and structured outputs.

### **Live Demo Features**

- 🩺 **5 synthetic patients** with full longitudinal records
- 🤖 **4 specialized agents**: Diagnostic, Treatment, Risk Assessment, Timeline
- 🔬 **Multi-agent debate** for consensus conclusions
- 📊 **Graph RAG** for relationship discovery
- ⏱️ **Temporal analysis** with anomaly detection
- ⚖️ **Safety gates** and human review workflows
- 🧠 **MiniMax-M3** LLM integration (OpenAI-compatible)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                         │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vercel Edge — Next.js 16 Frontend                              │
│  https://aegis-beta-bice.vercel.app                             │
│  • React 19 + Server Components                                 │
│  • TanStack Query + Zustand                                     │
│  • shadcn-style components                                      │
│  • /api/proxy/* → forwards to Python backend                    │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vercel Functions — Python 3.12 / FastAPI / Mangum              │
│  https://backend-three-tan-79.vercel.app                        │
│  • 50+ endpoints (v1, v2, v3, multi-agent, graph RAG, temporal) │
│  • Streaming SSE for investigations                             │
│  • Tool-using orchestrator                                      │
│  • SQLite + structured logging                                  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  MiniMax-M3 LLM                                                 │
│  https://api.minimax.io/v1                                      │
│  • OpenAI-compatible Chat Completions                           │
│  • 1M context window, frontier reasoning                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone & install
```bash
git clone https://github.com/samuelhyle/Aegis.git
cd Aegis

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,llm]"

# Frontend
cd web && npm install && cd ..
```

### 2. Configure environment
```bash
# Copy and edit env files
cp .env.example .env.development
cp web/.env.local.example web/.env.local

# Add your MiniMax API key to .env.development
echo "MINIMAX_API_KEY=your-key-here" >> .env.development
```

### 3. Start the stack
```bash
# Terminal 1 — backend (http://localhost:8000)
uvicorn aegis.api:app --reload

# Terminal 2 — frontend (http://localhost:3000)
cd web && npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 📦 Repository Layout

```
aegis/
├── src/aegis/                 # Python backend (FastAPI)
│   ├── api.py                 # Main app + 50+ endpoints
│   ├── llm.py                 # LLM provider abstraction
│   ├── orchestrator.py        # Multi-agent orchestration
│   ├── reasoning_agents.py    # Diagnostic/Treatment/Risk/Timeline
│   ├── graph_rag.py           # Knowledge graph RAG
│   ├── temporal.py            # Time-series analysis
│   ├── debate.py              # Multi-agent debate protocol
│   ├── safety.py              # Input/output safety gates
│   ├── evidence.py            # Evidence tracking
│   ├── evaluation.py          # Agent evaluation framework
│   └── ...
│
├── web/                       # Next.js 16 frontend
│   ├── app/
│   │   ├── (dashboard)/       # Protected pages
│   │   │   ├── dashboard/
│   │   │   ├── patients/
│   │   │   ├── investigations/
│   │   │   ├── analytics/     # Graph RAG, Temporal, Eval, Risk
│   │   │   └── settings/
│   │   └── api/proxy/         # Backend proxy
│   ├── components/
│   ├── lib/
│   └── ...
│
├── backend/                   # Vercel Python deployment
│   ├── app.py                 # Vercel entry point
│   ├── src/aegis/             # Backend code (synced)
│   ├── data/synthea/          # Seed CSV data
│   ├── requirements.txt
│   └── vercel.json
│
├── data/synthea/              # Generated Synthea CSVs
├── docs/                      # Architecture & planning docs
├── prompts/                   # Agent system prompts
└── tests/                     # Pytest suite
```

---

## 🎯 Core Capabilities

### Multi-Agent Orchestration
Four specialized agents work in parallel and debate:
- **Diagnostic** — Differential diagnosis, evidence evaluation
- **Treatment** — Medication review, drug interaction checking
- **Risk Assessment** — Risk stratification, outcome prediction
- **Timeline** — Temporal pattern detection, disease progression

### Graph RAG
Beyond vector search — traverses patient knowledge graphs to discover:
- Comorbidity patterns
- Causal chains (condition → treatment → outcome)
- Communities of related health issues
- Centrality-ranked key factors

### Temporal Intelligence
- Lab value trajectory prediction
- Disease progression modeling
- Anomaly detection (z-score, out-of-range)
- Health state transitions

### Safety & Auditability
- Input safety gate (blocks unsafe queries)
- Output safety gate (flags low-confidence results)
- Human-in-the-loop review workflow
- Complete trace logging

---

## 🧪 Evaluation Framework

AEGIS includes a built-in benchmark suite:
- **Diagnostic accuracy** vs expected findings
- **Completeness** coverage
- **Grounding** evidence support
- **Confidence calibration** vs expected range
- **Reasoning quality** chain analysis
- **Tool efficiency** usage metrics

See [`docs/EVALUATION.md`](docs/EVALUATION.md) for details.

---

## 🛠️ LLM Provider Support

| Provider | Model | Config |
|----------|-------|--------|
| **MiniMax** (default) | MiniMax-M3 | `LLM_PROVIDER=minimax` |
| OpenAI | gpt-4o, gpt-4o-mini | `LLM_PROVIDER=openai` |
| Ollama (local) | gemma, llama, mistral | `LLM_PROVIDER=local` |
| MLX (Apple Silicon) | gemma-4-26b | `LLM_PROVIDER=mlx` |
| Mock (dev) | — | `LLM_PROVIDER=mock` |

Set `MINIMAX_API_KEY` (or `OPENAI_API_KEY`, etc.) in your environment.

---

## 🚢 Deployment

Both frontend and backend deploy to **Vercel**:

| Project | URL |
|---------|-----|
| Frontend | [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app) |
| Backend | [backend-three-tan-79.vercel.app](https://backend-three-tan-79.vercel.app) |

### Deploy your own

```bash
# Frontend
cd web && vercel --prod

# Backend
cd backend && vercel --prod

# Set env vars
vercel env add LLM_PROVIDER production  # value: minimax
vercel env add LLM_MODEL production     # value: MiniMax-M3
vercel env add MINIMAX_API_KEY production  # your key
vercel env add AEGIS_AUTH_DISABLED production  # true
```

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full deployment guide.

---

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Production deployment guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System architecture deep-dive
- **[docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)** — MVP planning & scope
- **[docs/AGENTS.md](docs/AGENTS.md)** — Agent design specification
- **[docs/EVALUATION.md](docs/EVALUATION.md)** — Evaluation methodology
- **[docs/ROADMAP.md](docs/ROADMAP.md)** — Development roadmap
- **[docs/DATASET_SETUP.md](docs/DATASET_SETUP.md)** — Generating Synthea data

---

## ⚠️ Safety Notice

This is a **research and engineering demonstration** project.
- Uses **synthetic** patient data from Synthea — no real PHI
- All AI outputs are **advisory only** — not for clinical decisions
- Every investigation is **traceable** and **reviewable**
- Built-in safety gates block unsafe queries

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- [Synthea](https://github.com/synthetichealth/synthea) — synthetic patient generator
- [FastAPI](https://fastapi.tiangolo.com/) — backend framework
- [Next.js](https://nextjs.org/) — frontend framework
- [Vercel](https://vercel.com/) — hosting
- [MiniMax](https://platform.minimax.io/) — LLM provider