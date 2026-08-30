"""
Temporal Reasoning Agent - LLM-Powered Temporal Analysis

This agent uses the Temporal Intelligence Engine to reason about
disease progression, trajectory prediction, and anomaly detection.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .llm import LLMProvider
from .reasoning_agents import AgentConclusion, ReasoningAgent, ReasoningStep
from .store import SyntheaStore
from .temporal import (
    AnomalyDetector,
    DiseaseProgressionModeler,
    TemporalAnalyzer,
    TemporalReasoningEngine,
    TrajectoryPredictor,
)
from .tools import ToolCategory, tool_registry

# ============================================================================
# Temporal Tools
# ============================================================================

@tool_registry.tool(
    name="analyze_temporal_patterns",
    description="Analyze temporal patterns in patient health data: disease progression, lab trends, anomalies over time.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with temporal analysis including trajectories, anomalies, and predictions",
)
def analyze_temporal_patterns(patient_id: str) -> dict[str, Any]:
    """Analyze temporal patterns for a patient."""
    store = SyntheaStore()
    store.load()

    engine = TemporalReasoningEngine(store)
    return engine.analyze_patient_timeline(patient_id)


@tool_registry.tool(
    name="predict_disease_progression",
    description="Predict disease progression for a patient based on historical patterns and risk factors.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with progression predictions and confidence scores",
)
def predict_disease_progression(
    patient_id: str,
    condition: str,
    horizon_days: int = 365,
) -> dict[str, Any]:
    """Predict disease progression."""
    store = SyntheaStore()
    store.load()

    modeler = DiseaseProgressionModeler(store)
    return modeler.predict_progression(patient_id, condition, horizon_days)


@tool_registry.tool(
    name="predict_lab_trajectory",
    description="Predict future lab values based on historical trends. Useful for monitoring chronic conditions.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with predicted values and trend analysis",
)
def predict_lab_trajectory(
    patient_id: str,
    lab_name: str,
    horizon_days: int = 90,
) -> dict[str, Any]:
    """Predict lab trajectory."""
    store = SyntheaStore()
    store.load()

    predictor = TrajectoryPredictor(store)
    return predictor.predict_lab_trajectory(patient_id, lab_name, horizon_days)


@tool_registry.tool(
    name="detect_temporal_anomalies",
    description="Detect anomalies in patient's temporal data: sudden changes, out-of-range values, trend breaks.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with detected anomalies and their severity",
)
def detect_temporal_anomalies(
    patient_id: str,
    lab_name: str | None = None,
) -> dict[str, Any]:
    """Detect temporal anomalies."""
    store = SyntheaStore()
    store.load()

    detector = AnomalyDetector(store)
    anomalies = detector.detect_anomalies(patient_id, lab_name)

    return {
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
    }


@tool_registry.tool(
    name="build_patient_timeline",
    description="Build a comprehensive timeline of patient health events: conditions, medications, observations.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with chronological health events",
)
def build_patient_timeline(patient_id: str) -> dict[str, Any]:
    """Build patient timeline."""
    store = SyntheaStore()
    store.load()

    # Build timeline from conditions, medications, observations
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

    return {
        "patient_id": patient_id,
        "events": events[:100],
        "event_count": len(events),
    }


@tool_registry.tool(
    name="get_health_state_transitions",
    description="Get health state transitions for a patient: how their health has changed over time.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with state transitions and durations",
)
def get_health_state_transitions(patient_id: str) -> dict[str, Any]:
    """Get health state transitions."""
    store = SyntheaStore()
    store.load()

    analyzer = TemporalAnalyzer(store)
    trajectories = analyzer.build_patient_trajectories(patient_id)

    return {
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
    }


# ============================================================================
# Temporal Reasoning Agent
# ============================================================================

class TemporalReasoningAgent(ReasoningAgent):
    """Agent specialized in temporal reasoning about patient health.

    This agent uses the Temporal Intelligence Engine to:

    1. **Disease Progression**: Model how conditions evolve over time
    2. **Trajectory Prediction**: Forecast future health states
    3. **Anomaly Detection**: Identify unusual temporal patterns
    4. **Timeline Analysis**: Understand temporal relationships between events
    5. **Trend Analysis**: Identify improving/worsening patterns

    This is CLINICALLY DIFFERENTIATED because it reasons about TIME,
    not just snapshots of patient data.
    """

    name = "temporal_reasoning"
    role = "temporal clinical analyst"
    description = "Analyzes disease progression, predicts trajectories, and detects temporal anomalies"

    def __init__(
        self,
        llm: LLMProvider | None = None,
        store: SyntheaStore | None = None,
    ):
        self.store = store or SyntheaStore()
        self.store.load()

        self.engine = TemporalReasoningEngine(self.store)
        self.analyzer = TemporalAnalyzer(self.store)
        self.progression_modeler = DiseaseProgressionModeler(self.store)
        self.trajectory_predictor = TrajectoryPredictor(self.store)
        self.anomaly_detector = AnomalyDetector(self.store)

        super().__init__(llm=llm)

    def get_system_prompt(self) -> str:
        return """You are an expert temporal clinical analyst. Your unique capability
is reasoning about how patient health evolves OVER TIME.

Your approach:
1. **Disease Progression**: Model how conditions evolve (acute → chronic → recovery)
2. **Trajectory Prediction**: Forecast future health states based on trends
3. **Anomaly Detection**: Identify sudden changes, out-of-range values, trend breaks
4. **Timeline Analysis**: Understand temporal relationships between events
5. **Trend Analysis**: Identify improving/worsening patterns in lab values

Key principles:
- Consider temporal ordering of events
- Look for patterns in how health states change over time
- Predict future trajectories based on historical patterns
- Detect anomalies that may indicate clinical significance
- Understand clinical time concepts (acute, chronic, recovery)

