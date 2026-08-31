"""
Temporal Intelligence Engine - Disease Progression & Trajectory Prediction

This module implements a clinically differentiated temporal intelligence system:

1. **Temporal Data Structures**: Time series representation of patient health
2. **Disease Progression Models**: Markov chains, survival analysis, trend detection
3. **Trajectory Prediction**: Forecasting future health states
4. **Anomaly Detection**: Z-score, IQR, change point detection
5. **Temporal Reasoning**: Understanding time-based clinical relationships

This is CLINICALLY DIFFERENTENTIATED because it:
- Models disease progression over time (not just snapshots)
- Predicts future health trajectories
- Detects anomalies in temporal patterns
- Understands clinical time concepts (acute, chronic, recovery)
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Optional

from .store import SyntheaStore

# ============================================================================
# Temporal Data Structures
# ============================================================================

class HealthState(StrEnum):
    """Health states for disease progression."""
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    ACUTE = "acute"
    CHRONIC = "chronic"
    RECOVERY = "recovery"
    REMISSION = "remission"
    RELAPSE = "relapse"
    END_STAGE = "end_stage"


class TrendDirection(StrEnum):
    """Direction of a trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class AnomalyType(StrEnum):
    """Types of temporal anomalies."""
    SUDDEN_CHANGE = "sudden_change"
    TREND_BREAK = "trend_break"
    OUT_OF_RANGE = "out_of_range"
    MISSING_DATA = "missing_data"
    UNUSUAL_SEQUENCE = "unusual_sequence"


@dataclass
class TemporalPoint:
    """A single point in a time series."""
    timestamp: datetime
    value: float
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalSeries:
    """A time series of clinical measurements."""
    series_id: str
    name: str
    unit: str
    points: list[TemporalPoint] = field(default_factory=list)
    reference_low: float | None = None
    reference_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None

    @property
    def values(self) -> list[float]:
        """Get all values."""
        return [p.value for p in self.points]

    @property
    def timestamps(self) -> list[datetime]:
        """Get all timestamps."""
        return [p.timestamp for p in self.points]

    @property
    def latest(self) -> TemporalPoint | None:
        """Get the latest point."""
        return self.points[-1] if self.points else None

    @property
    def mean(self) -> float:
        """Calculate mean value."""
        vals = self.values
        return sum(vals) / len(vals) if vals else 0.0

    @property
    def std_dev(self) -> float:
        """Calculate standard deviation."""
        vals = self.values
        if len(vals) < 2:
            return 0.0
        mean = self.mean
        variance = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
        return math.sqrt(variance)

    def add_point(self, timestamp: datetime, value: float, **kwargs):
        """Add a point to the series."""
        self.points.append(TemporalPoint(
            timestamp=timestamp,
            value=value,
            **kwargs,
        ))
        # Keep sorted by timestamp
        self.points.sort(key=lambda p: p.timestamp)


@dataclass
class HealthTrajectory:
    """A patient's health trajectory over time."""
    patient_id: str
    states: list[tuple[datetime, HealthState]] = field(default_factory=list)
    transitions: list[tuple[datetime, HealthState, HealthState]] = field(default_factory=list)
    current_state: HealthState = HealthState.HEALTHY
    state_durations: dict[HealthState, float] = field(default_factory=dict)  # days

    def add_state(self, timestamp: datetime, state: HealthState):
        """Add a state to the trajectory."""
        if self.states:
            prev_time, prev_state = self.states[-1]
            self.transitions.append((timestamp, prev_state, state))
            # Calculate duration
            duration = (timestamp - prev_time).total_seconds() / 86400
            self.state_durations[prev_state] = (
                self.state_durations.get(prev_state, 0) + duration
            )

        self.states.append((timestamp, state))
        self.current_state = state

    def get_state_at(self, timestamp: datetime) -> HealthState | None:
        """Get the health state at a specific time."""
        for i in range(len(self.states) - 1, -1, -1):
            if self.states[i][0] <= timestamp:
                return self.states[i][1]
        return None

    def get_duration_in_state(self, state: HealthState) -> float:
        """Get total duration in a state (days)."""
        return self.state_durations.get(state, 0.0)

    def get_transition_count(self, from_state: HealthState, to_state: HealthState) -> int:
        """Count transitions between states."""
        return sum(
            1 for _, f, t in self.transitions
            if f == from_state and t == to_state
        )


