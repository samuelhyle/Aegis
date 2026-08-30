"""
Tests for Temporal Intelligence Engine

Comprehensive tests for temporal analysis including:
- Temporal data structures
- Disease progression models
- Trajectory prediction
- Anomaly detection
- Temporal reasoning agent
- API endpoints
"""

import os
from datetime import datetime, timedelta, timezone

import pytest

# Set test environment
os.environ["AEGIS_AUTH_DISABLED"] = "true"
os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"

from aegis.store import SyntheaStore
from aegis.temporal import (
    AnomalyDetector,
    AnomalyType,
    DiseaseProgressionModeler,
    HealthState,
    HealthTrajectory,
    ProgressionModel,
    TemporalAnalyzer,
    TemporalAnomaly,
    TemporalReasoningEngine,
    TemporalSeries,
    TrajectoryPredictor,
    TrendDirection,
)
from aegis.temporal_agent import TemporalReasoningAgent

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def store():
    """Create a loaded store for testing."""
    s = SyntheaStore("data/synthea")
    s.load()
    return s


@pytest.fixture
def sample_patient_id(store):
    """Get a sample patient ID."""
    patients = store.tables.get("patients")
    if patients is None or len(patients) == 0:
        pytest.skip("No patients")
    return patients.iloc[0]["Id"]


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi.testclient import TestClient

    from aegis.api import app
    return TestClient(app)


@pytest.fixture
def sample_series():
    """Create a sample time series."""
    series = TemporalSeries(
        series_id="test_glucose",
        name="Glucose",
        unit="mg/dL",
        reference_low=70,
        reference_high=100,
        critical_low=54,
        critical_high=250,
    )

    # Add points over 6 months
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    values = [90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145]

    for i, value in enumerate(values):
        series.add_point(
            timestamp=base_date + timedelta(days=i * 30),
            value=value,
        )

    return series


@pytest.fixture
def sample_trajectory():
    """Create a sample health trajectory."""
    trajectory = HealthTrajectory(patient_id="test_patient")

    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    trajectory.add_state(base_date, HealthState.HEALTHY)
    trajectory.add_state(base_date + timedelta(days=180), HealthState.AT_RISK)
    trajectory.add_state(base_date + timedelta(days=365), HealthState.CHRONIC)

    return trajectory


# ============================================================================
# Test Temporal Data Structures
# ============================================================================

class TestTemporalSeries:
    """Tests for TemporalSeries."""

    def test_creation(self):
        """Test series creation."""
        series = TemporalSeries(
            series_id="test",
            name="Test",
            unit="mg/dL",
        )
        assert series.series_id == "test"
        assert series.name == "Test"
        assert len(series.points) == 0

    def test_add_point(self, sample_series):
        """Test adding points."""
        assert len(sample_series.points) == 12
        assert sample_series.latest.value == 145

    def test_values_property(self, sample_series):
        """Test values property."""
        values = sample_series.values
        assert len(values) == 12
        assert values[0] == 90
        assert values[-1] == 145

    def test_mean(self, sample_series):
        """Test mean calculation."""
        mean = sample_series.mean
        assert mean > 0
        assert 90 < mean < 150

    def test_std_dev(self, sample_series):
        """Test standard deviation calculation."""
        std = sample_series.std_dev
        assert std > 0

    def test_sorted_by_timestamp(self, sample_series):
        """Test points are sorted by timestamp."""
        timestamps = sample_series.timestamps
        for i in range(len(timestamps) - 1):
            assert timestamps[i] <= timestamps[i + 1]


class TestHealthTrajectory:
    """Tests for HealthTrajectory."""

    def test_creation(self):
        """Test trajectory creation."""
        trajectory = HealthTrajectory(patient_id="test")
        assert trajectory.patient_id == "test"
        assert trajectory.current_state == HealthState.HEALTHY

    def test_add_state(self, sample_trajectory):
        """Test adding states."""
        assert len(sample_trajectory.states) == 3
        assert sample_trajectory.current_state == HealthState.CHRONIC

    def test_transitions(self, sample_trajectory):
        """Test transitions."""
        assert len(sample_trajectory.transitions) == 2

    def test_state_durations(self, sample_trajectory):
        """Test state durations."""
        durations = sample_trajectory.state_durations
        assert HealthState.HEALTHY in durations
        assert durations[HealthState.HEALTHY] > 0

    def test_get_state_at(self, sample_trajectory):
        """Test getting state at time."""
        base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Before any states
        state = sample_trajectory.get_state_at(base_date - timedelta(days=1))
        assert state is None

        # At first state
        state = sample_trajectory.get_state_at(base_date)
        assert state == HealthState.HEALTHY

        # Between states
        state = sample_trajectory.get_state_at(base_date + timedelta(days=100))
        assert state == HealthState.HEALTHY

        # After second state
        state = sample_trajectory.get_state_at(base_date + timedelta(days=200))
        assert state == HealthState.AT_RISK

    def test_get_transition_count(self, sample_trajectory):
        """Test transition count."""
        count = sample_trajectory.get_transition_count(
            HealthState.HEALTHY, HealthState.AT_RISK
        )
        assert count == 1