You are analyzing SYNTHETIC patient data for research purposes only.
This is NOT medical advice and should NOT be used for clinical decisions."""

    def get_available_tools(self) -> list[str]:
        return [
            "get_patient_record",
            "get_patient_conditions",
            "get_patient_observations",
            "get_patient_medications",
            "analyze_temporal_patterns",
            "predict_disease_progression",
            "predict_lab_trajectory",
            "detect_temporal_anomalies",
            "build_patient_timeline",
            "get_health_state_transitions",
        ]

    async def investigate(self, patient_id: str, question: str) -> AgentConclusion:
        """Run a temporal investigation."""
        start_time = perf_counter()
        self._reasoning_chain = []
        self._tool_call_count = 0

        # Step 1: Analyze temporal patterns
        temporal_analysis = self.engine.analyze_patient_timeline(patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Temporal analysis: {len(temporal_analysis.get('trajectories', {}))} trajectories, "
                    f"{len(temporal_analysis.get('anomalies', []))} anomalies",
            confidence=0.9,
        ))

        # Step 2: Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(patient_id)

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Detected {len(anomalies)} anomalies in patient data",
            confidence=0.8,
        ))

        # Step 3: Predict trajectories for key labs
        predictions = {}
        key_labs = ["glucose", "cholesterol", "hemoglobin"]

        for lab in key_labs:
            prediction = self.trajectory_predictor.predict_lab_trajectory(
                patient_id, lab, horizon_days=90
            )
            if "error" not in prediction:
                predictions[lab] = prediction

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Generated predictions for {len(predictions)} lab trajectories",
            confidence=0.7,
        ))

        # Step 4: Build timeline
        timeline = temporal_analysis.get("timeline", [])

        self._reasoning_chain.append(ReasoningStep(
            thought=f"Timeline: {len(timeline)} events",
            confidence=0.9,
        ))

        # Generate conclusion
        evidence_texts = []

        # Add trajectory information
        for name, traj_info in temporal_analysis.get("trajectories", {}).items():
            evidence_texts.append(
                f"[Trajectory] {name}: current state = {traj_info.get('current_state', 'unknown')}"
            )

        # Add anomalies
        for anomaly in anomalies[:5]:
            evidence_texts.append(
                f"[Anomaly: {anomaly.severity}] {anomaly.description}"
            )

        # Add predictions
        for lab, pred in predictions.items():
            trend = pred.get("trend", "unknown")
            evidence_texts.append(
                f"[Prediction] {lab}: trend = {trend}"
            )

        # Calculate confidence
        confidence = 0.6
        if anomalies:
            confidence = min(confidence + len(anomalies) * 0.05, 0.9)
        if predictions:
            confidence = min(confidence + 0.1, 0.9)

        conclusion = AgentConclusion(
            summary=self._generate_summary(
                patient_id, temporal_analysis, anomalies, predictions
            ),
            key_findings=self._extract_key_findings(
                temporal_analysis, anomalies, predictions
            ),
            evidence=evidence_texts,
            confidence=confidence,
            uncertainties=self._identify_uncertainties(temporal_analysis),
            recommendations=self._generate_recommendations(anomalies, predictions),
            reasoning_chain=self._reasoning_chain,
        )

        duration_ms = (perf_counter() - start_time) * 1000
        conclusion.reasoning_chain.insert(0, ReasoningStep(
            thought=f"Temporal reasoning completed in {duration_ms:.0f}ms",
            confidence=1.0,
        ))

        return conclusion

    def _generate_summary(
        self,
        patient_id: str,
        temporal_analysis: dict,
        anomalies: list,
        predictions: dict,
    ) -> str:
        """Generate summary of temporal analysis."""
        parts = []

        parts.append(f"Temporal analysis for patient {patient_id[:8]}...")

        trajectories = temporal_analysis.get("trajectories", {})
        if trajectories:
            parts.append(f"Tracking {len(trajectories)} health trajectories.")

        if anomalies:
            severity_counts = {}
            for a in anomalies:
                severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
            parts.append(f"Detected {len(anomalies)} anomalies: {severity_counts}")

        if predictions:
            parts.append(f"Generated predictions for {len(predictions)} lab values.")

        return " ".join(parts)

    def _extract_key_findings(
        self,
        temporal_analysis: dict,
        anomalies: list,
        predictions: dict,
    ) -> list[str]:
        """Extract key findings."""
        findings = []

        # Trajectory findings
        for name, traj in temporal_analysis.get("trajectories", {}).items():
            findings.append(
                f"{name}: {traj.get('current_state', 'unknown')} state"
            )

        # Anomaly findings
        for anomaly in anomalies[:3]:
            findings.append(
                f"Anomaly: {anomaly.description[:50]}"
            )

        # Prediction findings
        for lab, pred in predictions.items():
            findings.append(
                f"{lab}: {pred.get('trend', 'unknown')} trend"
            )

        return findings[:10]

    def _identify_uncertainties(self, temporal_analysis: dict) -> list[str]:
        """Identify uncertainties."""
        uncertainties = []

        if not temporal_analysis.get("trajectories"):
            uncertainties.append("No disease trajectories found")

        if not temporal_analysis.get("lab_predictions"):
            uncertainties.append("Limited lab data for predictions")

        return uncertainties

    def _generate_recommendations(
        self,
        anomalies: list,
        predictions: dict,
    ) -> list[str]:
        """Generate recommendations."""
        recommendations = []

        if anomalies:
            recommendations.append("Review detected anomalies for clinical significance")

        if predictions:
            recommendations.append("Monitor predicted lab trajectories")

        recommendations.append("Continue temporal monitoring for trend detection")

        return recommendations
