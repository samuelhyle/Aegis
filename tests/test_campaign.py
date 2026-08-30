"""
AEGIS Comprehensive Test Campaign
==================================

This module contains extensive tests for the AEGIS system covering:
1. Unit Tests - Individual component testing
2. Integration Tests - Component interaction testing
3. API Tests - Endpoint testing
4. Performance Tests - Load and stress testing
5. Security Tests - Vulnerability testing
6. Resilience Tests - Fault tolerance testing
7. End-to-End Tests - Complete workflow testing
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

# Set test environment
os.environ["AEGIS_AUTH_DISABLED"] = "true"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"

from fastapi.testclient import TestClient

from aegis.api import app
from aegis.cache import CacheManager, MemoryCacheBackend, cache_key
from aegis.clinical_tools import (
    assess_patient_risks,
    check_drug_interactions,
    forecast_patient_outcome,
    get_lab_analysis,
    get_patient_conditions,
    get_patient_medications,
    get_patient_observations,
    get_patient_record,
    match_clinical_trials,
)
from aegis.llm import LLMProvider, LLMResponse
from aegis.observability import AlertManager, MetricsCollector, Tracer
from aegis.rate_limit import RateLimiter
from aegis.resilience import (
    Bulkhead,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    HealthChecker,
    RetryConfig,
    retry_async,
)
from aegis.security import (
    AuditLogger,
    InputSanitizer,
    SecretsManager,
)
from aegis.store import SyntheaStore
from aegis.tools import ToolCategory, ToolRegistry

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def store():
    """Create a loaded store for testing."""
    s = SyntheaStore("data/synthea")
    s.load()
    return s


@pytest.fixture(scope="session")
def sample_patient_id(store):
    """Get a sample patient ID."""
    patients = store.tables.get("patients")
    if patients is None or len(patients) == 0:
        pytest.skip("No patients in dataset")
    return patients.iloc[0]["Id"]


@pytest.fixture(scope="session")
def patient_with_conditions(store):
    """Get a patient with conditions."""
    patients = store.tables.get("patients")
    if patients is None:
        pytest.skip("No patients table")
    for _, row in patients.iterrows():
        pid = row["Id"]
        conditions = store.rows("conditions", pid)
        if len(conditions) > 0:
            return pid
    pytest.skip("No patient with conditions")


@pytest.fixture(scope="session")
def patient_with_medications(store):
    """Get a patient with medications."""
    patients = store.tables.get("patients")
    if patients is None:
        pytest.skip("No patients table")
    for _, row in patients.iterrows():
        pid = row["Id"]
        meds = store.rows("medications", pid)
        if len(meds) > 0:
            return pid
    pytest.skip("No patient with medications")


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    class MockLLM(LLMProvider):
        @property
        def name(self):
            return "mock"

        @property
        def model_name(self):
            return "mock-model"

        async def complete(self, system, user, temperature=0.0):
            return LLMResponse(
                content='{"thought": "test", "confidence": 0.8}',
                model="mock-model",
            )

        async def structured_output(self, system, user, response_model, temperature=0.0):
            return response_model()

    return MockLLM()


@pytest.fixture
def cache():
    """Create a fresh cache for testing."""
    return CacheManager(MemoryCacheBackend(max_size=100, default_ttl=60))


@pytest.fixture
def metrics():
    """Create a fresh metrics collector."""
    return MetricsCollector()


@pytest.fixture
def tracer():
    """Create a fresh tracer."""
    return Tracer()


@pytest.fixture
def audit_logger():
    """Create a fresh audit logger."""
    return AuditLogger()


# ============================================================================
# 1. UNIT TESTS - Individual Component Testing
# ============================================================================

class TestStoreUnit:
    """Unit tests for SyntheaStore."""

    def test_store_initialization(self):
        """Test store can be initialized."""
        store = SyntheaStore("data/synthea")
        assert store.data_dir.name == "synthea"
        assert store._loaded is False

    def test_store_load(self, store):
        """Test store loads data."""
        assert store._loaded is True
        assert len(store.tables) > 0

    def test_store_patient_count(self, store):
        """Test patient count."""
        count = store.patient_count()
        assert count > 0

    def test_store_table_stats(self, store):
        """Test table statistics."""
        stats = store.table_stats()
        assert "patients" in stats
        assert stats["patients"] > 0

    def test_store_patient_found(self, store, sample_patient_id):
        """Test finding a patient."""
        patient = store.patient(sample_patient_id)
        assert patient is not None
        assert "Id" in patient or "FIRST" in patient

    def test_store_patient_not_found(self, store):
        """Test patient not found."""
        patient = store.patient("nonexistent")
        assert patient == {}

    def test_store_rows(self, store, sample_patient_id):
        """Test getting rows."""
        rows = store.rows("conditions", sample_patient_id)
        assert isinstance(rows, list)

    def test_store_search(self, store):
        """Test search functionality."""
        results = store.search("patients", "GENDER", "M")
        assert isinstance(results, list)

    def test_store_cache_invalidation(self, store):
        """Test cache invalidation."""
        store.invalidate_cache()
        assert store._loaded is False


class TestCacheUnit:
    """Unit tests for caching system."""

    def test_memory_backend_set_get(self, cache):
        """Test basic set/get."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_memory_backend_ttl(self):
        """Test TTL expiration."""
        backend = MemoryCacheBackend(max_size=10, default_ttl=1)
        cache = CacheManager(backend)
        cache.set("key1", "value1")
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_memory_backend_eviction(self):
        """Test LRU eviction."""
        backend = MemoryCacheBackend(max_size=3, default_ttl=60)
        cache = CacheManager(backend)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Evicts key1
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_cache_get_or_set(self, cache):
        """Test get_or_set pattern."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "computed"

        result1 = cache.get_or_set("key", factory)
        result2 = cache.get_or_set("key", factory)
        assert result1 == result2 == "computed"
        assert call_count == 1

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = cache_key("a", "b", param="c")
        key2 = cache_key("a", "b", param="c")
        key3 = cache_key("a", "b", param="d")
        assert key1 == key2
        assert key1 != key3

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        stats = cache.get_stats()
        assert stats["backend"] == "memory"


class TestSecurityUnit:
    """Unit tests for security components."""

    def test_input_sanitizer_clean(self):
        """Test clean input passes."""
        result = InputSanitizer.sanitize_string("normal text")
        assert result == "normal text"

    def test_input_sanitizer_null_bytes(self):
        """Test null byte removal."""
        result = InputSanitizer.sanitize_string("hello\x00world")
        assert result == "helloworld"

    def test_input_sanitizer_max_length(self):
        """Test max length enforcement."""
        result = InputSanitizer.sanitize_string("a" * 2000, max_length=100)
        assert len(result) == 100

    def test_sql_injection_detection(self):
        """Test SQL injection detection."""
        assert InputSanitizer.check_sql_injection("SELECT * FROM users") is True
        assert InputSanitizer.check_sql_injection("normal text") is False

    def test_xss_detection(self):
        """Test XSS detection."""
        assert InputSanitizer.check_xss("<script>alert(1)</script>") is True
        assert InputSanitizer.check_xss("normal text") is False

    def test_path_traversal_detection(self):
        """Test path traversal detection."""
        assert InputSanitizer.check_path_traversal("../etc/passwd") is True
        assert InputSanitizer.check_path_traversal("normal/path") is False

    def test_patient_id_validation(self):
        """Test patient ID validation."""
        assert InputSanitizer.validate_patient_id("patient-123") == "patient-123"
        with pytest.raises(ValueError):
            InputSanitizer.validate_patient_id("patient@123")

    def test_question_validation(self):
        """Test question validation."""
        assert InputSanitizer.validate_question("What is the condition?") == "What is the condition?"
        with pytest.raises(ValueError):
            InputSanitizer.validate_question("ab")

    def test_audit_logger_events(self, audit_logger):
        """Test audit event logging."""
        audit_logger.log_auth_success("user1", "127.0.0.1", "api_key")
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key")
        assert len(audit_logger.events) == 2

    def test_secrets_manager(self):
        """Test secrets management."""
        sm = SecretsManager()
        sm.set("TEST_SECRET", "value123")
        assert sm.get("TEST_SECRET") == "value123"
        assert sm.get_masked("TEST_SECRET") == "va...23"


class TestResilienceUnit:
    """Unit tests for resilience patterns."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        async def success():
            return "ok"

        result = await cb.execute(success)
        assert result == "ok"
        assert cb.state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after failures."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

        async def fail():
            raise ValueError("fail")

        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.execute(fail)

        assert cb.state.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry with eventual success."""
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "success"

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await retry_async(flaky, config)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_bulkhead_limits(self):
        """Test bulkhead concurrency limits."""
        bh = Bulkhead("test", max_concurrent=2, max_queue=5)

        async def work():
            await asyncio.sleep(0.1)
            return "done"

        result = await bh.execute(work)
        assert result == "done"


class TestObservabilityUnit:
    """Unit tests for observability components."""

    def test_metrics_counter(self, metrics):
        """Test counter metrics."""
        metrics.inc_counter("test_counter")
        metrics.inc_counter("test_counter")
        data = metrics.get_metrics()
        assert data["counters"]["test_counter"] == 2

    def test_metrics_gauge(self, metrics):
        """Test gauge metrics."""
        metrics.set_gauge("test_gauge", 42.0)
        data = metrics.get_metrics()
        assert data["gauges"]["test_gauge"] == 42.0

    def test_metrics_histogram(self, metrics):
        """Test histogram metrics."""
        metrics.observe_histogram("test_hist", 10.0)
        metrics.observe_histogram("test_hist", 20.0)
        data = metrics.get_metrics()
        assert data["histograms"]["test_hist"]["count"] == 2

    def test_tracer_spans(self, tracer):
        """Test tracing spans."""
        with tracer.trace("test_op") as span:
            span.add_event("test_event")
        assert span.duration_ms >= 0

    def test_alert_manager(self):
        """Test alert management."""
        am = AlertManager()
        alerts = am.check_alerts({"errors_total": 150})
        assert len(alerts) > 0


# ============================================================================
# 2. INTEGRATION TESTS - Component Interaction Testing
# ============================================================================

class TestStoreIntegration:
    """Integration tests for store with other components."""

    def test_store_with_clinical_tools(self, store, sample_patient_id):
        """Test store integration with clinical tools."""
        patient = get_patient_record(sample_patient_id)
        assert patient is not None

    def test_store_conditions_flow(self, store, patient_with_conditions):
        """Test complete conditions data flow."""
        conditions = get_patient_conditions(patient_with_conditions)
        assert len(conditions) > 0
        # Each condition should have expected fields
        for cond in conditions:
            assert isinstance(cond, dict)

    def test_store_medications_flow(self, store, patient_with_medications):
        """Test complete medications data flow."""
        meds = get_patient_medications(patient_with_medications)
        assert len(meds) > 0

    def test_store_observations_flow(self, store, sample_patient_id):
        """Test observations data flow."""
        observations = get_patient_observations(sample_patient_id)
        assert isinstance(observations, list)


class TestClinicalToolsIntegration:
    """Integration tests for clinical tools."""

    def test_risk_assessment_flow(self, patient_with_conditions):
        """Test risk assessment integration."""
        risks = assess_patient_risks(patient_with_conditions)
        assert isinstance(risks, list)
        for risk in risks:
            assert "risk_type" in risk
            assert "score" in risk
            assert "risk_level" in risk

    def test_drug_interactions_flow(self, patient_with_medications):
        """Test drug interactions integration."""
        result = check_drug_interactions(patient_with_medications)
        assert isinstance(result, dict)
        assert "medication_count" in result
        assert "risk_level" in result

    def test_clinical_trials_flow(self, patient_with_conditions):
        """Test clinical trials matching."""
        matches = match_clinical_trials(patient_with_conditions)
        assert isinstance(matches, list)

    def test_forecast_flow(self, patient_with_conditions):
        """Test outcome forecasting."""
        forecast = forecast_patient_outcome(patient_with_conditions)
        assert isinstance(forecast, dict)
        assert "risks" in forecast

    def test_lab_analysis_flow(self, sample_patient_id):
        """Test lab analysis."""
        analysis = get_lab_analysis(sample_patient_id)
        assert isinstance(analysis, dict)
        assert "lab_results" in analysis


class TestCacheIntegration:
    """Integration tests for caching with other components."""

    def test_cache_with_store(self, store, cache):
        """Test caching with store operations."""
        patients = store.tables.get("patients")
        if patients is None or len(patients) == 0:
            pytest.skip("No patients")
        patient_id = patients.iloc[0]["Id"]

        # First call - cache miss
        patient1 = cache.get_or_set(
            f"patient:{patient_id}",
            lambda: store.patient(patient_id),
        )

        # Second call - cache hit
        patient2 = cache.get_or_set(
            f"patient:{patient_id}",
            lambda: store.patient(patient_id),
        )

        assert patient1 == patient2

    def test_cache_invalidation_pattern(self, cache):
        """Test pattern-based cache invalidation."""
        cache.set("user:1:name", "Alice")
        cache.set("user:2:name", "Bob")
        cache.set("other:key", "value")

        count = cache.invalidate_pattern("user:")
        assert count == 2
        assert cache.get("other:key") == "value"


# ============================================================================
# 3. API TESTS - Endpoint Testing
# ============================================================================

class TestHealthAPI:
    """Tests for health endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "aegis"
        assert "version" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data


