from __future__ import annotations

from typing import Any

from .store import SyntheaStore
from .tools import ToolCategory, tool_registry

# ---------------------------------------------------------------------------
# Data Access Tools
# ---------------------------------------------------------------------------

@tool_registry.tool(
    name="get_patient_record",
    description="Retrieve a patient's demographic and basic information by patient ID.",
    category=ToolCategory.DATA_ACCESS,
    returns="dict with patient demographics (name, gender, birthdate, race, ethnicity, address)",
    examples=[
        {"input": {"patient_id": "abc-123"}, "output": {"FIRST": "John", "LAST": "Doe", "GENDER": "M", "BIRTHDATE": "1970-01-01"}},
    ],
)
def get_patient_record(patient_id: str) -> dict[str, Any]:
    store = SyntheaStore()
    store.load()
    patient = store.patient(patient_id)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")
    return patient


@tool_registry.tool(
    name="get_patient_conditions",
    description="Retrieve all medical conditions/diagnoses for a patient, including onset and resolution dates.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of condition records with CODE, DESCRIPTION, START, STOP",
    examples=[
        {"input": {"patient_id": "abc-123"}, "output": [{"DESCRIPTION": "Hypertension", "START": "2020-01-01", "CODE": "38341003"}]},
    ],
)
def get_patient_conditions(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("conditions", patient_id)


@tool_registry.tool(
    name="get_patient_medications",
    description="Retrieve all medications for a patient, including start/stop dates and reason for prescription.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of medication records with DESCRIPTION, START, STOP, REASONDESCRIPTION",
)
def get_patient_medications(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("medications", patient_id)


@tool_registry.tool(
    name="get_patient_observations",
    description="Retrieve lab results and clinical observations for a patient. Includes vital signs, lab values, and measurements.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of observation records with DESCRIPTION, VALUE, UNITS, DATE",
)
def get_patient_observations(patient_id: str, limit: int = 100) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    rows = store.rows("observations", patient_id)
    return rows[:limit]


@tool_registry.tool(
    name="get_patient_encounters",
    description="Retrieve all healthcare encounters/visits for a patient, including type and dates.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of encounter records with DESCRIPTION, ENCOUNTERCLASS, START, STOP",
)
def get_patient_encounters(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("encounters", patient_id)


@tool_registry.tool(
    name="get_patient_procedures",
    description="Retrieve all medical procedures performed on a patient.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of procedure records with DESCRIPTION, DATE, CODE",
)
def get_patient_procedures(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("procedures", patient_id)


@tool_registry.tool(
    name="get_patient_allergies",
    description="Retrieve all known allergies for a patient.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of allergy records with DESCRIPTION, CODE",
)
def get_patient_allergies(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("allergies", patient_id)


@tool_registry.tool(
    name="get_patient_careplans",
    description="Retrieve care plans for a patient, including goals and activities.",
    category=ToolCategory.DATA_ACCESS,
    returns="list of careplan records with DESCRIPTION, START, STOP, REASONDESCRIPTION",
)
def get_patient_careplans(patient_id: str) -> list[dict[str, Any]]:
    store = SyntheaStore()
    store.load()
    return store.rows("careplans", patient_id)


# ---------------------------------------------------------------------------
# Knowledge Graph Tools
# ---------------------------------------------------------------------------

@tool_registry.tool(
    name="find_related_conditions",
    description="Find conditions that are clinically related to a given condition through shared patients, medications, or procedures.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="list of related condition descriptions with relationship type",
)
def find_related_conditions(condition_description: str, patient_id: str | None = None) -> list[dict[str, Any]]:
    from .knowledge_graph import build_knowledge_graph

    store = SyntheaStore()
    store.load()
    kg = build_knowledge_graph(store)

    # Find condition nodes matching the description
    matching_nodes = kg.query(node_type="condition", description=condition_description)
    if not matching_nodes:
        # Try partial match
        for node in kg.query(node_type="condition"):
            if condition_description.lower() in node.properties.get("description", "").lower():
                matching_nodes.append(node)

    related = []
    for node in matching_nodes[:3]:  # Limit to top 3
        related_conditions = kg.find_related_conditions(node.id)
        for rc in related_conditions[:5]:
            related.append({
                "condition": rc.properties.get("description", ""),
                "code": rc.properties.get("code", ""),
                "relationship": "co-occurring",
            })

    return related


@tool_registry.tool(
    name="find_condition_medication_correlations",
    description="Find which medications are commonly prescribed for a given condition based on patient data patterns.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="list of medications with correlation strength",
)
def find_condition_medication_correlations(condition_description: str) -> list[dict[str, Any]]:
    from .knowledge_graph import build_knowledge_graph

    store = SyntheaStore()
    store.load()
    kg = build_knowledge_graph(store)

    correlation = kg.get_condition_medication_correlation()

    # Find matching condition
    matching_condition_id = None
    for node in kg.query(node_type="condition"):
        if condition_description.lower() in node.properties.get("description", "").lower():
            matching_condition_id = node.id
            break

    if not matching_condition_id or matching_condition_id not in correlation:
        return []

    medication_ids = correlation[matching_condition_id]
    results = []
    for med_id in medication_ids[:10]:
        med_node = kg.get_node(med_id)
        if med_node:
            results.append({
                "medication": med_node.properties.get("description", ""),
                "code": med_node.properties.get("code", ""),
            })

    return results


@tool_registry.tool(
    name="get_patient_clinical_graph",
    description="Get a patient's clinical knowledge graph showing relationships between conditions, medications, and procedures.",
    category=ToolCategory.KNOWLEDGE_GRAPH,
    returns="dict with nodes and edges representing the patient's clinical graph",
)
def get_patient_clinical_graph(patient_id: str) -> dict[str, Any]:
    from .knowledge_graph import build_knowledge_graph

    store = SyntheaStore()
    store.load()
    kg = build_knowledge_graph(store)

    subgraph = kg.get_subgraph(patient_id, depth=2)
    return subgraph.to_dict()


# ---------------------------------------------------------------------------
# Evidence Retrieval Tools
# ---------------------------------------------------------------------------

@tool_registry.tool(
    name="search_patient_evidence",
    description="Search for clinical evidence in a patient's record using hybrid retrieval (keyword + semantic). Returns relevant snippets ranked by relevance.",
    category=ToolCategory.EVIDENCE_RETRIEVAL,
    returns="list of evidence items with snippet, source, relevance_score",
)
def search_patient_evidence(query: str, patient_id: str) -> list[dict[str, Any]]:
    from .evidence import HybridRetriever

    store = SyntheaStore()
    store.load()
    retriever = HybridRetriever(store, patient_id=patient_id)
    result = retriever.retrieve(query, patient_id=patient_id)

    return [
        {
            "snippet": item.snippet,
            "source": item.source,
            "source_id": item.source_id,
            "relevance_score": round(item.relevance_score, 3),
        }
        for item in result.evidence[:20]
    ]


# ---------------------------------------------------------------------------
# Clinical Reasoning Tools
# ---------------------------------------------------------------------------

@tool_registry.tool(
    name="assess_patient_risks",
    description="Assess clinical risks for a patient including diabetes, cardiovascular, and readmission risk scores.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="list of risk assessments with type, score, level, factors, and recommendations",
)
def assess_patient_risks(patient_id: str) -> list[dict[str, Any]]:
    from .predictive import PredictiveAnalyticsEngine

    store = SyntheaStore()
    store.load()
    engine = PredictiveAnalyticsEngine()
    risks = engine.assess_risks(store, patient_id)

    return [
        {
            "risk_type": r.risk_type,
            "score": round(r.score, 3),
            "risk_level": r.risk_level,
            "factors": r.factors,
            "recommendations": r.recommendations,
            "confidence": round(r.confidence, 3),
        }
        for r in risks
    ]


@tool_registry.tool(
    name="check_drug_interactions",
    description="Check for drug-drug interactions and polypharmacy risks for a patient's current medications.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with interactions, duplicate therapies, high-risk meds, and recommendations",
)
def check_drug_interactions(patient_id: str) -> dict[str, Any]:
    from .drug_interactions import PolypharmacyAnalyzer

    store = SyntheaStore()
    store.load()
    analyzer = PolypharmacyAnalyzer()
    risk = analyzer.analyze(store, patient_id)

    return {
        "medication_count": risk.medication_count,
        "risk_level": risk.risk_level,
        "risk_score": round(risk.risk_score, 3),
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
        "duplicate_therapies": risk.duplicate_therapies,
        "high_risk_medications": risk.high_risk_medications,
        "recommendations": risk.recommendations,
        "deprescribing_candidates": risk.deprescribing_candidates,
    }


@tool_registry.tool(
    name="match_clinical_trials",
    description="Find clinical trials that a patient may be eligible for based on their conditions and demographics.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="list of trial matches with eligibility status, confidence, and reasons",
)
def match_clinical_trials(patient_id: str) -> list[dict[str, Any]]:
    from .clinical_trials import ClinicalTrialMatcher

    store = SyntheaStore()
    store.load()
    matcher = ClinicalTrialMatcher()
    matches = matcher.match_trials(store, patient_id)

    return [
        {
            "trial_id": m.trial.trial_id,
            "title": m.trial.title,
            "condition": m.trial.condition,
            "phase": m.trial.phase,
            "confidence": round(m.confidence, 3),
            "eligibility_status": m.eligibility_status,
            "match_reasons": m.match_reasons,
            "exclusion_reasons": m.exclusion_reasons,
            "recommendations": m.recommendations,
        }
        for m in matches
    ]


@tool_registry.tool(
    name="forecast_patient_outcome",
    description="Forecast patient outcomes and disease progression based on current conditions and historical patterns.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with risk forecasts, trajectory, and probabilities",
)
def forecast_patient_outcome(patient_id: str, horizon_days: int = 90) -> dict[str, Any]:
    from .evidence import PrognosisEngine

    store = SyntheaStore()
    store.load()

    # Get conditions
    conditions = store.rows("conditions", patient_id)
    condition_names = [c.get("DESCRIPTION", "").lower() for c in conditions if c.get("DESCRIPTION")]

    engine = PrognosisEngine(store)
    return engine.forecast_patient_outcome(patient_id, condition_names, horizon_days=horizon_days)


@tool_registry.tool(
    name="get_lab_analysis",
    description="Analyze lab results against reference ranges, detect trends and anomalies.",
    category=ToolCategory.CLINICAL_REASONING,
    returns="dict with lab analysis including status, trends, and anomalies",
)
def get_lab_analysis(patient_id: str) -> dict[str, Any]:
    from .multimodal import MultiModalEvidenceCollector

    store = SyntheaStore()
    store.load()

    observations = store.rows("observations", patient_id)
    collector = MultiModalEvidenceCollector()

    lab_evidence = collector.collect_lab_evidence(observations)
    temporal_evidence = collector.collect_temporal_evidence(observations)

    return {
        "lab_results": [
            {
                "lab_name": e.metadata.get("lab_name", ""),
                "value": e.raw_value,
                "analysis": e.analysis,
                "confidence": round(e.confidence, 3),
            }
            for e in lab_evidence[:20]
        ],
        "temporal_patterns": [
            {
                "group": e.analysis.get("group", ""),
                "trend": e.analysis.get("trend", {}),
                "anomaly_count": e.analysis.get("anomaly_count", 0),
            }
            for e in temporal_evidence[:10]
        ],
    }


# ---------------------------------------------------------------------------
# Utility Tools
# ---------------------------------------------------------------------------

@tool_registry.tool(
    name="calculate_age",
    description="Calculate a patient's age from their birthdate.",
    category=ToolCategory.DATA_ACCESS,
    returns="int representing age in years",
)
def calculate_age(patient_id: str) -> int:
    from datetime import datetime, timezone

    store = SyntheaStore()
    store.load()
    patient = store.patient(patient_id)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")

    birthdate = patient.get("BIRTHDATE", "")
    if not birthdate:
        raise ValueError("No birthdate found")

    birth_year = int(birthdate.split("-")[0])
    return datetime.now(timezone.utc).year - birth_year


@tool_registry.tool(
    name="get_condition_duration",
    description="Calculate how long a patient has had a specific condition.",
    category=ToolCategory.DATA_ACCESS,
    returns="dict with duration in days and years",
)
def get_condition_duration(patient_id: str, condition_description: str) -> dict[str, Any]:
    from datetime import datetime, timezone

    store = SyntheaStore()
    store.load()
    conditions = store.rows("conditions", patient_id)

    for cond in conditions:
        if condition_description.lower() in cond.get("DESCRIPTION", "").lower():
            start = cond.get("START", "")
            stop = cond.get("STOP", "")

            if start:
                start_date = datetime.strptime(start[:10], "%Y-%m-%d")
                end_date = datetime.now(timezone.utc) if not stop else datetime.strptime(stop[:10], "%Y-%m-%d")
                duration = end_date - start_date
                return {
                    "condition": cond.get("DESCRIPTION", ""),
                    "start": start,
                    "stop": stop or "ongoing",
                    "duration_days": duration.days,
                    "duration_years": round(duration.days / 365.25, 1),
                    "status": "active" if not stop else "resolved",
                }

    raise ValueError(f"Condition '{condition_description}' not found for patient {patient_id}")
