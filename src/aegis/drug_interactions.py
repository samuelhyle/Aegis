from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DrugInteraction:
    """A drug-drug interaction."""
    drug1: str
    drug2: str
    severity: str  # minor, moderate, major, contraindicated
    description: str
    clinical_effect: str
    management: str
    evidence_level: str  # high, moderate, low
    sources: list[str] = field(default_factory=list)


@dataclass
class PolypharmacyRisk:
    """Polypharmacy risk assessment for a patient."""
    patient_id: str
    medication_count: int
    risk_level: str  # low, moderate, high, very_high
    risk_score: float  # 0.0 to 1.0
    interactions: list[DrugInteraction] = field(default_factory=list)
    duplicate_therapies: list[dict[str, Any]] = field(default_factory=list)
    high_risk_medications: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    deprescribing_candidates: list[dict[str, Any]] = field(default_factory=list)


# Common drug interaction database (subset for demonstration)
DRUG_INTERACTIONS = {
    ("warfarin", "aspirin"): DrugInteraction(
        drug1="warfarin",
        drug2="aspirin",
        severity="major",
        description="Increased risk of bleeding",
        clinical_effect="Enhanced anticoagulant effect, increased bleeding risk",
        management="Monitor INR closely, watch for signs of bleeding",
        evidence_level="high",
        sources=["DrugBank", "FDA"],
    ),
    ("warfarin", "ibuprofen"): DrugInteraction(
        drug1="warfarin",
        drug2="ibuprofen",
        severity="major",
        description="Increased risk of GI bleeding",
        clinical_effect="NSAIDs increase anticoagulant effect and GI bleeding risk",
        management="Avoid combination if possible, use acetaminophen instead",
        evidence_level="high",
        sources=["DrugBank"],
    ),
    ("metformin", "contrast_dye"): DrugInteraction(
        drug1="metformin",
        drug2="contrast_dye",
        severity="major",
        description="Risk of lactic acidosis",
        clinical_effect="Contrast dye may impair renal function, leading to metformin accumulation",
        management="Hold metformin 48 hours after contrast administration",
        evidence_level="high",
        sources=["ACR", "FDA"],
    ),
    ("lisinopril", "potassium"): DrugInteraction(
        drug1="lisinopril",
        drug2="potassium",
        severity="moderate",
        description="Risk of hyperkalemia",
        clinical_effect="ACE inhibitors increase potassium levels, potassium supplements compound this",
        management="Monitor serum potassium regularly",
        evidence_level="high",
        sources=["DrugBank"],
    ),
    ("simvastatin", "amiodarone"): DrugInteraction(
        drug1="simvastatin",
        drug2="amiodarone",
        severity="major",
        description="Increased risk of rhabdomyolysis",
        clinical_effect="Amiodarone inhibits simvastatin metabolism, increasing statin levels",
        management="Limit simvastatin dose to 20mg/day",
        evidence_level="high",
        sources=["FDA"],
    ),
    ("clopidogrel", "omeprazole"): DrugInteraction(
        drug1="clopidogrel",
        drug2="omeprazole",
        severity="moderate",
        description="Reduced antiplatelet effect",
        clinical_effect="Omeprazole inhibits CYP2C19, reducing clopidogrel activation",
        management="Use pantoprazole instead of omeprazole",
        evidence_level="moderate",
        sources=["FDA"],
    ),
    ("ssri", "maoi"): DrugInteraction(
        drug1="ssri",
        drug2="maoi",
        severity="contraindicated",
        description="Risk of serotonin syndrome",
        clinical_effect="Combined serotonergic effects can cause life-threatening serotonin syndrome",
        management="Do not combine. Allow 14-day washout between agents",
        evidence_level="high",
        sources=["FDA", "DrugBank"],
    ),
    ("methotrexate", "nsaid"): DrugInteraction(
        drug1="methotrexate",
        drug2="nsaid",
        severity="major",
        description="Increased methotrexate toxicity",
        clinical_effect="NSAIDs reduce renal clearance of methotrexate",
        management="Monitor for methotrexate toxicity, consider dose adjustment",
        evidence_level="high",
        sources=["DrugBank"],
    ),
    ("digoxin", "amiodarone"): DrugInteraction(
        drug1="digoxin",
        drug2="amiodarone",
        severity="major",
        description="Increased digoxin levels",
        clinical_effect="Amiodarone increases digoxin concentration by 70-100%",
        management="Reduce digoxin dose by 50%, monitor levels",
        evidence_level="high",
        sources=["DrugBank", "FDA"],
    ),
    ("lithium", "ace_inhibitor"): DrugInteraction(
        drug1="lithium",
        drug2="ace_inhibitor",
        severity="major",
        description="Increased lithium toxicity",
        clinical_effect="ACE inhibitors reduce lithium clearance",
        management="Monitor lithium levels closely, adjust dose as needed",
        evidence_level="high",
        sources=["DrugBank"],
    ),
}

