from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClinicalTrial:
    """A clinical trial."""
    trial_id: str
    title: str
    condition: str
    phase: str
    status: str
    eligibility_criteria: dict[str, Any] = field(default_factory=dict)
    exclusion_criteria: list[str] = field(default_factory=list)
    inclusion_criteria: list[str] = field(default_factory=list)
    interventions: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    contact: str = ""
    url: str = ""


@dataclass
class TrialMatch:
    """A match between a patient and a clinical trial."""
    trial: ClinicalTrial
    patient_id: str
    confidence: float  # 0.0 to 1.0
    match_reasons: list[str] = field(default_factory=list)
    exclusion_reasons: list[str] = field(default_factory=list)
    eligibility_status: str = "unknown"  # eligible, ineligible, potentially_eligible
    recommendations: list[str] = field(default_factory=list)


# Sample clinical trials database (subset for demonstration)
CLINICAL_TRIALS = [
    ClinicalTrial(
        trial_id="NCT001",
        title="Type 2 Diabetes Prevention Study",
        condition="Diabetes Mellitus, Type 2",
        phase="Phase 3",
        status="Recruiting",
        eligibility_criteria={"age_min": 30, "age_max": 75, "bmi_min": 25},
        inclusion_criteria=[
            "Diagnosed with type 2 diabetes",
            "HbA1c between 7.0% and 10.0%",
            "Age 30-75 years",
        ],
        exclusion_criteria=[
            "Type 1 diabetes",
            "Severe renal impairment",
            "Pregnancy",
        ],
        interventions=["Metformin", "Lifestyle intervention"],
        locations=["Boston, MA", "New York, NY"],
        contact="diabetes-trial@hospital.org",
    ),
    ClinicalTrial(
        trial_id="NCT002",
        title="Cardiovascular Outcome Trial",
        condition="Cardiovascular Disease",
        phase="Phase 4",
        status="Recruiting",
        eligibility_criteria={"age_min": 40, "age_max": 80},
        inclusion_criteria=[
            "History of cardiovascular events",
            "Stable medication regimen",
            "Age 40-80 years",
        ],
        exclusion_criteria=[
            "Uncontrolled hypertension",
            "Severe heart failure",
            "Recent stroke",
        ],
        interventions=["Statin therapy", "Antiplatelet therapy"],
        locations=["Chicago, IL", "Los Angeles, CA"],
        contact="cv-trial@hospital.org",
    ),
    ClinicalTrial(
        trial_id="NCT003",
        title="Hypertension Management Study",
        condition="Hypertension",
        phase="Phase 2",
        status="Recruiting",
        eligibility_criteria={"age_min": 18, "age_max": 90, "bp_systolic_min": 140},
        inclusion_criteria=[
            "Diagnosed hypertension",
            "Systolic BP >= 140 mmHg",
            "Age 18-90 years",
        ],
        exclusion_criteria=[
            "Secondary hypertension",
            "Severe renal disease",
            "Pregnancy",
        ],
        interventions=["ACE inhibitor", "ARB therapy"],
        locations=["Houston, TX", "Phoenix, AZ"],
        contact="htn-trial@hospital.org",
    ),
    ClinicalTrial(
        trial_id="NCT004",
        title="Cholesterol Lowering Study",
        condition="Hyperlipidemia",
        phase="Phase 3",
        status="Recruiting",
        eligibility_criteria={"age_min": 18, "age_max": 80, "ldl_min": 130},
        inclusion_criteria=[
            "Elevated LDL cholesterol",
            "LDL >= 130 mg/dL",
            "Age 18-80 years",
        ],
        exclusion_criteria=[
            "Statin allergy",
            "Active liver disease",
            "Pregnancy",
        ],
        interventions=["PCSK9 inhibitor", "Statin therapy"],
        locations=["San Francisco, CA", "Seattle, WA"],
        contact="lipid-trial@hospital.org",
    ),
    ClinicalTrial(
        trial_id="NCT005",
        title="Heart Failure Treatment Study",
        condition="Heart Failure",
        phase="Phase 2",
        status="Recruiting",
        eligibility_criteria={"age_min": 18, "age_max": 85},
        inclusion_criteria=[
            "Diagnosed heart failure",
            "EF <= 40%",
            "Age 18-85 years",
        ],
        exclusion_criteria=[
            "Acute decompensated heart failure",
            "Severe valvular disease",
            "Recent cardiac surgery",
        ],
        interventions=["ARNI therapy", "Beta-blocker"],
        locations=["Dallas, TX", "Atlanta, GA"],
        contact="hf-trial@hospital.org",
    ),
]


