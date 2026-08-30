# 8-Week Portfolio Roadmap

## Week 1 ✅
Foundation, Synthea generation/import, database model, API.

## Week 2 ✅
Agent interface, orchestrator, task graph, event tracing.

## Week 3 ✅
LLM provider abstraction, structured outputs, prompt registry.

## Week 4 ✅
RAG pipeline and evidence objects.

## Week 5 ✅
Safety hardening: confidence thresholds, contradiction detection, prompt injection defenses, PII checks, human-in-the-loop gate, audit logging.

## Week 6 ✅
Extended metrics (factuality, hallucination, citation correctness, token/cost efficiency), agent comparison tool, synthetic benchmark generator, SQLite persistence, evaluation API v3.

## Week 7 ✅
Next.js UI: evaluation dashboard (`/analytics/evaluation`), investigation report view (`/investigations/[traceId]`), global patient store (Zustand), sidebar evaluation link, investigation table links to report.

## Week 8
Docker, CI/CD, observability, documentation, demo video and portfolio write-up.

## Final demo

Show one investigation from start to finish:
1. Select patient.
2. Ask question.
3. Orchestrator creates plan.
4. Agents run in parallel.
5. Evidence is retrieved.
6. Critic challenges findings.
7. Safety gate requests review.
8. Synthesis produces report.
9. Evaluation scores the run.
10. Dashboard displays trace, latency and evidence.