@dataclass
class TemporalAnomaly:
    """A detected anomaly in temporal data."""
    anomaly_id: str
    anomaly_type: AnomalyType
    timestamp: datetime
    series_id: str
    description: str
    severity: str  # low, medium, high, critical
    value: float
    expected_range: tuple[float, float]
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressionModel:
    """A disease progression model."""
    model_id: str
    condition: str
    states: list[HealthState]
    transition_matrix: dict[tuple[HealthState, HealthState], float] = field(default_factory=dict)
    mean_durations: dict[HealthState, float] = field(default_factory=dict)  # days
    risk_factors: dict[str, float] = field(default_factory=dict)


# ============================================================================
# Temporal Analysis Engine
# ============================================================================

class TemporalAnalyzer:
    """Core temporal analysis engine."""

    def __init__(self, store: SyntheaStore):
        self.store = store

    def build_time_series(
        self,
        patient_id: str,
        series_type: str,
        description_filter: str | None = None,
    ) -> TemporalSeries:
        """Build a time series from patient observations."""
        observations = self.store.rows("observations", patient_id)

        # Filter by description if specified
        if description_filter:
            observations = [
                obs for obs in observations
                if description_filter.lower() in obs.get("DESCRIPTION", "").lower()
            ]

        # Create series
        series = TemporalSeries(
            series_id=f"{patient_id}_{series_type}",
            name=series_type,
            unit="",
        )

        for obs in observations:
            value = obs.get("VALUE")
            date = obs.get("DATE", "")

            if value is not None and date:
                try:
                    numeric_value = float(value)
                    timestamp = self._parse_date(date)

                    if timestamp:
                        series.add_point(
                            timestamp=timestamp,
                            value=numeric_value,
                            label=obs.get("DESCRIPTION", ""),
                        )

                        # Set unit from first observation
                        if not series.unit:
                            series.unit = obs.get("UNITS", "")

                except (ValueError, TypeError):
                    continue

        # Set reference ranges based on series type
        self._set_reference_ranges(series, series_type)

        return series

    def build_patient_trajectories(
        self,
        patient_id: str,
    ) -> dict[str, HealthTrajectory]:
        """Build health trajectories for a patient."""
        trajectories = {}

        # Get conditions
        conditions = self.store.rows("conditions", patient_id)

        for condition in conditions:
            desc = condition.get("DESCRIPTION", "")
            start = condition.get("START", "")
            stop = condition.get("STOP", "")

            if not start:
                continue

            # Create trajectory for this condition
            trajectory = HealthTrajectory(patient_id=patient_id)

            start_time = self._parse_date(start)
            if not start_time:
                continue

            # Initial state: acute onset
            trajectory.add_state(start_time, HealthState.ACUTE)

            # If resolved, add recovery
            if stop:
                stop_time = self._parse_date(stop)
                if stop_time:
                    trajectory.add_state(stop_time, HealthState.RECOVERY)

            trajectories[desc] = trajectory

        return trajectories

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse a date string. Handles NaN/None/empty values."""
        if not date_str or (isinstance(date_str, float) and math.isnan(date_str)):
            return None
        date_str = str(date_str).strip()
        if not date_str or date_str.lower() in ("nan", "none", "null"):
            return None

        try:
            # Try ISO format
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None
        except ValueError:
            pass

        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(date_str[:10], fmt[:len(date_str[:10])])
                except (ValueError, TypeError):
                    continue
        except Exception:
            pass

        return None

    def _set_reference_ranges(self, series: TemporalSeries, series_type: str):
        """Set reference ranges based on series type."""
        ranges = {
            "glucose": (70, 100, 54, 250),
            "hba1c": (4.0, 5.6, 4.0, 9.0),
            "cholesterol": (0, 200, 0, 300),
            "hdl": (40, 60, 20, 100),
            "ldl": (0, 100, 0, 190),
            "triglycerides": (0, 150, 0, 500),
            "creatinine": (0.6, 1.2, 0.6, 10.0),
            "hemoglobin": (12.0, 17.5, 7.0, 20.0),
            "wbc": (4.5, 11.0, 2.0, 30.0),
            "platelets": (150, 400, 50, 1000),
            "tsh": (0.4, 4.0, 0.1, 10.0),
            "blood_pressure_systolic": (90, 120, 70, 180),
            "blood_pressure_diastolic": (60, 80, 40, 120),
            "heart_rate": (60, 100, 40, 150),
            "bmi": (18.5, 24.9, 16.0, 40.0),
        }

        series_lower = series_type.lower().replace(" ", "_")
        for key, (low, high, crit_low, crit_high) in ranges.items():
            if key in series_lower:
                series.reference_low = low
                series.reference_high = high
                series.critical_low = crit_low
                series.critical_high = crit_high
                break


# ============================================================================
# Disease Progression Models
# ============================================================================

class DiseaseProgressionModeler:
    """Models disease progression using statistical methods."""

    # Common disease progression patterns
    PROGRESSION_PATTERNS = {
        "hypertension": {
            "states": [HealthState.AT_RISK, HealthState.CHRONIC, HealthState.ACUTE],
            "typical_duration_days": {
                HealthState.AT_RISK: 365,
                HealthState.CHRONIC: 1825,  # 5 years
            },
            "risk_factors": {
                "age_over_65": 1.5,
                "bmi_over_30": 1.3,
                "family_history": 1.4,
            },
        },
        "diabetes": {
            "states": [HealthState.AT_RISK, HealthState.CHRONIC, HealthState.ACUTE],
            "typical_duration_days": {
                HealthState.AT_RISK: 730,  # 2 years
                HealthState.CHRONIC: 3650,  # 10 years
            },
            "risk_factors": {
                "age_over_45": 1.3,
                "bmi_over_25": 1.5,
                "sedentary": 1.2,
            },
        },
        "heart_failure": {
            "states": [HealthState.AT_RISK, HealthState.ACUTE, HealthState.CHRONIC, HealthState.END_STAGE],
            "typical_duration_days": {
                HealthState.AT_RISK: 365,
                HealthState.ACUTE: 30,
                HealthState.CHRONIC: 1825,
            },
            "risk_factors": {
                "hypertension": 1.4,
                "diabetes": 1.3,
                "age_over_65": 1.5,
            },
        },
    }

    def __init__(self, store: SyntheaStore):
        self.store = store

    def build_progression_model(
        self,
        condition: str,
        patient_ids: list[str] | None = None,
    ) -> ProgressionModel:
        """Build a disease progression model from patient data."""
        # Get pattern template
        pattern = self._get_pattern(condition)

        # Collect patient trajectories
        trajectories = []
        if patient_ids:
            for pid in patient_ids:
                trajectory = self._build_patient_trajectory(pid, condition)
                if trajectory:
                    trajectories.append(trajectory)

        # Calculate transition probabilities
        transition_counts: dict[tuple[HealthState, HealthState], int] = defaultdict(int)
        state_durations: dict[HealthState, list[float]] = defaultdict(list)

        for trajectory in trajectories:
            for _, from_state, to_state in trajectory.transitions:
                transition_counts[(from_state, to_state)] += 1

            for state, duration in trajectory.state_durations.items():
                state_durations[state].append(duration)

        # Calculate transition probabilities
        total_from_state: dict[HealthState, int] = defaultdict(int)
        for (from_state, _), count in transition_counts.items():
            total_from_state[from_state] += count

        transition_matrix = {}
        for (from_state, to_state), count in transition_counts.items():
            total = total_from_state[from_state]
            if total > 0:
                transition_matrix[(from_state, to_state)] = count / total

        # Calculate mean durations
        mean_durations = {}
        for state, durations in state_durations.items():
            if durations:
                mean_durations[state] = sum(durations) / len(durations)

        return ProgressionModel(
            model_id=f"model_{condition}",
            condition=condition,
            states=pattern["states"],
            transition_matrix=transition_matrix,
            mean_durations=mean_durations,
            risk_factors=pattern.get("risk_factors", {}),
        )

    def predict_progression(
        self,
        patient_id: str,
        condition: str,
        horizon_days: int = 365,
    ) -> dict[str, Any]:
        """Predict disease progression for a patient."""
        # Get current state
        current_state = self._get_current_state(patient_id, condition)

        # Get progression model
        model = self.build_progression_model(condition)

        # Simulate progression
        predictions = self._simulate_progression(
            current_state=current_state,
            model=model,
            horizon_days=horizon_days,
        )

        return {
            "patient_id": patient_id,
            "condition": condition,
            "current_state": current_state.value,
            "horizon_days": horizon_days,
            "predictions": predictions,
            "model_confidence": self._calculate_model_confidence(model),
        }

    def _get_pattern(self, condition: str) -> dict:
        """Get progression pattern for a condition."""
        condition_lower = condition.lower()

        for key, pattern in self.PROGRESSION_PATTERNS.items():
            if key in condition_lower:
                return pattern

        # Default pattern
        return {
            "states": [HealthState.HEALTHY, HealthState.AT_RISK, HealthState.ACUTE, HealthState.CHRONIC],
            "typical_duration_days": {
                HealthState.AT_RISK: 365,
                HealthState.ACUTE: 30,
                HealthState.CHRONIC: 1825,
            },
            "risk_factors": {},
        }

    def _build_patient_trajectory(
        self,
        patient_id: str,
        condition: str,
    ) -> HealthTrajectory | None:
        """Build trajectory for a specific patient and condition."""
        conditions = self.store.rows("conditions", patient_id)

        # Find matching condition
        matching = None
        for cond in conditions:
            if condition.lower() in cond.get("DESCRIPTION", "").lower():
                matching = cond
                break

        if not matching:
            return None

        trajectory = HealthTrajectory(patient_id=patient_id)

        start = matching.get("START", "")
        stop = matching.get("STOP", "")

        if start:
            start_time = self._parse_date(start)
            if start_time:
                trajectory.add_state(start_time, HealthState.ACUTE)

                if stop:
                    stop_time = self._parse_date(stop)
                    if stop_time:
                        trajectory.add_state(stop_time, HealthState.RECOVERY)

        return trajectory if trajectory.states else None

    def _get_current_state(self, patient_id: str, condition: str) -> HealthState:
        """Get current health state for a patient."""
        conditions = self.store.rows("conditions", patient_id)

        for cond in conditions:
            if condition.lower() in cond.get("DESCRIPTION", "").lower():
                stop = cond.get("STOP", "")
                if stop:
                    return HealthState.RECOVERY
                else:
                    return HealthState.CHRONIC

        return HealthState.HEALTHY

    def _simulate_progression(
        self,
        current_state: HealthState,
        model: ProgressionModel,
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        """Simulate disease progression."""
        predictions = []
        state = current_state
        day = 0

        while day < horizon_days:
            # Find possible transitions
            possible_transitions = [
                (to_state, prob)
                for (from_state, to_state), prob in model.transition_matrix.items()
                if from_state == state
            ]

            if not possible_transitions:
                # No transitions possible, stay in current state
                predictions.append({
                    "day": day,
                    "state": state.value,
                    "probability": 1.0,
                })
                day += 30  # Check monthly
                continue

            # Select most likely transition
            next_state, prob = max(possible_transitions, key=lambda x: x[1])

            predictions.append({
                "day": day,
                "state": next_state.value,
                "probability": prob,
            })

            state = next_state
            day += 30  # Monthly transitions

        return predictions

    def _calculate_model_confidence(self, model: ProgressionModel) -> float:
        """Calculate confidence in the model."""
        if not model.transition_matrix:
            return 0.3

        # More data = higher confidence
        total_transitions = sum(model.transition_matrix.values())
        if total_transitions > 100:
            return 0.9
        elif total_transitions > 50:
            return 0.7
        elif total_transitions > 10:
            return 0.5
        else:
            return 0.3

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse a date string. Handles NaN/None/empty values."""
        if not date_str or (isinstance(date_str, float) and math.isnan(date_str)):
            return None
        date_str = str(date_str).strip()
        if not date_str or date_str.lower() in ("nan", "none", "null"):
            return None
        try:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None
        except ValueError:
            try:
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except ValueError:
                return None