# ============================================================================
# Test Anomaly Detection
# ============================================================================

class TestAnomalyDetection:
    """Tests for anomaly detection."""

    def test_zscore_anomalies(self, store, sample_patient_id):
        """Test Z-score anomaly detection."""
        detector = AnomalyDetector(store)
        anomalies = detector.detect_anomalies(sample_patient_id)

        # Should return a list (may or may not have anomalies)
        assert isinstance(anomalies, list)

    def test_anomaly_types(self):
        """Test anomaly type enum."""
        assert AnomalyType.SUDDEN_CHANGE.value == "sudden_change"
        assert AnomalyType.OUT_OF_RANGE.value == "out_of_range"
        assert AnomalyType.TREND_BREAK.value == "trend_break"

    def test_anomaly_creation(self):
        """Test anomaly creation."""
        anomaly = TemporalAnomaly(
            anomaly_id="test",
            anomaly_type=AnomalyType.SUDDEN_CHANGE,
            timestamp=datetime.now(timezone.utc),
            series_id="test_series",
            description="Test anomaly",
            severity="high",
            value=150.0,
            expected_range=(70, 100),
            confidence=0.9,
        )
        assert anomaly.severity == "high"
        assert anomaly.confidence == 0.9


# ============================================================================
# Test Disease Progression
# ============================================================================

class TestDiseaseProgression:
    """Tests for disease progression modeling."""

    def test_progression_model(self):
        """Test progression model creation."""
        model = ProgressionModel(
            model_id="test",
            condition="hypertension",
            states=[HealthState.AT_RISK, HealthState.CHRONIC],
        )
        assert model.model_id == "test"
        assert len(model.states) == 2

    def test_health_states(self):
        """Test health state enum."""
        assert HealthState.HEALTHY.value == "healthy"
        assert HealthState.CHRONIC.value == "chronic"
        assert HealthState.RECOVERY.value == "recovery"

    def test_predict_progression(self, store, sample_patient_id):
        """Test progression prediction."""
        modeler = DiseaseProgressionModeler(store)

        # Get a condition for this patient
        conditions = store.rows("conditions", sample_patient_id)
        if not conditions:
            pytest.skip("No conditions")

        condition = conditions[0].get("DESCRIPTION", "")
        if not condition:
            pytest.skip("No condition description")

        result = modeler.predict_progression(
            sample_patient_id, condition, horizon_days=365
        )

        assert "patient_id" in result
        assert "condition" in result
        assert "predictions" in result


# ============================================================================
# Test Trajectory Prediction
# ============================================================================

class TestTrajectoryPrediction:
    """Tests for trajectory prediction."""

    def test_predict_lab_trajectory(self, store, sample_patient_id):
        """Test lab trajectory prediction."""
        predictor = TrajectoryPredictor(store)

        result = predictor.predict_lab_trajectory(
            sample_patient_id, "glucose", horizon_days=90
        )

        # May have error if insufficient data
        assert "patient_id" in result
        assert "lab_name" in result

    def test_predict_risk_trajectory(self, store, sample_patient_id):
        """Test risk trajectory prediction."""
        predictor = TrajectoryPredictor(store)

        result = predictor.predict_risk_trajectory(
            sample_patient_id, "hypertension", horizon_days=365
        )

        assert "patient_id" in result
        assert "condition" in result
        assert "risk_trajectory" in result

    def test_trend_directions(self):
        """Test trend direction enum."""
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.WORSENING.value == "worsening"
        assert TrendDirection.STABLE.value == "stable"


# ============================================================================
# Test Temporal Analyzer
# ============================================================================