# High-risk medication categories
HIGH_RISK_MEDICATIONS = {
    "anticoagulants": {
        "medications": ["warfarin", "heparin", "enoxaparin", "rivaroxaban", "apixaban"],
        "risks": ["bleeding", "bruising", "hemorrhage"],
        "monitoring": ["INR", "aPTT", "anti-Xa levels"],
    },
    "insulin": {
        "medications": ["insulin", "insulin glargine", "insulin lispro", "insulin aspart"],
        "risks": ["hypoglycemia", "hyperglycemia"],
        "monitoring": ["blood glucose", "HbA1c"],
    },
    "opioids": {
        "medications": ["morphine", "oxycodone", "hydrocodone", "fentanyl", "tramadol"],
        "risks": ["respiratory depression", "sedation", "constipation", "dependence"],
        "monitoring": ["pain scores", "respiratory rate", "sedation level"],
    },
    "immunosuppressants": {
        "medications": ["tacrolimus", "cyclosporine", "mycophenolate", "azathioprine"],
        "risks": ["infection", "nephrotoxicity", "hepatotoxicity"],
        "monitoring": ["drug levels", "CBC", "renal function", "LFTs"],
    },
    "antiarrhythmics": {
        "medications": ["amiodarone", "flecainide", "propafenone", "sotalol"],
        "risks": ["arrhythmia", "QT prolongation", "thyroid dysfunction"],
        "monitoring": ["ECG", "thyroid function", "pulmonary function"],
    },
}

# Duplicate therapy categories
DUPLICATE_THERAPY_CATEGORIES = {
    "statins": ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin"],
    "ace_inhibitors": ["lisinopril", "enalapril", "ramipril", "benazepril"],
    "arb": ["losartan", "valsartan", "irbesartan", "olmesartan"],
    "ppi": ["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole"],
    "ssri": ["fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram"],
    "benzodiazepines": ["diazepam", "lorazepam", "alprazolam", "clonazepam"],
    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "meloxicam"],
}


class DrugInteractionChecker:
    """Check for drug-drug interactions."""

    def check_interactions(self, medications: list[dict[str, Any]]) -> list[DrugInteraction]:
        """Check for interactions between a list of medications."""
        interactions = []
        med_names = [self._normalize_name(m.get("DESCRIPTION", "")) for m in medications]

        # Check all pairs
        for i, med1 in enumerate(med_names):
            for j, med2 in enumerate(med_names):
                if i >= j:
                    continue

                # Check interaction database
                interaction = self._lookup_interaction(med1, med2)
                if interaction:
                    interactions.append(interaction)

        return interactions

    def _normalize_name(self, name: str) -> str:
        """Normalize medication name for lookup."""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [" hcl", " sodium", " potassium", " mg", " tablet", " capsule"]:
            name = name.replace(suffix, "")
        return name

    def _lookup_interaction(self, med1: str, med2: str) -> DrugInteraction | None:
        """Look up interaction between two medications."""
        # Check both orderings
        key1 = (med1, med2)
        key2 = (med2, med1)

        if key1 in DRUG_INTERACTIONS:
            return DRUG_INTERACTIONS[key1]
        if key2 in DRUG_INTERACTIONS:
            return DRUG_INTERACTIONS[key2]

        # Check for category matches
        for (cat1, cat2), interaction in DRUG_INTERACTIONS.items():
            if (cat1 in med1 and cat2 in med2) or (cat1 in med2 and cat2 in med1):
                return interaction

        return None


