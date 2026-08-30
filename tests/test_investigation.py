import os

from fastapi.testclient import TestClient

# Disable auth and rate limiting for testing
os.environ["AEGIS_AUTH_DISABLED"] = "true"
os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"

from aegis.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_investigation_with_demo_patient():
    response = client.post("/v1/investigations", json={
        "patient_id": "demo-001",
        "question": "Summarize this patient's health record"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "demo-001"
    assert data["question"] == "Summarize this patient's health record"
    assert "conclusion" in data
    assert "evidence" in data
    assert "confidence" in data
    assert "review_required" in data
    assert data["review_required"] is True
    assert "trace_id" in data
    assert "generated_at" in data
    assert len(data["agent_results"]) == 4
    for result in data["agent_results"]:
        assert result["status"] == "completed"


def test_investigation_with_real_patient():
    from aegis.store import SyntheaStore
    store = SyntheaStore("data/synthea")
    store.load()

    # Find a patient with both conditions and medications
    patients = store.tables["patients"]
    target_patient = None
    for _, row in patients.iterrows():
        pid = row["Id"]
        conds = store.rows("conditions", pid)
        meds = store.rows("medications", pid)
        if len(conds) > 0 and len(meds) > 0:
            target_patient = pid
            break

    assert target_patient is not None, "No patient with conditions and medications found"

    response = client.post("/v1/investigations", json={
        "patient_id": target_patient,
        "question": "Summarize this patient's health record and medication history"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == target_patient
    assert len(data["agent_results"]) == 4
    # With real data, agents should find records and report non-zero confidence
    timeline = next(r for r in data["agent_results"] if r["agent"] == "timeline")
    medication = next(r for r in data["agent_results"] if r["agent"] == "medication")
    assert len(timeline["evidence"]) > 0, "Timeline should have evidence"
    assert len(medication["evidence"]) > 0, "Medication agent should have evidence"
    assert data["review_required"] is True


def test_investigation_missing_patient():
    response = client.post("/v1/investigations", json={
        "patient_id": "nonexistent-patient",
        "question": "What conditions does this patient have?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["review_required"] is True


def test_benchmark_structure():
    """Verify benchmark JSONL is well-formed and patient IDs exist in dataset."""
    import json

    from aegis.store import SyntheaStore

    store = SyntheaStore("data/synthea")
    store.load()
    valid_patients = set(store.tables["patients"]["Id"].astype(str))

    with open("benchmark.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            pid = record["patient_id"]
            assert pid in valid_patients, \
                f"Benchmark patient {pid} not found in dataset"


def test_hitl_review_approval():
    """Test HITL review approval flow."""
    # Run an investigation
    response = client.post("/v1/investigations", json={
        "patient_id": "demo-001",
        "question": "Summarize health"
    })
    assert response.status_code == 200
    trace_id = response.json()["trace_id"]
    assert response.json()["review_required"] is True

    # Approve the investigation
    review_response = client.post(f"/v1/traces/{trace_id}/review", json={
        "decision": "approved",
        "reviewer_id": "dr-smith",
        "notes": "Looks good, no concerning findings."
    })
    assert review_response.status_code == 200
    data = review_response.json()
    assert data["reviewed"] is True
    assert data["review_decision"] == "approved"
    assert data["reviewer_id"] == "dr-smith"
    assert data["review_required"] is False


def test_hitl_review_rejection():
    """Test HITL review rejection flow."""
    # Run an investigation
    response = client.post("/v1/investigations", json={
        "patient_id": "demo-001",
        "question": "Summarize health"
    })
    assert response.status_code == 200
    trace_id = response.json()["trace_id"]

    # Reject the investigation
    review_response = client.post(f"/v1/traces/{trace_id}/review", json={
        "decision": "rejected",
        "reviewer_id": "dr-jones",
        "notes": "Insufficient evidence for conclusion."
    })
    assert review_response.status_code == 200
    data = review_response.json()
    assert data["reviewed"] is True
    assert data["review_decision"] == "rejected"
    assert data["reviewer_id"] == "dr-jones"
    assert data["review_required"] is True  # Still requires review since rejected


def test_list_traces():
    """Test listing traces with filtering."""
    # Run a couple investigations
    client.post("/v1/investigations", json={
        "patient_id": "demo-001",
        "question": "Summarize health"
    })
    client.post("/v1/investigations", json={
        "patient_id": "demo-001",
        "question": "List conditions"
    })

    # List all traces
    response = client.get("/v1/traces")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["meta"]["total"] >= 2
    assert len(data["data"]) >= 2

    # List traces filtered by patient_id
    response = client.get("/v1/traces?patient_id=demo-001")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert all(t["patient_id"] == "demo-001" for t in data["data"])


def test_list_patients():
    """Test listing patients endpoint."""
    response = client.get("/v1/patients")
    assert response.status_code == 200
    data = response.json()
    assert "patients" in data
    assert "total" in data
    assert data["total"] > 0


def test_get_patient():
    """Test getting a specific patient."""
    # First get a patient ID
    response = client.get("/v1/patients?limit=1")
    assert response.status_code == 200
    patient_id = response.json()["patients"][0]["patient_id"]

    # Get patient details
    response = client.get(f"/v1/patients/{patient_id}")
    assert response.status_code == 200
    data = response.json()
    assert "Id" in data or "FIRST" in data


def test_get_patient_conditions():
    """Test getting patient conditions."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/conditions")
    assert response.status_code == 200
    data = response.json()
    assert "conditions" in data
    assert "total" in data


def test_get_patient_medications():
    """Test getting patient medications."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/medications")
    assert response.status_code == 200
    data = response.json()
    assert "medications" in data
    assert "total" in data


def test_get_patient_observations():
    """Test getting patient observations."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/observations")
    assert response.status_code == 200
    data = response.json()
    assert "observations" in data
    assert "total" in data


def test_get_patient_encounters():
    """Test getting patient encounters."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/encounters")
    assert response.status_code == 200
    data = response.json()
    assert "encounters" in data
    assert "total" in data


def test_get_patient_journey():
    """Test getting patient journey."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/patients/{patient_id}/journey")
    assert response.status_code == 200
    data = response.json()
    assert "patient_id" in data
    assert "current_state" in data


def test_get_risk_assessment():
    """Test getting patient risk assessment."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/risk-assessment")
    assert response.status_code == 200
    data = response.json()
    assert "risks" in data


def test_get_drug_interactions():
    """Test getting drug interactions."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/drug-interactions")
    assert response.status_code == 200
    data = response.json()
    assert "medication_count" in data
    assert "risk_level" in data


def test_get_clinical_trials():
    """Test getting clinical trial matches."""
    response = client.get("/v1/patients?limit=1")
    patient_id = response.json()["patients"][0]["patient_id"]

    response = client.get(f"/v1/patients/{patient_id}/clinical-trials")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data


def test_pagination():
    """Test pagination parameters."""
    response = client.get("/v1/patients?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["patients"]) <= 5
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert "has_more" in data


def test_metrics():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data
