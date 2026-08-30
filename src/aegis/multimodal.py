from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceModality(StrEnum):
    """Types of evidence modalities."""
    TEXT = "text"
    NUMERIC = "numeric"
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"


@dataclass
class MultiModalEvidence:
    """Evidence item with modality-specific analysis."""
    source: str
    source_id: str
    modality: EvidenceModality
    raw_value: Any
    processed_value: Any = None
    analysis: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LabResultAnalyzer:
    """Analyzer for laboratory results with reference ranges."""

    # Common lab reference ranges
    REFERENCE_RANGES = {
        "glucose": {"low": 70, "high": 100, "unit": "mg/dL", "critical_low": 54, "critical_high": 250},
        "hba1c": {"low": 4.0, "high": 5.6, "unit": "%", "critical_low": 4.0, "critical_high": 9.0},
        "cholesterol": {"low": 0, "high": 200, "unit": "mg/dL", "critical_low": 0, "critical_high": 300},
        "hdl": {"low": 40, "high": 60, "unit": "mg/dL", "critical_low": 20, "critical_high": 100},
        "ldl": {"low": 0, "high": 100, "unit": "mg/dL", "critical_low": 0, "critical_high": 190},
        "triglycerides": {"low": 0, "high": 150, "unit": "mg/dL", "critical_low": 0, "critical_high": 500},
        "creatinine": {"low": 0.6, "high": 1.2, "unit": "mg/dL", "critical_low": 0.6, "critical_high": 10.0},
        "bun": {"low": 7, "high": 20, "unit": "mg/dL", "critical_low": 7, "critical_high": 100},
        "hemoglobin": {"low": 12.0, "high": 17.5, "unit": "g/dL", "critical_low": 7.0, "critical_high": 20.0},
        "wbc": {"low": 4.5, "high": 11.0, "unit": "K/uL", "critical_low": 2.0, "critical_high": 30.0},
        "platelets": {"low": 150, "high": 400, "unit": "K/uL", "critical_low": 50, "critical_high": 1000},
        "tsh": {"low": 0.4, "high": 4.0, "unit": "mIU/L", "critical_low": 0.1, "critical_high": 10.0},
        "vitamin_d": {"low": 30, "high": 100, "unit": "ng/mL", "critical_low": 10, "critical_high": 150},
        "blood_pressure_systolic": {"low": 90, "high": 120, "unit": "mmHg", "critical_low": 70, "critical_high": 180},
        "blood_pressure_diastolic": {"low": 60, "high": 80, "unit": "mmHg", "critical_low": 40, "critical_high": 120},
        "heart_rate": {"low": 60, "high": 100, "unit": "bpm", "critical_low": 40, "critical_high": 150},
        "temperature": {"low": 97.8, "high": 99.1, "unit": "F", "critical_low": 95.0, "critical_high": 104.0},
        "bmi": {"low": 18.5, "high": 24.9, "unit": "kg/m2", "critical_low": 16.0, "critical_high": 40.0},
    }

    def analyze(self, lab_name: str, value: float, unit: str = "") -> MultiModalEvidence:
        """Analyze a lab result against reference ranges."""
        lab_key = lab_name.lower().replace(" ", "_")
        reference = self.REFERENCE_RANGES.get(lab_key)

        analysis = {
            "value": value,
            "unit": unit or (reference["unit"] if reference else ""),
            "lab_name": lab_name,
        }

        if reference:
            analysis["reference_low"] = reference["low"]
            analysis["reference_high"] = reference["high"]
            analysis["in_range"] = reference["low"] <= value <= reference["high"]

            # Determine status
            if value < reference.get("critical_low", reference["low"]):
                analysis["status"] = "critical_low"
                analysis["severity"] = "critical"
            elif value > reference.get("critical_high", reference["high"]):
                analysis["status"] = "critical_high"
                analysis["severity"] = "critical"
            elif value < reference["low"]:
                analysis["status"] = "low"
                analysis["severity"] = "abnormal"
            elif value > reference["high"]:
                analysis["status"] = "high"
                analysis["severity"] = "abnormal"
            else:
                analysis["status"] = "normal"
                analysis["severity"] = "normal"

            # Calculate percentage from normal
            if value < reference["low"]:
                analysis["percent_from_normal"] = ((reference["low"] - value) / reference["low"]) * 100
            elif value > reference["high"]:
                analysis["percent_from_normal"] = ((value - reference["high"]) / reference["high"]) * 100
            else:
                analysis["percent_from_normal"] = 0.0
        else:
            analysis["status"] = "unknown"
            analysis["severity"] = "unknown"

        confidence = 0.9 if reference else 0.5

        return MultiModalEvidence(
            source="lab_result",
            source_id=lab_key,
            modality=EvidenceModality.NUMERIC,
            raw_value=value,
            processed_value=value,
            analysis=analysis,
            confidence=confidence,
            metadata={"lab_name": lab_name, "unit": unit},
        )


