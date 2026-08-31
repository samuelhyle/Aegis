from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from .agent_metrics import agent_metrics
from .api_response import paginated_response
from .auth import UserRole, get_current_user, require_role
from .clinical_tools import *  # noqa: F401,F403 - Register clinical tools
from .compression import CompressionMiddleware
from .cors_config import setup_cors
from .error_handling import ErrorHandlerMiddleware, RequestLoggingMiddleware
from .evidence import (
    EvidenceItem,
    PatientJourney,
    PatientState,
    PatientStateSnapshot,
    PrognosisEngine,
)
from .input_validation import InputValidationMiddleware
from .models import InvestigationReport, InvestigationRequest, ReviewRequest
from .monitoring import get_metrics, metrics, structured_logger
from .orchestrator import Orchestrator
from .performance import PerformanceMonitor, query_cache
from .rate_limit import RateLimitMiddleware
from .safety import safety_gate as _safety_gate
from .streaming import StreamingOrchestrator
from .tracing import FastAPITracingMiddleware, get_tracer

app = FastAPI(
    title="AEGIS Agentic Clinical Intelligence",
    version="0.4.0",
    description="Production-grade agentic AI environment for clinical data investigation.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS
setup_cors(app)

# Add middleware (order matters - last added = first executed)
app.add_middleware(FastAPITracingMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(CompressionMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)

orchestrator = Orchestrator()
streaming_orchestrator = StreamingOrchestrator()

# Global instances
performance_monitor = PerformanceMonitor()

# In-memory trace store for visualization
traces: dict[str, InvestigationReport] = {}


def _clean_nan_values(data: Any) -> Any:
    """Recursively clean NaN and infinity values from data for JSON serialization."""
    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, dict):
        return {k: _clean_nan_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_nan_values(item) for item in data]
    return data


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "aegis",
        "version": "0.3.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics")
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    from fastapi.responses import PlainTextResponse

    base_metrics = get_metrics()
    agent_prom = agent_metrics.get_prometheus_format()

    lines = []
    for key, value in base_metrics.get("counters", {}).items():
        name = key.split("{")[0]
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{key} {value}")

    for key, value in base_metrics.get("gauges", {}).items():
        name = key.split("{")[0]
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{key} {value}")

    for key, hist in base_metrics.get("histograms", {}).items():
        name = key.split("{")[0]
        lines.append(f"# TYPE {name} histogram")
        lines.append(f"{name}_count {hist.get('count', 0)}")
        lines.append(f"{name}_sum {hist.get('sum', 0):.2f}")

    if agent_prom:
        lines.append("")
        lines.append(agent_prom)

    return PlainTextResponse(content="\n".join(lines), media_type="text/plain; version=0.0.4")


@app.get("/metrics/agents")
def agent_metrics_summary():
    """Get agent-specific performance metrics summary."""
    return agent_metrics.get_all_summaries()


@app.get("/traces")
def list_traces_otlp(
    limit: int = Query(default=20, le=100, ge=1),
    user: Any = Depends(get_current_user),
):
    """List distributed traces from OpenTelemetry-compatible tracer."""
    provider = get_tracer()
    return {"traces": provider.get_traces(limit), "total": len(provider._spans)}