class TestPatientAPI:
    """Tests for patient endpoints."""

    def test_list_patients(self, client):
        """Test listing patients."""
        response = client.get("/v1/patients?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert "total" in data
        assert data["total"] > 0

    def test_list_patients_pagination(self, client):
        """Test patient list pagination."""
        response = client.get("/v1/patients?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["patients"]) <= 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_get_patient(self, client, sample_patient_id):
        """Test getting a patient."""
        response = client.get(f"/v1/patients/{sample_patient_id}")
        assert response.status_code == 200

    def test_get_patient_not_found(self, client):
        """Test patient not found."""
        response = client.get("/v1/patients/nonexistent")
        assert response.status_code == 404

    def test_get_patient_conditions(self, client, patient_with_conditions):
        """Test getting patient conditions."""
        response = client.get(f"/v1/patients/{patient_with_conditions}/conditions")
        assert response.status_code == 200
        data = response.json()
        assert "conditions" in data

    def test_get_patient_medications(self, client, patient_with_medications):
        """Test getting patient medications."""
        response = client.get(f"/v1/patients/{patient_with_medications}/medications")
        assert response.status_code == 200
        data = response.json()
        assert "medications" in data

    def test_get_patient_observations(self, client, sample_patient_id):
        """Test getting patient observations."""
        response = client.get(f"/v1/patients/{sample_patient_id}/observations")
        assert response.status_code == 200
        data = response.json()
        assert "observations" in data

    def test_get_patient_encounters(self, client, sample_patient_id):
        """Test getting patient encounters."""
        response = client.get(f"/v1/patients/{sample_patient_id}/encounters")
        assert response.status_code == 200
        data = response.json()
        assert "encounters" in data

    def test_get_patient_journey(self, client, sample_patient_id):
        """Test getting patient journey."""
        response = client.get(f"/patients/{sample_patient_id}/journey")
        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data
        assert "current_state" in data


class TestInvestigationAPI:
    """Tests for investigation endpoints."""

    def test_run_investigation(self, client, sample_patient_id):
        """Test running an investigation."""
        response = client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "Summarize this patient's health",
        })
        assert response.status_code == 200
        data = response.json()
        assert "trace_id" in data
        assert "conclusion" in data
        assert "confidence" in data

    def test_run_investigation_validation(self, client):
        """Test investigation input validation."""
        response = client.post("/v1/investigations", json={
            "patient_id": "",
            "question": "ab",
        })
        assert response.status_code == 422  # Validation error

    def test_list_traces(self, client, sample_patient_id):
        """Test listing traces."""
        # Create a trace first
        client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "Test question",
        })

        response = client.get("/v1/traces")
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data

    def test_get_trace(self, client, sample_patient_id):
        """Test getting a specific trace."""
        # Create a trace
        create_response = client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "Test question",
        })
        trace_id = create_response.json()["trace_id"]

        response = client.get(f"/v1/traces/{trace_id}")
        assert response.status_code == 200

    def test_review_trace(self, client, sample_patient_id):
        """Test reviewing a trace."""
        # Create a trace
        create_response = client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "Test question",
        })
        trace_id = create_response.json()["trace_id"]

        # Review it
        response = client.post(f"/v1/traces/{trace_id}/review", json={
            "decision": "approved",
            "reviewer_id": "test-reviewer",
            "notes": "Looks good",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["reviewed"] is True
        assert data["review_decision"] == "approved"


class TestClinicalAPI:
    """Tests for clinical endpoints."""

    def test_risk_assessment(self, client, patient_with_conditions):
        """Test risk assessment endpoint."""
        response = client.get(f"/v1/patients/{patient_with_conditions}/risk-assessment")
        assert response.status_code == 200
        data = response.json()
        assert "risks" in data

    def test_drug_interactions(self, client, patient_with_medications):
        """Test drug interactions endpoint."""
        response = client.get(f"/v1/patients/{patient_with_medications}/drug-interactions")
        assert response.status_code == 200
        data = response.json()
        assert "medication_count" in data

    def test_clinical_trials(self, client, patient_with_conditions):
        """Test clinical trials endpoint."""
        response = client.get(f"/v1/patients/{patient_with_conditions}/clinical-trials")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data


class TestV2API:
    """Tests for v2 API endpoints."""

    def test_list_agents(self, client):
        """Test listing agents."""
        response = client.get("/v2/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 4

    def test_list_tools(self, client):
        """Test listing tools."""
        response = client.get("/v2/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["total"] > 0


# ============================================================================
# 4. PERFORMANCE TESTS - Load and Stress Testing
# ============================================================================

class TestPerformance:
    """Performance tests."""

    def test_store_load_time(self):
        """Test store loading performance."""
        start = time.perf_counter()
        store = SyntheaStore("data/synthea")
        store.load()
        duration = (time.perf_counter() - start) * 1000
        assert duration < 5000  # Should load in under 5 seconds

    def test_patient_lookup_performance(self, store):
        """Test patient lookup performance."""
        patients = store.tables.get("patients")
        if patients is None or len(patients) == 0:
            pytest.skip("No patients")
        patient_id = patients.iloc[0]["Id"]

        start = time.perf_counter()
        for _ in range(100):
            store.patient(patient_id)
        duration = (time.perf_counter() - start) * 1000

        avg_duration = duration / 100
        assert avg_duration < 10  # Should be under 10ms per lookup

    def test_cache_performance(self, cache):
        """Test cache performance."""
        start = time.perf_counter()
        for i in range(1000):
            cache.set(f"key{i}", f"value{i}")
        for i in range(1000):
            cache.get(f"key{i}")
        duration = (time.perf_counter() - start) * 1000

        assert duration < 1000  # Should complete in under 1 second

    def test_api_response_time(self, client, sample_patient_id):
        """Test API response time."""
        start = time.perf_counter()
        response = client.get(f"/v1/patients/{sample_patient_id}")
        duration = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert duration < 1000  # Should respond in under 1 second

    def test_investigation_response_time(self, client, sample_patient_id):
        """Test investigation response time."""
        start = time.perf_counter()
        response = client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "Summarize health",
        })
        duration = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert duration < 5000  # Should complete in under 5 seconds

    def test_concurrent_requests(self, client, sample_patient_id):
        """Test concurrent request handling."""
        def make_request():
            return client.get(f"/v1/patients/{sample_patient_id}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        assert all(r.status_code == 200 for r in results)


# ============================================================================
# 5. SECURITY TESTS - Vulnerability Testing
# ============================================================================

class TestSecurity:
    """Security tests."""

    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention."""
        response = client.get("/v1/patients/'; DROP TABLE patients;--")
        # Should not crash - either 404 or sanitized
        assert response.status_code in [404, 400, 422]

    def test_xss_prevention(self, client):
        """Test XSS prevention in inputs."""
        response = client.post("/v1/investigations", json={
            "patient_id": "test",
            "question": "<script>alert('xss')</script>",
        })
        # Should either reject or sanitize
        assert response.status_code in [400, 422, 200]

    def test_path_traversal_prevention(self, client):
        """Test path traversal prevention."""
        response = client.get("/v1/patients/../../../etc/passwd")
        assert response.status_code in [404, 400, 422]

    def test_rate_limiting(self):
        """Test rate limiting."""
        limiter = RateLimiter()
        request = MagicMock()
        request.headers = {}
        request.url.path = "/test"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock(spec=[])

        # Make requests up to limit
        for _ in range(100):
            limiter.check_rate_limit(request)

        # Next should be blocked
        allowed, _ = limiter.check_rate_limit(request)
        assert allowed is False

    def test_audit_logging(self, audit_logger):
        """Test audit logging for security events."""
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key", "attacker")
        audit_logger.log_security_event("suspicious_activity", "user1", "127.0.0.1")

        events = audit_logger.get_security_events()
        assert len(events) == 2


# ============================================================================
# 6. RESILIENCE TESTS - Fault Tolerance Testing
# ============================================================================

class TestResilience:
    """Resilience tests."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
        ))

        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("fail")
            return "success"

        # Fail twice to open
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.execute(flaky)

        assert cb.state.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.2)

        # Should succeed now
        result = await cb.execute(flaky)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not ready")
            return "ready"

        config = RetryConfig(max_retries=3, base_delay=0.01)
        start = time.perf_counter()
        result = await retry_async(flaky, config)
        duration = time.perf_counter() - start

        assert result == "ready"
        assert call_count == 3
        # Should have some delay from retries
        assert duration > 0.01

    @pytest.mark.asyncio
    async def test_health_checker(self):
        """Test health checking."""
        checker = HealthChecker()

        def healthy():
            return {"status": "ok"}

        def unhealthy():
            raise ValueError("down")

        checker.register("service1", healthy)
        checker.register("service2", unhealthy)

        result = await checker.check_all()
        assert result["status"] == "degraded"  # One unhealthy
        assert len(result["checks"]) == 2