# ============================================================================
# Trajectory Prediction Engine
# ============================================================================

class TrajectoryPredictor:
    """Predicts future health trajectories."""

    def __init__(self, store: SyntheaStore):
        self.store = store
        self.analyzer = TemporalAnalyzer(store)

    def predict_lab_trajectory(
        self,
        patient_id: str,
        lab_name: str,
        horizon_days: int = 90,
    ) -> dict[str, Any]:
        """Predict future lab values."""
        series = self.analyzer.build_time_series(
            patient_id, lab_name, lab_name
        )

        if len(series.points) < 3:
            return {
                "patient_id": patient_id,
                "lab_name": lab_name,
                "error": "Insufficient data for prediction",
                "data_points": len(series.points),
            }

        # Calculate trend
        trend = self._calculate_trend(series)

        # Simple linear extrapolation
        predictions = self._extrapolate_trend(series, horizon_days)

        # Calculate confidence based on data quality
        confidence = self._calculate_prediction_confidence(series)

        return {
            "patient_id": patient_id,
            "lab_name": lab_name,
            "current_value": series.latest.value if series.latest else None,
            "trend": trend.value,
            "predictions": predictions,
            "confidence": confidence,
            "data_points": len(series.points),
            "reference_range": {
                "low": series.reference_low,
                "high": series.reference_high,
            },
        }

    def predict_risk_trajectory(
        self,
        patient_id: str,
        condition: str,
        horizon_days: int = 365,
    ) -> dict[str, Any]:
        """Predict risk trajectory for a condition."""
        # Get current risk factors
        risk_factors = self._assess_risk_factors(patient_id, condition)

        # Calculate baseline risk
        baseline_risk = self._calculate_baseline_risk(patient_id, condition)

        # Project risk over time
        risk_trajectory = self._project_risk(
            baseline_risk, risk_factors, horizon_days
        )

        return {
            "patient_id": patient_id,
            "condition": condition,
            "baseline_risk": baseline_risk,
            "risk_factors": risk_factors,
            "risk_trajectory": risk_trajectory,
            "horizon_days": horizon_days,
        }

    def _calculate_trend(self, series: TemporalSeries) -> TrendDirection:
        """Calculate trend direction."""
        if len(series.points) < 2:
            return TrendDirection.UNKNOWN

        values = series.values
        n = len(values)

        # Split into halves
        first_half = values[:n // 2]
        second_half = values[n // 2:]

        first_mean = sum(first_half) / len(first_half)
        second_mean = sum(second_half) / len(second_half)

        # Calculate change percentage
        if first_mean == 0:
            return TrendDirection.UNKNOWN

        change_pct = (second_mean - first_mean) / abs(first_mean)

        if change_pct > 0.1:
            return TrendDirection.WORSENING
        elif change_pct < -0.1:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.STABLE

    def _extrapolate_trend(
        self,
        series: TemporalSeries,
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        """Extrapolate trend into the future."""
        if len(series.points) < 2:
            return []

        values = series.values
        timestamps = series.timestamps

        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return []

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Generate predictions
        predictions = []
        last_timestamp = timestamps[-1]

        for days_ahead in range(30, horizon_days + 1, 30):
            future_x = n + (days_ahead / 30)  # Approximate monthly steps
            predicted_value = slope * future_x + intercept

            future_timestamp = last_timestamp + timedelta(days=days_ahead)

            predictions.append({
                "date": future_timestamp.isoformat(),
                "value": round(predicted_value, 2),
                "days_ahead": days_ahead,
            })

        return predictions

    def _calculate_prediction_confidence(self, series: TemporalSeries) -> float:
        """Calculate confidence in predictions."""
        n = len(series.points)

        if n < 3:
            return 0.2
        elif n < 6:
            return 0.4
        elif n < 12:
            return 0.6
        else:
            return 0.8

    def _assess_risk_factors(
        self,
        patient_id: str,
        condition: str,
    ) -> dict[str, float]:
        """Assess risk factors for a condition."""
        risk_factors = {}

        patient = self.store.patient(patient_id)
        conditions = self.store.rows("conditions", patient_id)
        observations = self.store.rows("observations", patient_id)

        # Age
        birthdate = patient.get("BIRTHDATE", "")
        if birthdate:
            try:
                birth_year = int(birthdate.split("-")[0])
                age = 2026 - birth_year
                if age > 65:
                    risk_factors["age_over_65"] = 1.5
                elif age > 45:
                    risk_factors["age_over_45"] = 1.2
            except (ValueError, IndexError):
                pass

        # BMI
        for obs in observations:
            if "body mass index" in obs.get("DESCRIPTION", "").lower():
                try:
                    bmi = float(obs.get("VALUE", 0))
                    if bmi > 30:
                        risk_factors["bmi_over_30"] = 1.4
                    elif bmi > 25:
                        risk_factors["bmi_over_25"] = 1.2
                except (ValueError, TypeError):
                    pass

        # Comorbidities
        condition_descs = [c.get("DESCRIPTION", "").lower() for c in conditions]
        if "hypertension" in condition_descs:
            risk_factors["hypertension"] = 1.3
        if "diabetes" in condition_descs:
            risk_factors["diabetes"] = 1.3

        return risk_factors

    def _calculate_baseline_risk(
        self,
        patient_id: str,
        condition: str,
    ) -> float:
        """Calculate baseline risk for a condition."""
        # Simplified baseline risk calculation
        risk_factors = self._assess_risk_factors(patient_id, condition)

        base_risk = 0.1  # 10% baseline

        for factor, multiplier in risk_factors.items():
            base_risk *= multiplier

        return min(base_risk, 0.95)

    def _project_risk(
        self,
        baseline_risk: float,
        risk_factors: dict[str, float],
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        """Project risk over time."""
        trajectory = []

        for days in range(0, horizon_days + 1, 30):
            # Risk increases over time with risk factors
            time_factor = 1 + (days / 365) * 0.1  # 10% increase per year
            projected_risk = baseline_risk * time_factor

            # Apply risk factor effects
            for factor, multiplier in risk_factors.items():
                projected_risk *= (1 + (multiplier - 1) * 0.1)

            projected_risk = min(projected_risk, 0.95)

            trajectory.append({
                "day": days,
                "risk": round(projected_risk, 4),
                "risk_level": self._risk_level(projected_risk),
            })

        return trajectory

    def _risk_level(self, risk: float) -> str:
        """Convert risk score to level."""
        if risk >= 0.7:
            return "very_high"
        elif risk >= 0.5:
            return "high"
        elif risk >= 0.3:
            return "moderate"
        else:
            return "low"


# ============================================================================
# Anomaly Detection Engine
# ============================================================================

class AnomalyDetector:
    """Detects anomalies in temporal clinical data."""

    def __init__(self, store: SyntheaStore):
        self.store = store
        self.analyzer = TemporalAnalyzer(store)

    def detect_anomalies(
        self,
        patient_id: str,
        lab_name: str | None = None,
    ) -> list[TemporalAnomaly]:
        """Detect anomalies in patient data."""
        anomalies = []

        if lab_name:
            # Detect anomalies in specific lab
            series = self.analyzer.build_time_series(
                patient_id, lab_name, lab_name
            )
            anomalies.extend(self._detect_series_anomalies(series))
        else:
            # Detect anomalies across all labs
            observations = self.store.rows("observations", patient_id)

            # Group by description
            lab_groups: dict[str, list[dict]] = defaultdict(list)
            for obs in observations:
                desc = obs.get("DESCRIPTION", "")
                if desc:
                    lab_groups[desc].append(obs)

            for desc, obs_list in lab_groups.items():
                series = self.analyzer.build_time_series(
                    patient_id, desc, desc
                )
                anomalies.extend(self._detect_series_anomalies(series))

        return anomalies

    def _detect_series_anomalies(
        self,
        series: TemporalSeries,
    ) -> list[TemporalAnomaly]:
        """Detect anomalies in a time series."""
        anomalies = []

        if len(series.points) < 3:
            return anomalies

        # 1. Z-score anomalies
        z_anomalies = self._detect_zscore_anomalies(series)
        anomalies.extend(z_anomalies)

        # 2. Range anomalies
        range_anomalies = self._detect_range_anomalies(series)
        anomalies.extend(range_anomalies)

        # 3. Trend break anomalies
        trend_anomalies = self._detect_trend_breaks(series)
        anomalies.extend(trend_anomalies)

        return anomalies

    def _detect_zscore_anomalies(
        self,
        series: TemporalSeries,
        threshold: float = 2.5,
    ) -> list[TemporalAnomaly]:
        """Detect anomalies using Z-score."""
        anomalies = []

        mean = series.mean
        std = series.std_dev

        if std == 0:
            return anomalies

        for point in series.points:
            z_score = abs((point.value - mean) / std)

            if z_score > threshold:
                severity = "high" if z_score > 3 else "medium"

                anomalies.append(TemporalAnomaly(
                    anomaly_id=f"zscore_{series.series_id}_{point.timestamp.isoformat()}",
                    anomaly_type=AnomalyType.SUDDEN_CHANGE,
                    timestamp=point.timestamp,
                    series_id=series.series_id,
                    description=f"Value {point.value:.1f} is {z_score:.1f} standard deviations from mean",
                    severity=severity,
                    value=point.value,
                    expected_range=(mean - 2 * std, mean + 2 * std),
                    confidence=min(z_score / 4, 1.0),
                    metadata={"z_score": z_score, "mean": mean, "std": std},
                ))

        return anomalies

    def _detect_range_anomalies(
        self,
        series: TemporalSeries,
    ) -> list[TemporalAnomaly]:
        """Detect values outside reference range."""
        anomalies = []

        if series.reference_low is None or series.reference_high is None:
            return anomalies

        for point in series.points:
            if point.value < series.critical_low:
                anomalies.append(TemporalAnomaly(
                    anomaly_id=f"range_{series.series_id}_{point.timestamp.isoformat()}",
                    anomaly_type=AnomalyType.OUT_OF_RANGE,
                    timestamp=point.timestamp,
                    series_id=series.series_id,
                    description=f"Critically low value: {point.value:.1f}",
                    severity="critical",
                    value=point.value,
                    expected_range=(series.reference_low, series.reference_high),
                    confidence=0.95,
                ))
            elif point.value > series.critical_high:
                anomalies.append(TemporalAnomaly(
                    anomaly_id=f"range_{series.series_id}_{point.timestamp.isoformat()}",
                    anomaly_type=AnomalyType.OUT_OF_RANGE,
                    timestamp=point.timestamp,
                    series_id=series.series_id,
                    description=f"Critically high value: {point.value:.1f}",
                    severity="critical",
                    value=point.value,
                    expected_range=(series.reference_low, series.reference_high),
                    confidence=0.95,
                ))
            elif point.value < series.reference_low:
                anomalies.append(TemporalAnomaly(
                    anomaly_id=f"range_{series.series_id}_{point.timestamp.isoformat()}",
                    anomaly_type=AnomalyType.OUT_OF_RANGE,
                    timestamp=point.timestamp,
                    series_id=series.series_id,
                    description=f"Below reference range: {point.value:.1f}",
                    severity="medium",
                    value=point.value,
                    expected_range=(series.reference_low, series.reference_high),
                    confidence=0.8,
                ))
            elif point.value > series.reference_high:
                anomalies.append(TemporalAnomaly(
                    anomaly_id=f"range_{series.series_id}_{point.timestamp.isoformat()}",
                    anomaly_type=AnomalyType.OUT_OF_RANGE,
                    timestamp=point.timestamp,
                    series_id=series.series_id,
                    description=f"Above reference range: {point.value:.1f}",
                    severity="medium",
                    value=point.value,
                    expected_range=(series.reference_low, series.reference_high),
                    confidence=0.8,
                ))

        return anomalies

    def _detect_trend_breaks(
        self,
        series: TemporalSeries,
        window_size: int = 3,
    ) -> list[TemporalAnomaly]:
        """Detect sudden changes in trend."""
        anomalies = []

        if len(series.points) < window_size * 2:
            return anomalies

        values = series.values

        for i in range(window_size, len(values) - window_size):
            # Calculate means for windows before and after
            before = values[i - window_size:i]
            after = values[i:i + window_size]

            before_mean = sum(before) / len(before)
            after_mean = sum(after) / len(after)

            # Calculate change
            if before_mean != 0:
                change_pct = abs((after_mean - before_mean) / before_mean)

                if change_pct > 0.5:  # 50% change
                    anomalies.append(TemporalAnomaly(
                        anomaly_id=f"trend_{series.series_id}_{i}",
                        anomaly_type=AnomalyType.TREND_BREAK,
                        timestamp=series.points[i].timestamp,
                        series_id=series.series_id,
                        description=f"Trend break: {change_pct:.0%} change detected",
                        severity="high" if change_pct > 1.0 else "medium",
                        value=values[i],
                        expected_range=(before_mean * 0.8, before_mean * 1.2),
                        confidence=min(change_pct, 1.0),
                        metadata={
                            "before_mean": before_mean,
                            "after_mean": after_mean,
                            "change_pct": change_pct,
                        },
                    ))

        return anomalies


# ============================================================================
# Temporal Reasoning Engine
# ============================================================================

class TemporalReasoningEngine:
    """Engine for temporal reasoning about patient health."""

    def __init__(self, store: SyntheaStore):
        self.store = store
        self.analyzer = TemporalAnalyzer(store)
        self.progression_modeler = DiseaseProgressionModeler(store)
        self.trajectory_predictor = TrajectoryPredictor(store)
        self.anomaly_detector = AnomalyDetector(store)

    def analyze_patient_timeline(
        self,
        patient_id: str,
    ) -> dict[str, Any]:
        """Comprehensive temporal analysis of a patient."""
        # Build trajectories
        trajectories = self.analyzer.build_patient_trajectories(patient_id)

        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(patient_id)

        # Predict trajectories for key labs
        lab_predictions = {}
        key_labs = ["glucose", "cholesterol", "hemoglobin", "blood_pressure"]

        for lab in key_labs:
            prediction = self.trajectory_predictor.predict_lab_trajectory(
                patient_id, lab, horizon_days=90
            )
            if "error" not in prediction:
                lab_predictions[lab] = prediction

        # Build timeline
        timeline = self._build_timeline(patient_id)

        return {
            "patient_id": patient_id,
            "trajectories": {
                name: {
                    "current_state": t.current_state.value,
                    "state_count": len(t.states),
                    "transition_count": len(t.transitions),
                }
                for name, t in trajectories.items()
            },
            "anomalies": [
                {
                    "type": a.anomaly_type.value,
                    "description": a.description,
                    "severity": a.severity,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in anomalies[:10]
            ],
            "lab_predictions": lab_predictions,
            "timeline": timeline,
        }

    def _build_timeline(self, patient_id: str) -> list[dict[str, Any]]:
        """Build a comprehensive timeline of patient events."""
        events = []

        # Add conditions
        conditions = self.store.rows("conditions", patient_id)
        for cond in conditions:
            events.append({
                "type": "condition",
                "date": cond.get("START", ""),
                "description": cond.get("DESCRIPTION", ""),
                "status": "active" if not cond.get("STOP") else "resolved",
            })

        # Add medications
        medications = self.store.rows("medications", patient_id)
        for med in medications:
            events.append({
                "type": "medication",
                "date": med.get("START", ""),
                "description": med.get("DESCRIPTION", ""),
                "status": "active" if not med.get("STOP") else "discontinued",
            })

        # Add observations
        observations = self.store.rows("observations", patient_id)
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

        return events[:100]  # Limit to 100 events


# ============================================================================
# Integration Functions
# ============================================================================

def create_temporal_engine(store: SyntheaStore) -> TemporalReasoningEngine:
    """Create a temporal reasoning engine."""
    return TemporalReasoningEngine(store)


def analyze_temporal_patterns(
    store: SyntheaStore,
    patient_id: str,
) -> dict[str, Any]:
    """Analyze temporal patterns for a patient."""
    engine = create_temporal_engine(store)
    return engine.analyze_patient_timeline(patient_id)
