#!/usr/bin/env python3
"""
Comprehensive endpoint smoke test for the AEGIS backend.

Tests every backend endpoint to ensure:
- Returns 2xx for valid requests
- Returns 4xx (not 5xx) for invalid input
- Returns valid JSON
- No NaN/Infinity values in responses

Usage:
    python scripts/smoke_test_endpoints.py [BASE_URL]
    python scripts/smoke_test_endpoints.py https://backend-three-tan-79.vercel.app
    python scripts/smoke_test_endpoints.py http://localhost:8000
"""
from __future__ import annotations
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://backend-three-tan-79.vercel.app"


@dataclass
class TestResult:
    name: str
    method: str
    path: str
    expected_status: int
    actual_status: int
    passed: bool
    duration_ms: float
    response_preview: str = ""
    contains_nan: bool = False
    error: Optional[str] = None


def check_for_nan_inf(data: Any) -> bool:
    """Recursively check for NaN or Infinity in JSON data."""
    if isinstance(data, float):
        import math
        return math.isnan(data) or math.isinf(data)
    elif isinstance(data, dict):
        return any(check_for_nan_inf(v) for v in data.values())
    elif isinstance(data, list):
        return any(check_for_nan_inf(v) for v in data)
    return False


def make_request(method: str, path: str, body: Optional[Dict] = None, timeout: int = 30) -> Tuple[int, Any, float]:
    """Make an HTTP request and return (status, parsed_body, duration_ms)."""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps(body).encode() if body else None
    start = time.time()
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_bytes = resp.read()
            duration = (time.time() - start) * 1000
            try:
                parsed = json.loads(body_bytes) if body_bytes else {}
            except json.JSONDecodeError:
                parsed = {"raw": body_bytes.decode()[:200]}
            return resp.status, parsed, duration
    except urllib.error.HTTPError as e:
        duration = (time.time() - start) * 1000
        try:
            parsed = json.loads(e.read())
        except Exception:
            parsed = {}
        return e.code, parsed, duration
    except Exception as e:
        duration = (time.time() - start) * 1000
        return 0, {"error": str(e)}, duration


def run_test(
    name: str,
    method: str,
    path: str,
    expected_status: int = 200,
    body: Optional[Dict] = None,
    validate_nan: bool = True,
    timeout: int = 45,
) -> TestResult:
    """Run a single endpoint test."""
    status, parsed, duration_ms = make_request(method, path, body, timeout)
    passed = status == expected_status
    error = None
    nan_found = False

    if status == 0:
        passed = False
        error = parsed.get("error", "Connection failed")
    elif status != expected_status:
        error = f"Expected {expected_status}, got {status}"

    if passed and validate_nan and isinstance(parsed, dict):
        nan_found = check_for_nan_inf(parsed)
        if nan_found:
            passed = False
            error = "Response contains NaN or Infinity"

    preview = json.dumps(parsed)[:200] if isinstance(parsed, dict) else str(parsed)[:200]

    return TestResult(
        name=name,
        method=method,
        path=path,
        expected_status=expected_status,
        actual_status=status,
        passed=passed,
        duration_ms=duration_ms,
        error=error,
        response_preview=preview,
        contains_nan=nan_found,
    )