class ClinicalTrialMatcher:
    """Match patients to clinical trials."""

    def __init__(self, trials: list[ClinicalTrial] | None = None):
        self.trials = trials or CLINICAL_TRIALS

    def match_trials(self, store, patient_id: str) -> list[TrialMatch]:
        """Match a patient to available clinical trials."""
        patient = store.patient(patient_id)
        conditions = store.rows("conditions", patient_id)
        medications = store.rows("medications", patient_id)
        observations = store.rows("observations", patient_id)

        matches = []

        for trial in self.trials:
            match = self._evaluate_trial(patient, conditions, medications, observations, trial)
            if match:
                matches.append(match)

        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches

    def _evaluate_trial(
        self,
        patient: dict[str, Any],
        conditions: list[dict[str, Any]],
        medications: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        trial: ClinicalTrial,
    ) -> TrialMatch | None:
        """Evaluate if a patient matches a trial."""
        match_reasons = []
        exclusion_reasons = []
        confidence = 0.0

        # Check age eligibility
        birthdate = patient.get("BIRTHDATE", "")
        age = None
        if birthdate:
            try:
                birth_year = int(birthdate.split("-")[0])
                age = 2026 - birth_year
            except (ValueError, IndexError):
                pass

        if age is not None:
            age_min = trial.eligibility_criteria.get("age_min", 0)
            age_max = trial.eligibility_criteria.get("age_max", 200)
            if age_min <= age <= age_max:
                match_reasons.append(f"Age {age} within range ({age_min}-{age_max})")
                confidence += 0.2
            else:
                exclusion_reasons.append(f"Age {age} outside range ({age_min}-{age_max})")
                return None

        # Check condition match
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]
        trial_condition = trial.condition.lower()

        condition_matched = False
        for cond in condition_descriptions:
            if any(keyword in cond for keyword in trial_condition.split()):
                condition_matched = True
                match_reasons.append(f"Condition match: {cond}")
                confidence += 0.4
                break

        if not condition_matched:
            # Check for related conditions
            for cond in condition_descriptions:
                if any(keyword in cond for keyword in ["diabetes", "hypertension", "cholesterol", "heart"]):
                    match_reasons.append(f"Related condition: {cond}")
                    confidence += 0.2
                    break

        # Check inclusion criteria
        for criterion in trial.inclusion_criteria:
            criterion_lower = criterion.lower()
            # Check if criterion is met based on patient data
            if self._check_criterion(patient, conditions, observations, criterion_lower):
                match_reasons.append(f"Meets criterion: {criterion}")
                confidence += 0.1

        # Check exclusion criteria
        for criterion in trial.exclusion_criteria:
            criterion_lower = criterion.lower()
            if self._check_exclusion(patient, conditions, criterion_lower):
                exclusion_reasons.append(f"Exclusion: {criterion}")
                confidence -= 0.3

        # Determine eligibility status
        if exclusion_reasons:
            eligibility_status = "ineligible"
        elif confidence >= 0.5:
            eligibility_status = "eligible"
        elif confidence >= 0.3:
            eligibility_status = "potentially_eligible"
        else:
            eligibility_status = "ineligible"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            eligibility_status, match_reasons, exclusion_reasons, trial
        )

        return TrialMatch(
            trial=trial,
            patient_id=patient.get("Id", ""),
            confidence=max(0.0, min(confidence, 1.0)),
            match_reasons=match_reasons,
            exclusion_reasons=exclusion_reasons,
            eligibility_status=eligibility_status,
            recommendations=recommendations,
        )

    def _check_criterion(
        self,
        patient: dict[str, Any],
        conditions: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        criterion: str,
    ) -> bool:
        """Check if a patient meets a criterion."""
        # Check conditions
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]
        for cond in condition_descriptions:
            if any(keyword in cond for keyword in criterion.split()):
                return True

        # Check observations
        for obs in observations:
            desc = obs.get("DESCRIPTION", "").lower()
            if any(keyword in desc for keyword in criterion.split()):
                return True

        return False

    def _check_exclusion(
        self,
        patient: dict[str, Any],
        conditions: list[dict[str, Any]],
        criterion: str,
    ) -> bool:
        """Check if a patient meets an exclusion criterion."""
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]
        for cond in condition_descriptions:
            if any(keyword in cond for keyword in criterion.split()):
                return True
        return False

    def _generate_recommendations(
        self,
        eligibility_status: str,
        match_reasons: list[str],
        exclusion_reasons: list[str],
        trial: ClinicalTrial,
    ) -> list[str]:
        """Generate recommendations based on match analysis."""
        recommendations = []

        if eligibility_status == "eligible":
            recommendations.append(f"Patient appears eligible for {trial.title}")
            recommendations.append(f"Contact: {trial.contact}")
            recommendations.append(f"Locations: {', '.join(trial.locations)}")
        elif eligibility_status == "potentially_eligible":
            recommendations.append(f"Patient may be eligible for {trial.title}")
            recommendations.append("Additional screening may be required")
            recommendations.append(f"Contact: {trial.contact}")
        else:
            recommendations.append(f"Patient does not meet eligibility for {trial.title}")
            if exclusion_reasons:
                recommendations.append(f"Exclusion reasons: {'; '.join(exclusion_reasons)}")

        return recommendations

    def get_high_potential_matches(self, store, patient_id: str) -> list[TrialMatch]:
        """Get trials with high match potential."""
        matches = self.match_trials(store, patient_id)
        return [m for m in matches if m.eligibility_status in ["eligible", "potentially_eligible"]]

    def search_trials_by_condition(self, condition: str) -> list[ClinicalTrial]:
        """Search trials by condition."""
        condition_lower = condition.lower()
        return [
            trial for trial in self.trials
            if condition_lower in trial.condition.lower()
            or any(condition_lower in crit.lower() for crit in trial.inclusion_criteria)
        ]