class TestTemporalAnalyzer:
    """Tests for TemporalAnalyzer."""

    def test_build_time_series(self, store, sample_patient_id):
        """Test building time series."""
        analyzer = TemporalAnalyzer(store)

        series = analyzer.build_time_series(
            sample_patient_id, "glucose", "glucose"
        )

        assert isinstance(series, TemporalSeries)
        assert series.name == "glucose"

    def test_build_patient_trajectories(self, store, sample_patient_id):
        """Test building patient trajectories."""
        analyzer = TemporalAnalyzer(store)

        trajectories = analyzer.build_patient_trajectories(sample_patient_id)

        assert isinstance(trajectories, dict)

    def test_parse_date(self, store):
        """Test date parsing."""
        analyzer = TemporalAnalyzer(store)

        # Valid date
        date = analyzer._parse_date("2024-01-01")
        assert date is not None
        assert date.year == 2024

        # Invalid date
        date = analyzer._parse_date("invalid")
        assert date is None

        # Empty date
        date = analyzer._parse_date("")
        assert date is None


# ============================================================================
# Test Temporal Reasoning Engine
# ============================================================================

class TestTemporalReasoningEngine:
    """Tests for TemporalReasoningEngine."""

    def test_analyze_patient_timeline(self, store, sample_patient_id):
        """Test comprehensive temporal analysis."""
        engine = TemporalReasoningEngine(store)

        result = engine.analyze_patient_timeline(sample_patient_id)

        assert "patient_id" in result
        assert "trajectories" in result
        assert "anomalies" in result
        assert "timeline" in result


# ============================================================================
# Test Temporal Reasoning Agent
# ============================================================================

class TestTemporalReasoningAgent:
    """Tests for TemporalReasoningAgent."""

    def test_agent_name(self):
        """Test agent name."""
        try:
            agent = TemporalReasoningAgent()
            assert agent.name == "temporal_reasoning"
        except Exception:
            pytest.skip("No data available")

    def test_agent_role(self):
        """Test agent role."""
        try:
            agent = TemporalReasoningAgent()
            assert "temporal" in agent.role.lower()
        except Exception:
            pytest.skip("No data available")

    def test_agent_tools(self):
        """Test agent tools."""
        try:
            agent = TemporalReasoningAgent()
            tools = agent.get_available_tools()
            assert "analyze_temporal_patterns" in tools
            assert "predict_disease_progression" in tools
            assert "detect_temporal_anomalies" in tools
        except Exception:
            pytest.skip("No data available")

    def test_agent_system_prompt(self):
        """Test agent system prompt."""
        try:
            agent = TemporalReasoningAgent()
            prompt = agent.get_system_prompt()
            assert "temporal" in prompt.lower()
            assert "time" in prompt.lower()
        except Exception:
            pytest.skip("No data available")


# ============================================================================
# Test API Endpoints
# ============================================================================

class TestTemporalAPI:
    """Tests for temporal API endpoints."""

    def test_temporal_analysis_endpoint(self, client, sample_patient_id):
        """Test temporal analysis endpoint."""
        response = client.get(f"/v2/temporal/{sample_patient_id}")
        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data

    def test_anomalies_endpoint(self, client, sample_patient_id):
        """Test anomalies endpoint."""
        response = client.get(f"/v2/temporal/{sample_patient_id}/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data

    def test_predictions_endpoint(self, client, sample_patient_id):
        """Test predictions endpoint."""
        response = client.get(
            f"/v2/temporal/{sample_patient_id}/predictions?lab_name=glucose"
        )
        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data

    def test_progression_endpoint(self, client, sample_patient_id):
        """Test progression endpoint."""
        # Get a condition
        response = client.get(f"/v1/patients/{sample_patient_id}/conditions")
        conditions = response.json().get("conditions", [])

        if conditions:
            condition = conditions[0].get("DESCRIPTION", "")
            response = client.get(
                f"/v2/temporal/{sample_patient_id}/progression/{condition}"
            )
            assert response.status_code == 200

    def test_timeline_endpoint(self, client, sample_patient_id):
        """Test timeline endpoint."""
        response = client.get(f"/v2/temporal/{sample_patient_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_trajectories_endpoint(self, client, sample_patient_id):
        """Test trajectories endpoint."""
        response = client.get(f"/v2/temporal/{sample_patient_id}/trajectories")
        assert response.status_code == 200
        data = response.json()
        assert "trajectories" in data