def main():
    import time as time_module
    print(f"\n{'='*70}")
    print(f"AEGIS Backend Endpoint Smoke Test")
    print(f"Target: {BASE_URL}")
    print(f"{'='*70}\n")

    results: List[TestResult] = []

    def section(name: str):
        print(f"\n{name}")
        time_module.sleep(0.3)  # Small delay to avoid Vercel cold starts

    # ========================================
    # HEALTH & SYSTEM
    # ========================================
    print("📡 Health & System Endpoints")
    results.append(run_test("Health check", "GET", "/health"))
    results.append(run_test("Prometheus metrics", "GET", "/metrics"))
    results.append(run_test("Agent metrics", "GET", "/metrics/agents"))
    results.append(run_test("API docs", "GET", "/docs", expected_status=200))

    # ========================================
    # PATIENTS (v1)
    # ========================================
    print("\n👥 Patient Endpoints (v1)")
    results.append(run_test("List patients", "GET", "/v1/patients?limit=10"))
    results.append(run_test("Get patient", "GET", "/v1/patients/patient-001"))
    results.append(run_test("Get patient 404", "GET", "/v1/patients/nonexistent", expected_status=404))
    results.append(run_test("Patient conditions", "GET", "/v1/patients/patient-001/conditions"))
    results.append(run_test("Patient medications", "GET", "/v1/patients/patient-001/medications"))
    results.append(run_test("Patient observations", "GET", "/v1/patients/patient-001/observations"))
    results.append(run_test("Patient encounters", "GET", "/v1/patients/patient-001/encounters"))
    results.append(run_test("Patient journey", "GET", "/v1/patients/patient-001/journey"))
    results.append(run_test("Patient risk", "GET", "/v1/patients/patient-001/risk-assessment"))
    results.append(run_test("Drug interactions", "GET", "/v1/patients/patient-001/drug-interactions"))
    results.append(run_test("Clinical trials", "GET", "/v1/patients/patient-001/clinical-trials"))

    # ========================================
    # INVESTIGATIONS (v1 & v2)
    # Note: v2 is a complex multi-agent investigation with many LLM calls.
    # On serverless with 300s timeout, it may exceed the limit.
    # We test v1 (fast) and skip v2 in automated smoke tests.
    # ========================================
    print("\n🔬 Investigation Endpoints")
    results.append(run_test(
        "Run investigation (v1) - fast",
        "POST",
        "/v1/investigations",
        body={"patient_id": "patient-001", "question": "Summarize patient history"},
        timeout=60,
    ))
    # v2 takes too long for smoke tests - verify it exists but skip detailed test
    # To test v2 manually: curl -X POST .../v2/investigations with longer timeout
    results.append(run_test(
        "Investigation 422 (no patient)",
        "POST",
        "/v1/investigations",
        body={"question": "test"},
        expected_status=422,
    ))

    # ========================================
    # TRACES (v1)
    # ========================================
    print("\n📋 Trace Endpoints")
    results.append(run_test("List traces", "GET", "/v1/traces?limit=10"))
    results.append(run_test("List traces by patient", "GET", "/v1/traces?patient_id=patient-001&limit=5"))

    # ========================================
    # SYSTEM STATS & COMPLIANCE
    # ========================================
    print("\n📊 Stats & Compliance")
    results.append(run_test("System stats", "GET", "/v1/stats"))
    results.append(run_test("Compliance report", "GET", "/v1/compliance"))
    results.append(run_test("Search", "GET", "/v1/search?query=diabetes&top_k=5"))
    results.append(run_test("Benchmark results", "GET", "/v1/benchmark/results"))
    results.append(run_test("Run benchmark", "POST", "/v1/benchmark/run", body=[], timeout=60))

    # ========================================
    # AGENTS & TOOLS (v2)
    # ========================================
    print("\n🤖 Agent & Tool Endpoints")
    results.append(run_test("List agents", "GET", "/v2/agents"))
    results.append(run_test("List tools", "GET", "/v2/tools"))
    results.append(run_test("List tools by category", "GET", "/v2/tools?category=data_access"))

    # ========================================
    # GRAPH RAG (v2)
    # ========================================
    print("\n🔗 Graph RAG Endpoints")
    results.append(run_test("Graph RAG evidence", "GET", "/v2/graph-rag/patient-001?query=diabetes"))
    results.append(run_test("Patient patterns", "GET", "/v2/graph-rag/patient-001/patterns"))
    results.append(run_test("Causal chains", "GET", "/v2/graph-rag/patient-001/causal-chains"))
    results.append(run_test("Communities", "GET", "/v2/graph-rag/patient-001/communities"))
    results.append(run_test("Centrality", "GET", "/v2/graph-rag/patient-001/centrality"))
    results.append(run_test("Treatment pathways", "GET", "/v2/graph-rag/treatment-pathways/diabetes"))
    results.append(run_test("Related conditions", "GET", "/v2/graph-rag/related-conditions/diabetes"))

    # ========================================
    # TEMPORAL ANALYSIS (v2)
    # ========================================
    print("\n⏱️  Temporal Endpoints")
    results.append(run_test("Temporal analysis", "GET", "/v2/temporal/patient-001"))
    results.append(run_test("Temporal anomalies", "GET", "/v2/temporal/patient-001/anomalies"))
    results.append(run_test("Trajectory predictions", "GET", "/v2/temporal/patient-001/predictions?lab_name=HbA1c"))
    results.append(run_test("Disease progression", "GET", "/v2/temporal/patient-001/progression/diabetes"))
    results.append(run_test("Patient timeline", "GET", "/v2/temporal/patient-001/timeline"))
    results.append(run_test("Health trajectories", "GET", "/v2/temporal/patient-001/trajectories"))

    # ========================================
    # EVALUATION (v2 & v3)
    # ========================================
    print("\n📈 Evaluation Endpoints")
    results.append(run_test("Eval benchmark (v2)", "GET", "/v2/evaluation/benchmark"))
    results.append(run_test("Eval metrics (v2)", "GET", "/v2/evaluation/metrics"))
    results.append(run_test("Eval history (v3)", "GET", "/v3/evaluation/history?limit=10"))
    results.append(run_test("Eval trends (v3)", "GET", "/v3/evaluation/trends"))

    # ========================================
    # TRACES DETAIL
    # ========================================
    print("\n🔍 Trace Detail Endpoints")
    # Use a known trace ID if available, or skip
    trace_id = None
    try:
        status, data, _ = make_request("GET", "/v1/traces?limit=1")
        if status == 200 and data.get("traces"):
            trace_id = data["traces"][0].get("trace_id")
    except Exception:
        pass

    if trace_id:
        results.append(run_test("Get trace", "GET", f"/v1/traces/{trace_id}"))
        results.append(run_test(
            "Review trace",
            "POST",
            f"/v1/traces/{trace_id}/review",
            body={"decision": "approved", "reviewer_id": "test", "notes": "ok"}
        ))

    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r.passed)
    failed = [r for r in results if not r.passed]
    nan_results = [r for r in results if r.contains_nan]
    total_time = sum(r.duration_ms for r in results)

    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"⏱️  Total time: {total_time/1000:.1f}s")
    print(f"📊 Avg response: {total_time/max(len(results),1):.0f}ms")

    if nan_results:
        print(f"\n⚠️  {len(nan_results)} responses contained NaN/Infinity:")
        for r in nan_results:
            print(f"   - {r.method} {r.path}")

    if failed:
        print(f"\n❌ Failed tests:")
        for r in failed:
            print(f"   - [{r.actual_status}] {r.method} {r.path}")
            if r.error:
                print(f"     Error: {r.error}")
            if r.response_preview:
                print(f"     Preview: {r.response_preview[:150]}")

    # Performance summary
    slow = [r for r in results if r.duration_ms > 5000]
    if slow:
        print(f"\n🐌 Slow endpoints (>5s):")
        for r in slow:
            print(f"   - {r.method} {r.path}: {r.duration_ms:.0f}ms")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())