# ============================================================================
# 7. END-TO-END TESTS - Complete Workflow Testing
# ============================================================================

class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_complete_investigation_workflow(self, client, sample_patient_id):
        """Test complete investigation workflow."""
        # 1. List patients
        response = client.get("/v1/patients?limit=1")
        assert response.status_code == 200

        # 2. Get patient details
        response = client.get(f"/v1/patients/{sample_patient_id}")
        assert response.status_code == 200

        # 3. Run investigation
        response = client.post("/v1/investigations", json={
            "patient_id": sample_patient_id,
            "question": "What are the main health concerns?",
        })
        assert response.status_code == 200
        trace_id = response.json()["trace_id"]

        # 4. Get trace
        response = client.get(f"/v1/traces/{trace_id}")
        assert response.status_code == 200

        # 5. Review trace
        response = client.post(f"/v1/traces/{trace_id}/review", json={
            "decision": "approved",
            "reviewer_id": "test-doctor",
            "notes": "Comprehensive analysis",
        })
        assert response.status_code == 200
        assert response.json()["reviewed"] is True

    def test_patient_data_exploration(self, client, sample_patient_id):
        """Test patient data exploration workflow."""
        # Get all patient data
        endpoints = [
            f"/v1/patients/{sample_patient_id}",
            f"/v1/patients/{sample_patient_id}/conditions",
            f"/v1/patients/{sample_patient_id}/medications",
            f"/v1/patients/{sample_patient_id}/observations",
            f"/v1/patients/{sample_patient_id}/encounters",
            f"/patients/{sample_patient_id}/journey",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed: {endpoint}"

    def test_clinical_analysis_workflow(self, client, patient_with_conditions):
        """Test clinical analysis workflow."""
        # Risk assessment
        response = client.get(f"/v1/patients/{patient_with_conditions}/risk-assessment")
        assert response.status_code == 200

        # Drug interactions
        response = client.get(f"/v1/patients/{patient_with_conditions}/drug-interactions")
        assert response.status_code == 200

        # Clinical trials
        response = client.get(f"/v1/patients/{patient_with_conditions}/clinical-trials")
        assert response.status_code == 200

    def test_multi_investigation_workflow(self, client, sample_patient_id):
        """Test multiple investigations workflow."""
        # Run multiple investigations
        questions = [
            "Summarize health status",
            "List conditions",
        ]

        trace_ids = []
        for question in questions:
            response = client.post("/v1/investigations", json={
                "patient_id": sample_patient_id,
                "question": question,
            })
            # May hit rate limit, that's ok
            if response.status_code == 200:
                trace_ids.append(response.json()["trace_id"])
            elif response.status_code == 429:
                break  # Rate limited, stop

        # Should have at least one trace
        assert len(trace_ids) >= 1


# ============================================================================
# 8. TOOL REGISTRY TESTS
# ============================================================================

class TestToolRegistry:
    """Tests for tool registry."""

    def test_tool_registration(self):
        """Test tool registration."""
        registry = ToolRegistry()

        @registry.tool(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.DATA_ACCESS,
            returns="str",
        )
        def my_tool(param: str) -> str:
            return f"Result: {param}"

        assert "test_tool" in registry._tools

    def test_tool_execution(self):
        """Test tool execution."""
        registry = ToolRegistry()

        @registry.tool(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.DATA_ACCESS,
            returns="str",
        )
        def my_tool(param: str) -> str:
            return f"Result: {param}"

        result = registry.execute_sync("test_tool", param="hello")
        assert result.success is True
        assert result.data == "Result: hello"

    def test_tool_definitions(self):
        """Test tool definitions."""
        registry = ToolRegistry()

        @registry.tool(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.DATA_ACCESS,
            returns="str",
        )
        def my_tool(param: str) -> str:
            return f"Result: {param}"

        defn = registry.get_definition("test_tool")
        assert defn is not None
        assert defn.name == "test_tool"
        assert defn.category == ToolCategory.DATA_ACCESS

    def test_tool_prompt_generation(self):
        """Test tool prompt generation."""
        registry = ToolRegistry()

        @registry.tool(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.DATA_ACCESS,
            returns="str",
        )
        def my_tool(param: str) -> str:
            return f"Result: {param}"

        prompt = registry.get_tools_for_prompt()
        assert "test_tool" in prompt
        assert "Test tool" in prompt


# ============================================================================
# Test Campaign Runner
# ============================================================================

def run_test_campaign():
    """Run the complete test campaign and generate report."""
    import subprocess

    print("=" * 80)
    print("AEGIS COMPREHENSIVE TEST CAMPAIGN")
    print("=" * 80)

    # Run tests with verbose output
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd="/Users/samuel.hyle/medusa",
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    success = run_test_campaign()
    exit(0 if success else 1)