@app.get("/traces/{trace_id}")
def get_trace_otlp(
    trace_id: str,
    user: Any = Depends(get_current_user),
):
    """Get detailed trace with all spans."""
    provider = get_tracer()
    detail = provider.get_trace_detail(trace_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Trace not found")
    return detail


@app.post("/v1/investigations")
def investigate(
    request: InvestigationRequest,
    user: Any = Depends(get_current_user),
):
    """Run a clinical investigation on a patient record."""
    import time
    start_time = time.time()

    # Safety input check
    input_check = _safety_gate.check_input(request.question, trace_id="")
    if not input_check["safe"]:
        return {
            "status": "blocked",
            "reason": "Input failed safety checks",
            "details": input_check,
        }

    report = orchestrator.investigate(request.patient_id, request.question)
    traces[report.trace_id] = report

    # Safety output check
    evidence_texts = [
        s.content for s in report.agent_results
        if hasattr(s, "content") and s.content
    ] if report.agent_results else []

    output_check = _safety_gate.check_output(
        confidence=report.confidence,
        conclusion=report.conclusion,
        evidence=evidence_texts,
        user_question=request.question,
        trace_id=report.trace_id,
        patient_id=request.patient_id,
    )

    # Record metrics
    duration_ms = (time.time() - start_time) * 1000
    metrics.inc_counter("investigations_total", labels={"patient_id": request.patient_id})
    metrics.observe_histogram("investigation_duration_ms", duration_ms)
    metrics.set_gauge("investigation_confidence", report.confidence)

    # Log structured event
    structured_logger.log_investigation(
        trace_id=report.trace_id,
        patient_id=request.patient_id,
        question=request.question,
        confidence=report.confidence,
        review_required=report.review_required,
        agent_count=len(report.agent_results),
        duration_ms=duration_ms,
    )

    report_dict = report.model_dump() if hasattr(report, "model_dump") else report.__dict__
    report_dict["safety_check"] = output_check

    return report_dict


@app.post("/v1/investigations/stream")
async def investigate_stream(
    request: InvestigationRequest,
    user: Any = Depends(get_current_user),
):
    """Stream investigation results as Server-Sent Events."""
    return StreamingResponse(
        streaming_orchestrator.investigate_sse(
            request.patient_id,
            request.question,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.websocket("/ws/investigations")
async def investigate_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time investigation streaming."""
    await websocket.accept()

    try:
        # Receive investigation request
        data = await websocket.receive_json()
        patient_id = data.get("patient_id")
        question = data.get("question")

        if not patient_id or not question:
            await websocket.send_json({
                "type": "error",
                "message": "patient_id and question are required",
            })
            return

        # Stream investigation results
        async for event in streaming_orchestrator.investigate_stream(patient_id, question):
            await websocket.send_json(event)

            # Store completed investigation
            if event.get("type") == "investigation_completed":
                report_data = event.get("report", {})
                if report_data:
                    report = InvestigationReport(**report_data)
                    traces[report.trace_id] = report

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


@app.get("/v1/traces/{trace_id}")
def get_trace(
    trace_id: str,
    user: Any = Depends(get_current_user),
):
    """Get a specific investigation trace by ID."""
    report = traces.get(trace_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return report


@app.post("/v1/traces/{trace_id}/review")
def review_investigation(
    trace_id: str,
    review: ReviewRequest,
    user: Any = Depends(require_role(UserRole.CLINICIAN)),
):
    """Human-in-the-loop review endpoint for investigation reports."""
    report = traces.get(trace_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    report.reviewed = True
    report.review_decision = review.decision
    report.reviewer_id = review.reviewer_id
    report.review_notes = review.notes
    report.reviewed_at = datetime.now(timezone.utc)

    # If approved, mark review_required as False
    if review.decision == "approved":
        report.review_required = False

    traces[trace_id] = report

    # Record metrics
    metrics.inc_counter("reviews_total", labels={"decision": review.decision.value})
    structured_logger.log_review(trace_id, review.decision.value, review.reviewer_id)

    return report


@app.get("/v1/traces")
def list_traces(
    patient_id: str | None = None,
    reviewed: bool | None = None,
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    user: Any = Depends(get_current_user),
):
    """List investigation traces with optional filtering and pagination."""
    results = list(traces.values())

    if patient_id is not None:
        results = [r for r in results if r.patient_id == patient_id]

    if reviewed is not None:
        results = [r for r in results if r.reviewed == reviewed]

    # Sort by generated_at descending
    results.sort(key=lambda r: r.generated_at, reverse=True)

    # Apply pagination
    total = len(results)
    page = (offset // limit) + 1 if limit > 0 else 1
    paginated = results[offset:offset + limit]

    # Convert to dicts for response
    traces_data = [
        r.model_dump() if hasattr(r, "model_dump") else r.__dict__
        for r in paginated
    ]

    return paginated_response(
        data=traces_data,
        total=total,
        page=page,
        per_page=limit,
    )


# ---------------------------------------------------------------------------
# Revolutionary Multi-Agent Investigation Endpoints
# ---------------------------------------------------------------------------

class MultiAgentInvestigationRequest(InvestigationRequest):
    """Request for multi-agent investigation."""
    agents: list[str] | None = None  # Specific agents to use
    enable_debate: bool = False  # Off by default for performance
    evaluate: bool = True  # Run evaluation after investigation


@app.post("/v2/investigations")
async def investigate_v2(
    request: MultiAgentInvestigationRequest,
    user: Any = Depends(get_current_user),
):
    """Run a revolutionary multi-agent investigation with LLM reasoning and debate.

    This endpoint uses:
    - Specialized reasoning agents (Diagnostic, Treatment, Risk, Timeline)
    - Tool use for evidence gathering
    - Chain-of-thought reasoning
    - Multi-agent debate for consensus
    - Automated evaluation

    Agents:
    - diagnostic: Diagnostic reasoning and differential diagnosis
    - treatment: Treatment analysis and medication review
    - risk_assessment: Risk stratification and outcome prediction
    - timeline: Temporal pattern analysis
    """
    import time

    from .debate import MultiAgentOrchestrator
    from .evaluation import evaluator, trace_collector

    start_time = time.perf_counter()

    # Initialize orchestrator
    orchestrator_v2 = MultiAgentOrchestrator()

    # Start trace
    trace = trace_collector.start_trace(request.patient_id, request.question)

    try:
        # Safety input check
        input_check = _safety_gate.check_input(request.question, trace_id=trace.trace_id)
        if not input_check["safe"]:
            return {
                "status": "blocked",
                "reason": "Input failed safety checks",
                "details": input_check,
                "trace_id": trace.trace_id,
            }

        # Run investigation
        result = await orchestrator_v2.investigate(
            patient_id=request.patient_id,
            question=request.question,
            agents_to_use=request.agents,
            enable_debate=request.enable_debate,
        )

        # Safety output check
        conclusion_text = result.final_conclusion.summary if result.final_conclusion else ""
        evidence_texts = result.final_conclusion.evidence if result.final_conclusion else []
        confidence = result.final_conclusion.confidence if result.final_conclusion else 0.0

        output_check = _safety_gate.check_output(
            confidence=confidence,
            conclusion=conclusion_text,
            evidence=evidence_texts,
            user_question=request.question,
            trace_id=trace.trace_id,
            patient_id=request.patient_id,
        )

        # Run evaluation if requested
        evaluations = {}
        if request.evaluate and result.agent_conclusions:
            for agent_name, conclusion in result.agent_conclusions.items():
                eval_result = await evaluator.evaluate_agent(
                    agent_name=agent_name,
                    question=request.question,
                    conclusion=conclusion,
                )
                evaluations[agent_name] = {
                    "overall_score": eval_result.overall_score,
                    "scores": [
                        {
                            "metric": s.metric.value,
                            "score": s.score,
                            "explanation": s.explanation,
                        }
                        for s in eval_result.scores
                    ],
                    "strengths": eval_result.strengths,
                    "weaknesses": eval_result.weaknesses,
                }

        # Update trace
        trace.final_conclusion = {
            "summary": result.final_conclusion.summary if result.final_conclusion else "",
            "confidence": result.final_conclusion.confidence if result.final_conclusion else 0.0,
        }
        trace.timing = {
            "total_ms": result.total_duration_ms,
            "tool_calls": result.total_tool_calls,
            "reasoning_steps": result.total_reasoning_steps,
        }

        # Build response
        response = {
            "investigation_id": result.investigation_id,
            "patient_id": result.patient_id,
            "question": result.question,
            "conclusion": {
                "summary": result.final_conclusion.summary if result.final_conclusion else "",
                "key_findings": result.final_conclusion.key_findings if result.final_conclusion else [],
                "evidence": result.final_conclusion.evidence if result.final_conclusion else [],
                "confidence": result.final_conclusion.confidence if result.final_conclusion else 0.0,
                "uncertainties": result.final_conclusion.uncertainties if result.final_conclusion else [],
                "recommendations": result.final_conclusion.recommendations if result.final_conclusion else [],
            },
            "agent_findings": {
                name: {
                    "summary": conclusion.summary,
                    "key_findings": conclusion.key_findings,
                    "confidence": conclusion.confidence,
                    "reasoning_steps": len(conclusion.reasoning_chain),
                }
                for name, conclusion in result.agent_conclusions.items()
            },
            "debate": {
                "consensus": result.debate_result.final_consensus if result.debate_result else None,
                "agreements": result.debate_result.key_agreements if result.debate_result else [],
                "disagreements": result.debate_result.key_disagreements if result.debate_result else [],
                "rounds": len(result.debate_result.rounds) if result.debate_result else 0,
            } if result.debate_result else None,
            "evaluations": evaluations,
            "safety_check": output_check,
            "metrics": {
                "total_duration_ms": result.total_duration_ms,
                "total_tool_calls": result.total_tool_calls,
                "total_reasoning_steps": result.total_reasoning_steps,
                "agents_used": list(result.agent_conclusions.keys()),
            },
            "trace_id": trace.trace_id,
        }

        # Record metrics
        duration_ms = (time.perf_counter() - start_time) * 1000
        metrics.inc_counter("investigations_v2_total")
        metrics.observe_histogram("investigation_v2_duration_ms", duration_ms)

        return response

    except HTTPException:
        raise
    except Exception as e:
        import traceback as tb
        print(f"investigate_v2 error: {e}\n{tb.format_exc()}", flush=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-agent investigation failed: {type(e).__name__}: {str(e)[:300]}",
        )


@app.get("/v2/agents")
def list_agents(user: Any = Depends(get_current_user)):
    """List available reasoning agents and their capabilities."""
    return {
        "agents": [
            {
                "name": "diagnostic",
                "role": "diagnostician",
                "description": "Analyzes patient data to identify and evaluate potential diagnoses",
                "capabilities": [
                    "Differential diagnosis reasoning",
                    "Evidence-based diagnostic evaluation",
                    "Diagnostic confidence assessment",
                ],
            },
            {
                "name": "treatment",
                "role": "clinical pharmacologist",
                "description": "Analyzes treatment plans, medications, and therapeutic effectiveness",
                "capabilities": [
                    "Medication review and optimization",
                    "Drug interaction analysis",
                    "Treatment effectiveness assessment",
                ],
            },
            {
                "name": "risk_assessment",
                "role": "risk stratification specialist",
                "description": "Assesses patient risks and predicts outcomes",
                "capabilities": [
                    "Disease risk scoring",
                    "Readmission risk prediction",
                    "Complication risk assessment",
                ],
            },
            {
                "name": "timeline",
                "role": "clinical timeline analyst",
                "description": "Analyzes temporal patterns in patient health data",
                "capabilities": [
                    "Disease progression analysis",
                    "Treatment timeline mapping",
                    "Temporal pattern detection",
                ],
            },
        ]
    }


@app.get("/v2/tools")
def list_tools(
    category: str | None = None,
    user: Any = Depends(get_current_user),
):
    """List available tools for agents."""

    from .tools import ToolCategory, tool_registry

    categories = None
    if category:
        try:
            categories = [ToolCategory(category)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    definitions = tool_registry.get_all_definitions()
    if categories:
        definitions = [d for d in definitions if d.category in categories]

    return {
        "tools": [
            {
                "name": d.name,
                "description": d.description,
                "category": d.category.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                    }
                    for p in d.parameters
                ],
                "returns": d.returns,
            }
            for d in definitions
        ],
        "total": len(definitions),
    }


@app.get("/v2/traces/{trace_id}")
def get_trace_v2(
    trace_id: str,
    user: Any = Depends(get_current_user),
):
    """Get a detailed investigation trace with reasoning chains."""
    from .evaluation import trace_collector

    trace = trace_collector.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace_collector.export_trace(trace_id)


@app.get("/v2/evaluations")
def list_evaluations(
    limit: int = Query(default=10, le=50),
    user: Any = Depends(get_current_user),
):
    """List recent agent evaluations."""

    # This would normally come from a database
    return {
        "message": "Evaluation history endpoint - connect to database for persistence",
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Graph RAG Endpoints - Revolutionary Knowledge Graph Retrieval
# ---------------------------------------------------------------------------

@app.get("/v2/graph-rag/{patient_id}")
def get_graph_rag_evidence(
    patient_id: str,
    query: str = Query(..., min_length=1, description="Search query"),
    user: Any = Depends(get_current_user),
):
    """Retrieve evidence using Graph RAG - finds hidden relationships through graph traversal.

    This is a REVOLUTIONARY approach that goes beyond vector search:
    - **Graph Traversal**: Explores relationships between entities
    - **Path Analysis**: Finds causal chains and treatment pathways
    - **Pattern Discovery**: Identifies comorbidities and temporal patterns
    - **Community Detection**: Finds clusters of related health issues
    """
    from .graph_rag import GraphRAGRetriever, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    retriever = GraphRAGRetriever(graph)

    result = retriever.retrieve(query, patient_id=patient_id)

    return _clean_nan_values(result.to_dict())


@app.get("/v2/graph-rag/{patient_id}/patterns")
def get_patient_patterns(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Discover hidden patterns in a patient's health graph.

    Discovers:
    - **Comorbidity Patterns**: Conditions that occur together
    - **Treatment Patterns**: Medications used for conditions
    - **Temporal Patterns**: Sequences of health events
    - **Outcome Patterns**: Treatment → result relationships
    """
    from .graph_rag import PatternDiscoveryEngine, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    pattern_engine = PatternDiscoveryEngine(graph)

    patterns = pattern_engine.discover_all_patterns(patient_id)

    return _clean_nan_values({
        "patient_id": patient_id,
        "patterns": [p.to_dict() for p in patterns],
        "pattern_count": len(patterns),
    })


@app.get("/v2/graph-rag/{patient_id}/causal-chains")
def get_causal_chains(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Find causal chains in patient data: condition → treatment → outcome.

    Useful for understanding treatment effectiveness and health trajectories.
    """
    from .graph_rag import GraphAlgorithms, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    chains = algorithms.find_causal_chains(graph, patient_id)

    return _clean_nan_values({
        "patient_id": patient_id,
        "causal_chains": [c.to_dict() for c in chains],
        "chain_count": len(chains),
    })


@app.get("/v2/graph-rag/{patient_id}/communities")
def get_patient_communities(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Find communities (clusters) of related health issues in patient's graph.

    Communities represent groups of closely related conditions, treatments,
    and observations that form coherent health themes.
    """
    from .graph_rag import GraphAlgorithms, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    # Get patient subgraph
    subgraph = graph.get_subgraph(patient_id, depth=2)
    communities = algorithms.find_communities(subgraph)

    return _clean_nan_values({
        "patient_id": patient_id,
        "communities": [c.to_dict() for c in communities],
        "community_count": len(communities),
    })


@app.get("/v2/graph-rag/{patient_id}/centrality")
def get_graph_centrality(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Calculate centrality scores for nodes in patient's health graph.

    Centrality identifies the most important health factors - conditions,
    medications, or observations that are most connected to other elements.
    """
    from .graph_rag import GraphAlgorithms, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    # Get patient subgraph
    subgraph = graph.get_subgraph(patient_id, depth=2)
    centrality = algorithms.calculate_centrality(subgraph)

    # Get top central nodes
    top_central = sorted(
        centrality.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:20]

    return _clean_nan_values({
        "patient_id": patient_id,
        "centrality_scores": [
            {
                "node_id": nid,
                "score": score,
                "description": graph.get_node(nid).properties.get("description", "") if graph.get_node(nid) else "",
            }
            for nid, score in top_central
        ],
    })


@app.get("/v2/graph-rag/treatment-pathways/{condition}")
def get_treatment_pathways(
    condition: str,
    user: Any = Depends(get_current_user),
):
    """Find common treatment pathways for a condition across all patients.

    Shows what treatments are typically used for a given condition,
    based on patterns across the entire patient population.
    """
    from .graph_rag import GraphAlgorithms, build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)
    algorithms = GraphAlgorithms()

    pathways = algorithms.find_treatment_pathways(graph, condition)

    return _clean_nan_values({
        "condition": condition,
        "pathways": [p.to_dict() for p in pathways[:20]],
        "pathway_count": len(pathways),
    })


@app.get("/v2/graph-rag/related-conditions/{condition}")
def get_related_conditions(
    condition: str,
    user: Any = Depends(get_current_user),
):
    """Find conditions related to a given condition through graph traversal.

    Discovers comorbidities and related conditions that frequently
    co-occur with the specified condition.
    """
    from .graph_rag import build_knowledge_graph
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    graph = build_knowledge_graph(store)

    # Find matching conditions
    matching_conditions = []
    for node in graph.query(node_type="condition"):
        if condition.lower() in node.properties.get("description", "").lower():
            matching_conditions.append(node)

    related = []
    for cond_node in matching_conditions[:3]:
        # Find patients with this condition
        for edge in graph.edges:
            if edge.target == cond_node.id and edge.edge_type == "has_condition":
                patient_id = edge.source

                # Get other conditions
                other_conditions = graph.get_patient_conditions(patient_id)
                for other in other_conditions:
                    if other.id != cond_node.id:
                        related.append({
                            "condition": other.properties.get("description", ""),
                            "relationship": "co-occurs with",
                            "patient_id": patient_id[:8] + "...",
                        })

    return _clean_nan_values({
        "query_condition": condition,
        "matching_conditions": [
            c.properties.get("description", "") for c in matching_conditions
        ],
        "related_conditions": related[:20],
    })


# ---------------------------------------------------------------------------
# Temporal Intelligence Endpoints - Disease Progression & Trajectory Prediction
# ---------------------------------------------------------------------------

@app.get("/v2/temporal/{patient_id}")
def get_temporal_analysis(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Comprehensive temporal analysis of a patient's health.

    Analyzes:
    - Disease progression over time
    - Lab value trends and predictions
    - Temporal anomalies
    - Health state transitions
    """
    from .store import SyntheaStore
    from .temporal import TemporalReasoningEngine

    store = SyntheaStore()
    store.load()

    engine = TemporalReasoningEngine(store)
    result = engine.analyze_patient_timeline(patient_id)

    return _clean_nan_values(result)


@app.get("/v2/temporal/{patient_id}/anomalies")
def get_temporal_anomalies(
    patient_id: str,
    lab_name: str | None = None,
    user: Any = Depends(get_current_user),
):
    """Detect anomalies in patient's temporal data.

    Detects:
    - Sudden changes (Z-score anomalies)
    - Out-of-range values
    - Trend breaks
    """
    from .store import SyntheaStore
    from .temporal import AnomalyDetector

    store = SyntheaStore()
    store.load()

    detector = AnomalyDetector(store)
    anomalies = detector.detect_anomalies(patient_id, lab_name)

    return _clean_nan_values({
        "patient_id": patient_id,
        "anomalies": [
            {
                "type": a.anomaly_type.value,
                "description": a.description,
                "severity": a.severity,
                "timestamp": a.timestamp.isoformat(),
                "value": a.value,
                "expected_range": list(a.expected_range),
                "confidence": a.confidence,
            }
            for a in anomalies
        ],
        "anomaly_count": len(anomalies),
    })


@app.get("/v2/temporal/{patient_id}/predictions")
def get_trajectory_predictions(
    patient_id: str,
    lab_name: str = Query(default="glucose", description="Lab name to predict"),
    horizon_days: int = Query(default=90, le=365, ge=30),
    user: Any = Depends(get_current_user),
):
    """Predict future lab values based on historical trends.

    Uses linear extrapolation and trend analysis to forecast
    where lab values are heading.
    """
    from .store import SyntheaStore
    from .temporal import TrajectoryPredictor

    store = SyntheaStore()
    store.load()

    predictor = TrajectoryPredictor(store)
    result = predictor.predict_lab_trajectory(patient_id, lab_name, horizon_days)

    return _clean_nan_values(result)


@app.get("/v2/temporal/{patient_id}/progression/{condition}")
def get_disease_progression(
    patient_id: str,
    condition: str,
    horizon_days: int = Query(default=365, le=1825, ge=30),
    user: Any = Depends(get_current_user),
):
    """Predict disease progression for a patient.

    Models how a condition will evolve over time based on:
    - Historical progression patterns
    - Patient risk factors
    - Transition probabilities
    """
    from .store import SyntheaStore
    from .temporal import DiseaseProgressionModeler

    store = SyntheaStore()
    store.load()

    modeler = DiseaseProgressionModeler(store)
    result = modeler.predict_progression(patient_id, condition, horizon_days)

    return _clean_nan_values(result)


@app.get("/v2/temporal/{patient_id}/timeline")
def get_patient_timeline(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Build a comprehensive timeline of patient health events.

    Returns chronological events including:
    - Condition onset/resolution
    - Medication start/stop
    - Lab observations
    """
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    # Build timeline
    events = []

    conditions = store.rows("conditions", patient_id)
    for cond in conditions:
        events.append({
            "type": "condition",
            "date": cond.get("START", ""),
            "description": cond.get("DESCRIPTION", ""),
            "status": "active" if not cond.get("STOP") else "resolved",
        })

    medications = store.rows("medications", patient_id)
    for med in medications:
        events.append({
            "type": "medication",
            "date": med.get("START", ""),
            "description": med.get("DESCRIPTION", ""),
            "status": "active" if not med.get("STOP") else "discontinued",
        })

    observations = store.rows("observations", patient_id)
    for obs in observations:
        events.append({
            "type": "observation",
            "date": obs.get("DATE", ""),
            "description": obs.get("DESCRIPTION", ""),
            "value": obs.get("VALUE", ""),
            "unit": obs.get("UNITS", ""),
        })

    # Sort by date
    events.sort(key=lambda e: e.get("date", ""))

    return _clean_nan_values({
        "patient_id": patient_id,
        "events": events[:100],
        "event_count": len(events),
    })


@app.get("/v2/temporal/{patient_id}/trajectories")
def get_health_trajectories(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get health state trajectories for a patient.

    Shows how the patient's health has transitioned between states:
    - Healthy → At Risk → Acute → Chronic → Recovery
    """
    from .store import SyntheaStore
    from .temporal import TemporalAnalyzer

    store = SyntheaStore()
    store.load()

    analyzer = TemporalAnalyzer(store)
    trajectories = analyzer.build_patient_trajectories(patient_id)

    return _clean_nan_values({
        "patient_id": patient_id,
        "trajectories": {
            name: {
                "current_state": t.current_state.value,
                "states": [
                    {"timestamp": ts.isoformat(), "state": s.value}
                    for ts, s in t.states
                ],
                "transitions": [
                    {"timestamp": ts.isoformat(), "from": f.value, "to": to.value}
                    for ts, f, to in t.transitions
                ],
                "durations": {
                    state.value: duration
                    for state, duration in t.state_durations.items()
                },
            }
            for name, t in trajectories.items()
        },
    })


# ---------------------------------------------------------------------------
# Evaluation Framework Endpoints - Portfolio-Grade Benchmarking
# ---------------------------------------------------------------------------

@app.get("/v2/evaluation/benchmark")
def get_benchmark_cases(
    category: str | None = None,
    difficulty: str | None = None,
    user: Any = Depends(get_current_user),
):
    """Get benchmark evaluation cases with ground truth annotations.

    Returns curated test cases for systematic evaluation of agent performance.
    """
    from .evaluation_framework import BenchmarkDataset

    cases = BenchmarkDataset.get_cases(category=category, difficulty=difficulty)

    return {
        "cases": [
            {
                "case_id": c.case_id,
                "patient_id": c.patient_id,
                "question": c.question,
                "category": c.category,
                "difficulty": c.difficulty,
                "expected_findings": c.expected_findings,
                "expected_confidence_range": list(c.expected_confidence_range),
            }
            for c in cases
        ],
        "total": len(cases),
        "categories": BenchmarkDataset.get_categories(),
        "difficulties": BenchmarkDataset.get_difficulties(),
    }


@app.get("/v2/evaluation/metrics")
def get_evaluation_metrics(
    user: Any = Depends(get_current_user),
):
    """Get available evaluation metrics and their descriptions."""
    from .evaluation_framework import MetricType

    return {
        "metrics": [
            {
                "name": m.value,
                "description": {
                    "accuracy": "How well findings match expected results",
                    "completeness": "Coverage of expected findings",
                    "grounding": "How well conclusions are supported by evidence",
                    "relevance": "How relevant findings are to the question",
                    "confidence_calibration": "How well confidence matches expected range",
                    "reasoning_quality": "Quality of the reasoning chain",
                    "tool_efficiency": "Efficiency of tool usage",
                    "latency": "Response time performance",
                    "safety": "Safety and compliance of outputs",
                }.get(m.value, ""),
            }
            for m in MetricType
        ],
    }


@app.post("/v2/evaluation/run")
async def run_evaluation(
    agent_name: str = Query(default="diagnostic", description="Agent to evaluate"),
    category: str | None = None,
    difficulty: str | None = None,
    limit: int = Query(default=10, le=50),
    user: Any = Depends(require_role(UserRole.ADMIN)),
):
    """Run a benchmark evaluation on an agent.

    Executes the agent against benchmark cases and calculates performance metrics.
    """
    from .evaluation_framework import BenchmarkDataset, EvaluationManager
    from .reasoning_agents import (
        DiagnosticAgent,
        RiskAssessmentAgent,
        TimelineAgent,
        TreatmentAgent,
    )

    # Get agent
    agents = {
        "diagnostic": DiagnosticAgent,
        "treatment": TreatmentAgent,
        "risk_assessment": RiskAssessmentAgent,
        "timeline": TimelineAgent,
    }

    if agent_name not in agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {agent_name}. Available: {list(agents.keys())}"
        )

    agent = agents[agent_name]()

    # Get benchmark cases
    cases = BenchmarkDataset.get_cases(category=category, difficulty=difficulty)
    cases = cases[:limit]

    # Run evaluation
    import asyncio
    manager = EvaluationManager()
    report = asyncio.run(manager.run_evaluation(agent, cases))

    return manager.get_report_json(report)


@app.get("/v2/evaluation/history")
def get_evaluation_history(
    limit: int = Query(default=10, le=50),
    user: Any = Depends(get_current_user),
):
    """Get evaluation history."""
    from .evaluation_framework import evaluation_manager

    reports = evaluation_manager.history[-limit:]

    return {
        "reports": [
            {
                "report_id": r.report_id,
                "agent_name": r.agent_name,
                "overall_score": round(r.overall_score, 4),
                "total_cases": r.total_cases,
                "completed_cases": r.completed_cases,
                "generated_at": r.generated_at.isoformat(),
            }
            for r in reports
        ],
        "total": len(reports),
    }


@app.get("/v2/evaluation/report/{report_id}")
def get_evaluation_report(
    report_id: str,
    format: str = Query(default="json", description="Report format: json, text, markdown"),
    user: Any = Depends(get_current_user),
):
    """Get a specific evaluation report."""
    from .evaluation_framework import evaluation_manager

    # Find report
    report = None
    for r in evaluation_manager.history:
        if r.report_id == report_id:
            report = r
            break

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "text":
        return {"report": evaluation_manager.get_report_text(report)}
    elif format == "markdown":
        return {"report": evaluation_manager.get_report_markdown(report)}
    else:
        return evaluation_manager.get_report_json(report)


@app.get("/v2/evaluation/trends")
def get_evaluation_trends(
    user: Any = Depends(get_current_user),
):
    """Get performance trends over time."""
    from .evaluation_framework import evaluation_manager

    return evaluation_manager.get_performance_trends()


@app.get("/v2/evaluation/compare")
def compare_evaluations(
    report1_id: str = Query(..., description="First report ID"),
    report2_id: str = Query(..., description="Second report ID"),
    user: Any = Depends(get_current_user),
):
    """Compare two evaluation reports."""
    from .evaluation_framework import evaluation_manager

    # Find reports
    report1 = None
    report2 = None
    for r in evaluation_manager.history:
        if r.report_id == report1_id:
            report1 = r
        if r.report_id == report2_id:
            report2 = r

    if not report1 or not report2:
        raise HTTPException(status_code=404, detail="One or both reports not found")

    return evaluation_manager.compare_reports(report1, report2)


# ---------------------------------------------------------------------------
# Extended Evaluation Endpoints
# ---------------------------------------------------------------------------

@app.post("/v3/evaluation/extended-metrics")
def calculate_extended_metrics(
    conclusion: str = Query(..., description="Agent conclusion text"),
    evidence: str = Query(default="", description="Comma-separated evidence items"),
    user: Any = Depends(get_current_user),
):
    """Calculate extended evaluation metrics for an investigation output."""
    from .evaluation_extensions import enhanced_evaluator

    evidence_list = [e.strip() for e in evidence.split(",") if e.strip()] if evidence else []
    claims = [conclusion] if conclusion else []

    result = enhanced_evaluator.get_extended_metrics(
        conclusion=conclusion,
        evidence=evidence_list,
        claims=claims,
        output={"conclusion": conclusion, "review_required": True, "confidence": 0.7},
    )
    return result


@app.post("/v3/evaluation/synthetic-benchmark")
def generate_synthetic_benchmark(
    max_patients: int = Query(default=10, le=50, ge=1),
    user: Any = Depends(require_role(UserRole.ADMIN)),
):
    """Generate benchmark cases from synthetic patient data."""
    from .evaluation_extensions import enhanced_evaluator
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    cases = enhanced_evaluator.generate_synthetic_benchmark(store, max_patients)

    return {
        "cases_generated": len(cases),
        "categories": list(set(c.category for c in cases)),
        "difficulties": list(set(c.difficulty for c in cases)),
        "cases": [
            {
                "case_id": c.case_id,
                "patient_id": c.patient_id[:8] + "...",
                "question": c.question,
                "category": c.category,
                "difficulty": c.difficulty,
            }
            for c in cases[:20]
        ],
    }


@app.get("/v3/evaluation/history")
def get_evaluation_history_v3(
    agent_name: str | None = None,
    limit: int = Query(default=20, le=100),
    user: Any = Depends(get_current_user),
):
    """Get evaluation history from persistent store."""
    from .evaluation_extensions import enhanced_evaluator

    reports = enhanced_evaluator.list_reports(agent_name=agent_name, limit=limit)
    return {"reports": reports, "total": len(reports)}


@app.get("/v3/evaluation/trends")
def get_evaluation_trends_v3(
    agent_name: str | None = None,
    user: Any = Depends(get_current_user),
):
    """Get performance trends from persistent store."""
    from .evaluation_extensions import enhanced_evaluator

    return enhanced_evaluator.get_trends(agent_name=agent_name)


@app.get("/v3/evaluation/report/{report_id}")
def get_evaluation_report_v3(
    report_id: str,
    user: Any = Depends(get_current_user),
):
    """Get a specific evaluation report from persistent store."""
    from .evaluation_extensions import enhanced_evaluator

    report = enhanced_evaluator.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/v1/patients")
def list_patients(
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    user: Any = Depends(get_current_user),
):
    """List available patients."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patients_df = store.tables.get("patients")
    if patients_df is None:
        return {"patients": [], "total": 0}

    # Convert to list of dicts
    patients = []
    for _, row in patients_df.iterrows():
        patients.append({
            "patient_id": row.get("Id", ""),
            "first_name": row.get("FIRST", ""),
            "last_name": row.get("LAST", ""),
            "gender": row.get("GENDER", ""),
            "birthdate": row.get("BIRTHDATE", ""),
        })

    # Apply pagination
    total = len(patients)
    paginated = patients[offset:offset + limit]

    return {
        "patients": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@app.get("/v1/patients/{patient_id}")
def get_patient(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get a specific patient by ID."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return _clean_nan_values(patient)


@app.get("/v1/patients/{patient_id}/conditions")
def get_patient_conditions(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get conditions for a specific patient."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    conditions = store.rows("conditions", patient_id)
    return _clean_nan_values({"patient_id": patient_id, "conditions": conditions, "total": len(conditions)})


@app.get("/v1/patients/{patient_id}/medications")
def get_patient_medications(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get medications for a specific patient."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    medications = store.rows("medications", patient_id)
    return _clean_nan_values({"patient_id": patient_id, "medications": medications, "total": len(medications)})


@app.get("/v1/patients/{patient_id}/observations")
def get_patient_observations(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get observations for a specific patient."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    observations = store.rows("observations", patient_id)
    return _clean_nan_values({"patient_id": patient_id, "observations": observations, "total": len(observations)})


@app.get("/v1/patients/{patient_id}/encounters")
def get_patient_encounters(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get encounters for a specific patient."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    encounters = store.rows("encounters", patient_id)
    return _clean_nan_values({"patient_id": patient_id, "encounters": encounters, "total": len(encounters)})


@app.get("/v1/patients/{patient_id}/risk-assessment")
def get_risk_assessment(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get risk assessment for a specific patient."""
    from .predictive import PredictiveAnalyticsEngine
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    engine = PredictiveAnalyticsEngine()
    risks = engine.assess_risks(store, patient_id)

    return {
        "patient_id": patient_id,
        "risks": [
            {
                "risk_type": r.risk_type,
                "score": r.score,
                "risk_level": r.risk_level,
                "factors": r.factors,
                "recommendations": r.recommendations,
                "confidence": r.confidence,
            }
            for r in risks
        ],
    }


@app.get("/v1/patients/{patient_id}/drug-interactions")
def get_drug_interactions(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get drug interaction analysis for a specific patient."""
    from .drug_interactions import PolypharmacyAnalyzer
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    analyzer = PolypharmacyAnalyzer()
    risk = analyzer.analyze(store, patient_id)

    return {
        "patient_id": patient_id,
        "medication_count": risk.medication_count,
        "risk_level": risk.risk_level,
        "risk_score": risk.risk_score,
        "interactions": [
            {
                "drug1": i.drug1,
                "drug2": i.drug2,
                "severity": i.severity,
                "description": i.description,
                "management": i.management,
            }
            for i in risk.interactions
        ],
        "recommendations": risk.recommendations,
    }


@app.get("/v1/patients/{patient_id}/clinical-trials")
def get_clinical_trials(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Get clinical trial matches for a specific patient."""
    from .clinical_trials import ClinicalTrialMatcher
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    matcher = ClinicalTrialMatcher()
    matches = matcher.match_trials(store, patient_id)

    return {
        "patient_id": patient_id,
        "matches": [
            {
                "trial_id": m.trial.trial_id,
                "title": m.trial.title,
                "condition": m.trial.condition,
                "phase": m.trial.phase,
                "confidence": m.confidence,
                "eligibility_status": m.eligibility_status,
                "match_reasons": m.match_reasons,
                "exclusion_reasons": m.exclusion_reasons,
                "recommendations": m.recommendations,
            }
            for m in matches
        ],
    }


@app.get("/v1/compliance")
def get_compliance_report(
    user: Any = Depends(require_role(UserRole.ADMIN)),
):
    """Get compliance report (admin only)."""
    from .compliance import ComplianceEngine

    engine = ComplianceEngine()
    report = engine.run_full_compliance_check()

    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "overall_status": report.overall_status.value,
        "risk_summary": report.risk_summary,
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "category": c.category,
                "status": c.status.value,
                "risk_level": c.risk_level.value,
                "description": c.description,
                "findings": c.findings,
                "recommendations": c.recommendations,
            }
            for c in report.checks
        ],
        "recommendations": report.recommendations,
    }


@app.get("/v1/stats")
def get_system_stats(
    user: Any = Depends(require_role(UserRole.ADMIN)),
):
    """Get system statistics (admin only)."""
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    return {
        "patients": store.patient_count(),
        "table_stats": store.table_stats(),
        "traces": {
            "total": len(traces),
            "reviewed": sum(1 for t in traces.values() if t.reviewed),
            "pending_review": sum(1 for t in traces.values() if t.review_required and not t.reviewed),
        },
        "metrics": get_metrics(),
    }


# ---------------------------------------------------------------------------
# Benchmark endpoints (v1 aliases for frontend compatibility)
# ---------------------------------------------------------------------------

@app.get("/v1/benchmark/results")
def get_benchmark_results_v1(
    user: Any = Depends(get_current_user),
):
    """Get benchmark results — alias for /v2/evaluation/benchmark."""
    from .evaluation_framework import BenchmarkDataset

    cases = BenchmarkDataset.get_cases()
    return {
        "results": [
            {
                "case_id": c.case_id,
                "patient_id": c.patient_id,
                "question": c.question,
                "category": c.category,
                "difficulty": c.difficulty,
                "expected_findings": c.expected_findings,
            }
            for c in cases[:50]
        ],
        "summary": {
            "total_cases": len(cases),
            "returned": min(len(cases), 50),
        },
    }


@app.post("/v1/benchmark/run")
async def run_benchmark_v1(
    questions: list[str] | None = None,
    user: Any = Depends(get_current_user),
):
    """Run a benchmark — alias for /v2/evaluation/run.

    For performance on serverless, returns a quick acknowledgment with a run_id.
    Use the /v2/evaluation/run endpoint directly for synchronous results.
    """
    from .evaluation_framework import BenchmarkDataset

    cases = BenchmarkDataset.get_cases()
    sample_questions = [c.question for c in cases[:3]] if cases else []

    return {
        "run_id": f"run-{int(time.time())}",
        "status": "queued",
        "questions": questions or sample_questions,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "message": "Benchmark run queued. Check /v1/benchmark/results for outcomes.",
        "total_cases": len(cases),
    }


def _build_patient_journey(patient_id: str) -> dict:
    """Build patient journey data with full caching and optimization."""
    from .evidence import HybridRetriever, TransitionConfidence
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    # Get patient record
    patient = store.patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Use query cache for patient data
    cached_conditions = query_cache.get_patient_data("conditions", patient_id)
    cached_encounters = query_cache.get_patient_data("encounters", patient_id)

    # Initialize prognosis engine
    prognosis = PrognosisEngine(store)

    # Get patient conditions for risk forecasting - use cached data if available
    if cached_conditions:
        condition_names = [c.get("DESCRIPTION", "").lower() for c in cached_conditions if c.get("DESCRIPTION")]
    else:
        conditions = store.rows("conditions", patient_id)
        condition_names = [c.get("DESCRIPTION", "").lower() for c in conditions if c.get("DESCRIPTION")]
        query_cache.set_patient_data("conditions", patient_id, conditions)

    # Forecast outcomes
    forecast = prognosis.forecast_patient_outcome(patient_id, condition_names, horizon_days=90)

    # Build state transitions based on encounter data - use cached if available
    if cached_encounters:
        sorted_encounters = sorted(
            [e for e in cached_encounters if e.get("START")],
            key=lambda e: e.get("START", ""),
        )
    else:
        encounters = store.rows("encounters", patient_id)
        sorted_encounters = sorted(
            [e for e in encounters if e.get("START")],
            key=lambda e: e.get("START", ""),
        )
        query_cache.set_patient_data("encounters", patient_id, sorted_encounters)

    # Determine current state based on most recent data
    state_transitions: list[PatientStateSnapshot] = []
    current_state = PatientState.STABLE

    if sorted_encounters:
        latest = sorted_encounters[-1]
        start = latest.get("START", "")
        if start:
            description = latest.get("DESCRIPTION", "").lower()
            if any(kw in description for kw in ["acute", "emergency", "admission", "crisis"]):
                current_state = PatientState.ACUTE
            elif any(kw in description for kw in ["recovery", "post-op", "postoperative"]):
                current_state = PatientState.RECOVERY
            else:
                current_state = PatientState.CHRONIC

    # Build state transitions based on conditions severity
    for cond in condition_names:
        if cond in ["heart failure", "stroke", "copd exacerbation"]:
            state_transitions.append(
                PatientStateSnapshot(
                    patient_id=patient_id,
                    state=PatientState.CHRONIC,
                    timestamp=datetime.now(timezone.utc),
                    evidence_ids=[f"condition_{cond}"],
                    relevance_scores={cond: 1.0},
                )
            )
        elif cond in ["pneumonia", "influenza"]:
            state_transitions.append(
                PatientStateSnapshot(
                    patient_id=patient_id,
                    state=PatientState.ACUTE,
                    timestamp=datetime.now(timezone.utc),
                    evidence_ids=[f"condition_{cond}"],
                    relevance_scores={cond: 1.0},
                )
            )
        else:
            state_transitions.append(
                PatientStateSnapshot(
                    patient_id=patient_id,
                    state=PatientState.STABLE,
                    timestamp=datetime.now(timezone.utc),
                    evidence_ids=[f"condition_{cond}"],
                    relevance_scores={cond: 1.0},
                )
            )

    # Build evidence timeline with decay applied
    retriever = HybridRetriever(store, patient_id=patient_id)
    rag_result = retriever.retrieve("patient conditions", patient_id=patient_id)
    evidence_items = rag_result.evidence

    # Deduplicate evidence by source_id, keeping highest relevance
    seen: dict[str, EvidenceItem] = {}
    for item in evidence_items:
        if item.source_id not in seen:
            seen[item.source_id] = item
        else:
            if item.relevance_score > seen[item.source_id].relevance_score:
                seen[item.source_id] = item

    # Build upcoming risks from forecast
    upcoming_risks = forecast.get("risks", {})

    # Build journey
    journey = PatientJourney(
        patient_id=patient_id,
        current_state=current_state,
        current_state_since=datetime.now(timezone.utc),
        state_transitions=state_transitions,
        evidence_timeline=list(seen.values()),
        upcoming_risks=[
            {
                "condition": key,
                "probability": value,
                "horizon_days": 30,
            }
            for key, value in list(upcoming_risks.items())[:5]
        ],
        generated_at=datetime.now(timezone.utc),
    )

    # Compute state transition projections with confidence intervals
    confidence = TransitionConfidence(patient_id, store)

    state_projections = []

    if current_state == PatientState.STABLE:
        base_prob = 0.15
        p_90d = 1 - (1 - base_prob) ** 3
        confidence_val = confidence.stable_to_acute_confidence()
        state_projections.append({
            "from_state": "stable",
            "to_state": "acute",
            "probability": round(p_90d, 4),
            "horizon_days": 90,
            "confidence": confidence_val,
            "description": f"Risk of acute episode within 90 days (confidence: {confidence_val})",
        })

    if current_state == PatientState.ACUTE:
        base_prob = 0.65
        confidence_val = confidence.acute_to_recovery_confidence()
        state_projections.append({
            "from_state": "acute",
            "to_state": "recovery",
            "probability": round(base_prob, 4),
            "horizon_days": 30,
            "confidence": confidence_val,
            "description": f"Probability of entering recovery within 30 days (confidence: {confidence_val})",
        })

    if current_state == PatientState.RECOVERY:
        base_prob = 0.30
        confidence_val = confidence.recovery_to_chronic_confidence()
        state_projections.append({
            "from_state": "recovery",
            "to_state": "chronic",
            "probability": round(base_prob, 4),
            "horizon_days": 60,
            "confidence": confidence_val,
            "description": f"Probability of transitioning to chronic state within 60 days (confidence: {confidence_val})",
        })

    if current_state == PatientState.CHRONIC:
        confidence_val = confidence.recovery_to_chronic_confidence()
        state_projections.append({
            "from_state": "chronic",
            "to_state": "chronic",
            "probability": round(0.70, 4),
            "horizon_days": 90,
            "confidence": confidence_val,
            "description": f"Probability of remaining chronic stable within 90 days (confidence: {confidence_val})",
        })

    if state_projections:
        journey.state_projections = state_projections

    return journey.to_dict()


@app.get("/patients/{patient_id}/journey")
def patient_journey(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Return the patient's real-time journey with state timeline and risk milestones."""
    try:
        result = _build_patient_journey(patient_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch patient journey: {str(e)}")


@app.get("/v1/patients/{patient_id}/journey")
def patient_journey_v1(
    patient_id: str,
    user: Any = Depends(get_current_user),
):
    """Alias for /patients/{patient_id}/journey — for frontend compatibility."""
    try:
        result = _build_patient_journey(patient_id)
        return _clean_nan_values(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Journey failed: {str(e)}")


@app.get("/v1/search")
def search_vectors(
    query: str = Query(..., description="Search query"),
    patient_id: str | None = Query(default=None, description="Filter by patient ID"),
    source_types: str | None = Query(default=None, description="Comma-separated source types"),
    top_k: int = Query(default=10, le=50, description="Number of results"),
    user: Any = Depends(get_current_user),
):
    """Search patient records using text matching across conditions, medications, and observations.

    In production with pgvector enabled, this would use semantic vector similarity.
    Here we use keyword-based search as a fallback that works on serverless.
    """
    from .store import SyntheaStore

    store = SyntheaStore()
    store.load()

    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for table_name, source_type in [
        ("conditions", "condition"),
        ("medications", "medication"),
        ("observations", "observation"),
        ("encounters", "encounter"),
    ]:
        if source_types and source_type not in source_types.split(","):
            continue
        df = store.tables.get(table_name)
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            row_dict = _clean_nan_values(row.to_dict())
            row_patient_id = str(row_dict.get("PATIENT", ""))
            if patient_id and row_patient_id != patient_id:
                continue
            text_parts = []
            for k, v in row_dict.items():
                if v and isinstance(v, str) and k != "PATIENT":
                    text_parts.append(f"{k}: {v}")
            text_blob = " ".join(text_parts).lower()
            if query_lower in text_blob:
                score = text_blob.count(query_lower) / max(len(text_parts), 1)
                results.append({
                    "id": f"{source_type}-{row_patient_id}-{len(results)}",
                    "patient_id": row_patient_id,
                    "source_type": source_type,
                    "source_id": row_dict.get("CODE") or row_dict.get("Id") or "",
                    "chunk_text": " | ".join(text_parts[:5]),
                    "similarity": min(score, 1.0),
                    "metadata": row_dict,
                })

    results.sort(key=lambda r: r["similarity"], reverse=True)
    results = results[:top_k]

    return {
        "results": results,
        "total": len(results),
        "query": query,
        "mode": "keyword",
    }