class TemporalAnalyzer:
    """Analyzer for temporal patterns in data."""

    def analyze_trend(self, values: list[dict[str, Any]], value_key: str = "value") -> dict[str, Any]:
        """Analyze trends in temporal data."""
        if not values:
            return {"trend": "insufficient_data", "direction": "unknown"}

        # Extract numeric values
        numeric_values = []
        for v in values:
            val = v.get(value_key)
            if val is not None:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    continue

        if len(numeric_values) < 2:
            return {"trend": "insufficient_data", "direction": "unknown"}

        # Calculate basic statistics
        mean = sum(numeric_values) / len(numeric_values)
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        range_val = max_val - min_val

        # Calculate trend direction
        first_half = numeric_values[:len(numeric_values)//2]
        second_half = numeric_values[len(numeric_values)//2:]

        first_mean = sum(first_half) / len(first_half) if first_half else 0
        second_mean = sum(second_half) / len(second_half) if second_half else 0

        if second_mean > first_mean * 1.1:
            direction = "increasing"
        elif second_mean < first_mean * 0.9:
            direction = "decreasing"
        else:
            direction = "stable"

        # Calculate volatility
        if len(numeric_values) > 1:
            differences = [abs(numeric_values[i+1] - numeric_values[i]) for i in range(len(numeric_values)-1)]
            volatility = sum(differences) / len(differences)
        else:
            volatility = 0

        return {
            "trend": "analyzed",
            "direction": direction,
            "mean": mean,
            "min": min_val,
            "max": max_val,
            "range": range_val,
            "volatility": volatility,
            "data_points": len(numeric_values),
            "first_mean": first_mean,
            "second_mean": second_mean,
        }

    def detect_anomalies(
        self,
        values: list[dict[str, Any]],
        value_key: str = "value",
        threshold: float = 2.0,
    ) -> list[dict[str, Any]]:
        """Detect anomalies using z-score method."""
        if not values:
            return []

        # Extract numeric values
        numeric_values = []
        for v in values:
            val = v.get(value_key)
            if val is not None:
                try:
                    numeric_values.append((float(val), v))
                except (ValueError, TypeError):
                    continue

        if len(numeric_values) < 3:
            return []

        # Calculate mean and standard deviation
        vals = [v[0] for v in numeric_values]
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return []

        # Detect anomalies
        anomalies = []
        for val, data in numeric_values:
            z_score = abs((val - mean) / std_dev)
            if z_score > threshold:
                anomalies.append({
                    "value": val,
                    "z_score": z_score,
                    "mean": mean,
                    "std_dev": std_dev,
                    "data": data,
                })

        return anomalies


class MultiModalEvidenceCollector:
    """Collector for multi-modal evidence from patient data."""

    def __init__(self):
        self.lab_analyzer = LabResultAnalyzer()
        self.temporal_analyzer = TemporalAnalyzer()

    def collect_lab_evidence(
        self,
        observations: list[dict[str, Any]],
    ) -> list[MultiModalEvidence]:
        """Collect and analyze lab results."""
        evidence = []

        for obs in observations:
            description = obs.get("DESCRIPTION", "")
            value = obs.get("VALUE")
            unit = obs.get("UNITS", "")

            if value is not None:
                try:
                    numeric_value = float(value)
                    lab_evidence = self.lab_analyzer.analyze(description, numeric_value, unit)
                    evidence.append(lab_evidence)
                except (ValueError, TypeError):
                    # Non-numeric observation
                    evidence.append(MultiModalEvidence(
                        source="observation",
                        source_id=str(obs.get("Id", "")),
                        modality=EvidenceModality.TEXT,
                        raw_value=value,
                        processed_value=str(value),
                        analysis={"description": description, "value": str(value)},
                        confidence=0.7,
                    ))

        return evidence

    def collect_temporal_evidence(
        self,
        observations: list[dict[str, Any]],
        group_by: str = "DESCRIPTION",
    ) -> list[MultiModalEvidence]:
        """Collect temporal evidence by grouping observations."""
        evidence = []

        # Group observations by type
        groups: dict[str, list[dict[str, Any]]] = {}
        for obs in observations:
            key = obs.get(group_by, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(obs)

        # Analyze each group
        for group_key, group_observations in groups.items():
            if len(group_observations) < 2:
                continue

            # Sort by date
            group_observations.sort(key=lambda x: x.get("DATE", ""))

            # Analyze trend
            trend_analysis = self.temporal_analyzer.analyze_trend(group_observations, "VALUE")

            # Detect anomalies
            anomalies = self.temporal_analyzer.detect_anomalies(group_observations, "VALUE")

            evidence.append(MultiModalEvidence(
                source="temporal_analysis",
                source_id=group_key,
                modality=EvidenceModality.TEMPORAL,
                raw_value=group_observations,
                processed_value={
                    "trend": trend_analysis,
                    "anomalies": anomalies,
                    "data_points": len(group_observations),
                },
                analysis={
                    "group": group_key,
                    "trend": trend_analysis,
                    "anomaly_count": len(anomalies),
                },
                confidence=0.8 if len(group_observations) >= 5 else 0.6,
            ))

        return evidence

    def collect_all_evidence(
        self,
        store,
        patient_id: str,
    ) -> list[MultiModalEvidence]:
        """Collect all multi-modal evidence for a patient."""
        evidence = []

        # Get observations
        observations = store.rows("observations", patient_id)

        # Collect lab evidence
        lab_evidence = self.collect_lab_evidence(observations)
        evidence.extend(lab_evidence)

        # Collect temporal evidence
        temporal_evidence = self.collect_temporal_evidence(observations)
        evidence.extend(temporal_evidence)

        return evidence