class PolypharmacyAnalyzer:
    """Analyze polypharmacy risk for patients."""

    def analyze(self, store, patient_id: str) -> PolypharmacyRisk:
        """Analyze polypharmacy risk for a patient."""
        medications = store.rows("medications", patient_id)
        conditions = store.rows("conditions", patient_id)

        # Check for drug interactions
        interaction_checker = DrugInteractionChecker()
        interactions = interaction_checker.check_interactions(medications)

        # Check for duplicate therapies
        duplicate_therapies = self._find_duplicate_therapies(medications)

        # Check for high-risk medications
        high_risk_meds = self._find_high_risk_medications(medications)

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            len(medications),
            interactions,
            duplicate_therapies,
            high_risk_meds,
        )

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level,
            len(medications),
            interactions,
            duplicate_therapies,
            high_risk_meds,
        )

        # Identify deprescribing candidates
        deprescribing_candidates = self._identify_deprescribing_candidates(
            medications,
            conditions,
        )

        return PolypharmacyRisk(
            patient_id=patient_id,
            medication_count=len(medications),
            risk_level=risk_level,
            risk_score=risk_score,
            interactions=interactions,
            duplicate_therapies=duplicate_therapies,
            high_risk_medications=high_risk_meds,
            recommendations=recommendations,
            deprescribing_candidates=deprescribing_candidates,
        )

    def _find_duplicate_therapies(self, medications: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find medications in the same therapeutic category."""
        duplicates = []
        med_names = [m.get("DESCRIPTION", "").lower() for m in medications]

        for category, category_meds in DUPLICATE_THERAPY_CATEGORIES.items():
            found = []
            for med in med_names:
                for cat_med in category_meds:
                    if cat_med in med:
                        found.append(med)
                        break

            if len(found) > 1:
                duplicates.append({
                    "category": category,
                    "medications": found,
                    "risk": "Potential duplicate therapy",
                })

        return duplicates

    def _find_high_risk_medications(self, medications: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find high-risk medications."""
        high_risk = []
        med_names = [m.get("DESCRIPTION", "").lower() for m in medications]

        for category, info in HIGH_RISK_MEDICATIONS.items():
            for med in med_names:
                for hr_med in info["medications"]:
                    if hr_med in med:
                        high_risk.append({
                            "medication": med,
                            "category": category,
                            "risks": info["risks"],
                            "monitoring": info["monitoring"],
                        })
                        break

        return high_risk

    def _calculate_risk_score(
        self,
        med_count: int,
        interactions: list[DrugInteraction],
        duplicates: list[dict[str, Any]],
        high_risk: list[dict[str, Any]],
    ) -> float:
        """Calculate overall polypharmacy risk score."""
        score = 0.0

        # Medication count contribution
        if med_count >= 10:
            score += 0.3
        elif med_count >= 5:
            score += 0.15

        # Interaction contribution
        for interaction in interactions:
            if interaction.severity == "contraindicated":
                score += 0.3
            elif interaction.severity == "major":
                score += 0.2
            elif interaction.severity == "moderate":
                score += 0.1

        # Duplicate therapy contribution
        score += len(duplicates) * 0.1

        # High-risk medication contribution
        score += len(high_risk) * 0.05

        return min(score, 1.0)

    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score."""
        if risk_score >= 0.7:
            return "very_high"
        elif risk_score >= 0.5:
            return "high"
        elif risk_score >= 0.3:
            return "moderate"
        else:
            return "low"

    def _generate_recommendations(
        self,
        risk_level: str,
        med_count: int,
        interactions: list[DrugInteraction],
        duplicates: list[dict[str, Any]],
        high_risk: list[dict[str, Any]],
    ) -> list[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if risk_level in ["high", "very_high"]:
            recommendations.append("Schedule comprehensive medication review")
            recommendations.append("Consider deprescribing opportunities")

        if interactions:
            recommendations.append(f"Review {len(interactions)} drug interactions")
            for interaction in interactions:
                if interaction.severity in ["major", "contraindicated"]:
                    recommendations.append(f"Address {interaction.severity} interaction: {interaction.drug1} + {interaction.drug2}")

        if duplicates:
            recommendations.append(f"Review {len(duplicates)} potential duplicate therapies")

        if high_risk:
            recommendations.append(f"Monitor {len(high_risk)} high-risk medications closely")

        if med_count >= 10:
            recommendations.append("Consider medication consolidation")

        return recommendations

    def _identify_deprescribing_candidates(
        self,
        medications: list[dict[str, Any]],
        conditions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify medications that may be candidates for deprescribing."""
        candidates = []

        # Common deprescribing candidates
        deprescribing_patterns = {
            "ppi": {
                "reason": "Long-term PPI use associated with increased risks",
                "recommendation": "Consider step-down or discontinuation if no clear indication",
            },
            "benzodiazepine": {
                "reason": "Falls risk, cognitive impairment, dependence",
                "recommendation": "Gradual taper recommended, especially in elderly",
            },
            "antipsychotic": {
                "reason": "Increased mortality in dementia patients",
                "recommendation": "Consider discontinuation if used for behavioral symptoms",
            },
            "opioid": {
                "reason": "Risk of dependence, respiratory depression",
                "recommendation": "Consider non-opioid alternatives, dose reduction",
            },
        }

        med_names = [m.get("DESCRIPTION", "").lower() for m in medications]

        for med in med_names:
            for pattern, info in deprescribing_patterns.items():
                if pattern in med:
                    candidates.append({
                        "medication": med,
                        "reason": info["reason"],
                        "recommendation": info["recommendation"],
                    })

        return candidates
