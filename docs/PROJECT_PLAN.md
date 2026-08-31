# AEGIS Complete Project Plan

> **🚀 Status**: **All phases complete and deployed to production**
> Live at: [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)
> Backend: [backend-three-tan-79.vercel.app](https://backend-three-tan-79.vercel.app)

## 1. Vision

Build an auditable multi-agent AI environment that investigates synthetic longitudinal patient records. The objective is not automated diagnosis. The objective is to demonstrate production-oriented AI engineering: orchestration, tool use, retrieval, evaluation, observability, uncertainty handling and human oversight.

## 2. Target portfolio story

AEGIS demonstrates that an AI solution can move through the complete lifecycle:

Opportunity -> architecture -> prototype -> evaluation -> monitoring -> human review -> iteration -> production-ready service.

## 3. Dataset strategy

Primary dataset: Synthea.

Synthea is open source and generates synthetic patient records in CSV and FHIR formats. The project should start with 100-1,000 locally generated patients and scale later.

Recommended tables:
- patients
- encounters
- conditions
- medications
- observations
- procedures
- allergies
- careplans
- immunizations

Do not commit large generated datasets to Git. Commit a tiny synthetic fixture and provide reproducible generation/import instructions.

## 4. Core use cases

UC-01 Patient timeline investigation
UC-02 Medication history investigation
UC-03 Trend detection
UC-04 Evidence retrieval
UC-05 Multi-agent disagreement
UC-06 Human review
UC-07 Evaluation of an investigation
UC-08 Agent trace inspection

## 5. Agent roles

Orchestrator:
- Parse request
- Build task graph
- Delegate
- Track state
- Decide when review is required

Timeline Agent:
- Construct longitudinal timeline
- Identify temporal changes
- Return structured facts

Medication Agent:
- Summarize medication history
- Detect changes and possible data conflicts
- Later: call a licensed/open medication knowledge tool

Evidence Agent:
- Retrieve relevant source documents
- Return source IDs, snippets and relevance scores
- Never invent citations

Critic Agent:
- Challenge unsupported claims
- Identify contradictions
- Check whether evidence actually supports each claim

Safety Agent:
- Detect medical advice
- Force uncertainty
- Require human review
- Block unsafe output modes

Synthesis Agent:
- Produce a structured evidence-grounded report
- Separate facts, hypotheses and unknowns

Evaluation Agent:
- Score evidence coverage
- citation correctness
- completeness
- consistency
- latency
- cost

## 6. Phase roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 — Foundation | FastAPI, Pydantic, Synthea import, SQLite/PostgreSQL, basic tests | ✅ |
| Phase 1 — Agent runtime | Agent interface, task objects, event bus, orchestration graph, trace IDs, parallel execution | ✅ |
| Phase 2 — LLM integration | Provider abstraction, structured JSON outputs, retry/fallback, prompt versioning, token/cost tracking | ✅ |
| Phase 3 — RAG | Document ingestion, chunking, embeddings, vector database, reranking, evidence objects, citation enforcement | ✅ |
| Phase 4 — Safety | Confidence thresholds, contradiction detection, prompt injection defenses, PII checks, human approval gate, audit log | ✅ |
| Phase 5 — Evaluation | 50-200 benchmark questions, metrics (factuality, evidence coverage, retrieval precision, citation correctness, hallucination rate, latency, cost) | ✅ |
| Phase 6 — UI | Next.js interface (patient selector, investigation composer, agent graph, live event trace, evidence panel, final report, evaluation dashboard, human-review queue) | ✅ |
| Phase 7 — Production engineering | Docker Compose, PostgreSQL, Redis, OpenTelemetry, Prometheus/Grafana, CI, security scanning, rate limiting, structured logging | ✅ |

### 🎉 All phases delivered and live in production

Visit the [live deployment](https://aegis-beta-bice.vercel.app) to see the complete system in action.

## 7. Portfolio acceptance criteria

A strong v1 should:
- run locally with one command
- use reproducible synthetic data
- show at least four cooperating agents
- expose traces
- have automated tests
- demonstrate RAG
- show evaluation metrics
- clearly separate facts from generated interpretation
- require human review for medical conclusions
- include architecture and ADR documentation
