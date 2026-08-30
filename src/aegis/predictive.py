from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskScore:
    """Risk score for a patient."""
    patient_id: str
    risk_type: str
    score: float  # 0.0 to 1.0
    risk_level: str  # low, moderate, high, very_high
    factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class DiabetesRiskPredictor:
    """Predict diabetes risk based on patient data."""

    # Risk factors and their weights
    RISK_FACTORS = {
        "age_over_45": 0.15,
        "age_over_65": 0.10,
        "bmi_over_25": 0.15,
        "bmi_over_30": 0.10,
        "family_history": 0.15,
        "hypertension": 0.10,
        "high_cholesterol": 0.10,
        "sedentary_lifestyle": 0.10,
        "gestational_diabetes": 0.10,
        "pcos": 0.05,
    }

    def predict(self, store, patient_id: str) -> RiskScore:
        """Predict diabetes risk for a patient."""
        patient = store.patient(patient_id)
        conditions = store.rows("conditions", patient_id)
        observations = store.rows("observations", patient_id)

        risk_factors = []
        total_score = 0.0

        # Check age
        birthdate = patient.get("BIRTHDATE", "")
        if birthdate:
            try:
                birth_year = int(birthdate.split("-")[0])
                age = 2026 - birth_year
                if age >= 65:
                    risk_factors.append("Age over 65")
                    total_score += self.RISK_FACTORS["age_over_65"]
                elif age >= 45:
                    risk_factors.append("Age over 45")
                    total_score += self.RISK_FACTORS["age_over_45"]
            except (ValueError, IndexError):
                pass

        # Check BMI from observations
        for obs in observations:
            description = obs.get("DESCRIPTION", "").lower()
            value = obs.get("VALUE")
            if "body mass index" in description and value:
                try:
                    bmi = float(value)
                    if bmi >= 30:
                        risk_factors.append(f"BMI {bmi:.1f} (obese)")
                        total_score += self.RISK_FACTORS["bmi_over_30"]
                    elif bmi >= 25:
                        risk_factors.append(f"BMI {bmi:.1f} (overweight)")
                        total_score += self.RISK_FACTORS["bmi_over_25"]
                except (ValueError, TypeError):
                    pass

        # Check conditions
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]

        if any("hypertension" in d for d in condition_descriptions):
            risk_factors.append("Hypertension")
            total_score += self.RISK_FACTORS["hypertension"]

        if any("hyperlipidemia" in d or "cholesterol" in d for d in condition_descriptions):
            risk_factors.append("High cholesterol")
            total_score += self.RISK_FACTORS["high_cholesterol"]

        if any("polycystic ovarian syndrome" in d or "pcos" in d for d in condition_descriptions):
            risk_factors.append("PCOS")
            total_score += self.RISK_FACTORS["pcos"]

        if any("gestational diabetes" in d for d in condition_descriptions):
            risk_factors.append("History of gestational diabetes")
            total_score += self.RISK_FACTORS["gestational_diabetes"]

        # Determine risk level
        if total_score >= 0.7:
            risk_level = "very_high"
        elif total_score >= 0.5:
            risk_level = "high"
        elif total_score >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, risk_factors)

        return RiskScore(
            patient_id=patient_id,
            risk_type="diabetes",
            score=min(total_score, 1.0),
            risk_level=risk_level,
            factors=risk_factors,
            recommendations=recommendations,
            confidence=0.7,
            metadata={"age": age if birthdate else None},
        )

    def _generate_recommendations(self, risk_level: str, factors: list[str]) -> list[str]:
        """Generate recommendations based on risk level."""
        recommendations = []

        if risk_level in ["high", "very_high"]:
            recommendations.append("Schedule HbA1c test")
            recommendations.append("Consult with endocrinologist")
            recommendations.append("Begin glucose monitoring")

        if risk_level == "moderate":
            recommendations.append("Annual diabetes screening")
            recommendations.append("Lifestyle modifications")

        if any("BMI" in f for f in factors):
            recommendations.append("Weight management program")
            recommendations.append("Nutritional counseling")

        if any("Hypertension" in f for f in factors):
            recommendations.append("Blood pressure management")

        if any("cholesterol" in f.lower() for f in factors):
            recommendations.append("Lipid panel monitoring")

        return recommendations


class CardiovascularRiskPredictor:
    """Predict cardiovascular risk based on patient data."""

    def predict(self, store, patient_id: str) -> RiskScore:
        """Predict cardiovascular risk for a patient."""
        patient = store.patient(patient_id)
        conditions = store.rows("conditions", patient_id)
        observations = store.rows("observations", patient_id)

        risk_factors = []
        total_score = 0.0

        # Check age and gender
        birthdate = patient.get("BIRTHDATE", "")
        gender = patient.get("GENDER", "")
        age = 0
        if birthdate:
            try:
                birth_year = int(birthdate.split("-")[0])
                age = 2026 - birth_year
                if age >= 65:
                    risk_factors.append("Age over 65")
                    total_score += 0.20
                elif age >= 55:
                    risk_factors.append("Age over 55")
                    total_score += 0.15
            except (ValueError, IndexError):
                pass

        # Gender-specific risk
        if gender == "M" and age >= 45:
            risk_factors.append("Male over 45")
            total_score += 0.10
        elif gender == "F" and age >= 55:
            risk_factors.append("Female over 55")
            total_score += 0.10

        # Check blood pressure
        for obs in observations:
            description = obs.get("DESCRIPTION", "").lower()
            value = obs.get("VALUE")
            if "systolic" in description and value:
                try:
                    bp = float(value)
                    if bp >= 140:
                        risk_factors.append(f"Hypertension (BP {bp:.0f})")
                        total_score += 0.15
                    elif bp >= 130:
                        risk_factors.append(f"Elevated BP ({bp:.0f})")
                        total_score += 0.10
                except (ValueError, TypeError):
                    pass

        # Check conditions
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]

        if any("hypertension" in d for d in condition_descriptions):
            risk_factors.append("Hypertension diagnosis")
            total_score += 0.15

        if any("diabetes" in d for d in condition_descriptions):
            risk_factors.append("Diabetes")
            total_score += 0.15

        if any("hyperlipidemia" in d or "cholesterol" in d for d in condition_descriptions):
            risk_factors.append("High cholesterol")
            total_score += 0.10

        if any("atrial fibrillation" in d for d in condition_descriptions):
            risk_factors.append("Atrial fibrillation")
            total_score += 0.15

        if any("heart failure" in d or "cardiomyopathy" in d for d in condition_descriptions):
            risk_factors.append("Heart failure history")
            total_score += 0.20

        # Determine risk level
        if total_score >= 0.7:
            risk_level = "very_high"
        elif total_score >= 0.5:
            risk_level = "high"
        elif total_score >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        recommendations = self._generate_recommendations(risk_level, risk_factors)

        return RiskScore(
            patient_id=patient_id,
            risk_type="cardiovascular",
            score=min(total_score, 1.0),
            risk_level=risk_level,
            factors=risk_factors,
            recommendations=recommendations,
            confidence=0.7,
            metadata={"age": age, "gender": gender},
        )

    def _generate_recommendations(self, risk_level: str, factors: list[str]) -> list[str]:
        """Generate recommendations based on risk level."""
        recommendations = []

        if risk_level in ["high", "very_high"]:
            recommendations.append("Cardiology consultation")
            recommendations.append("Stress test evaluation")
            recommendations.append("Echocardiogram")

        if risk_level == "moderate":
            recommendations.append("Annual cardiac screening")
            recommendations.append("Lipid panel monitoring")

        if any("Hypertension" in f or "BP" in f for f in factors):
            recommendations.append("Blood pressure management")
            recommendations.append("Low-sodium diet")

        if any("cholesterol" in f.lower() for f in factors):
            recommendations.append("Statin therapy evaluation")

        return recommendations


class ReadmissionRiskPredictor:
    """Predict hospital readmission risk."""

    def predict(self, store, patient_id: str) -> RiskScore:
        """Predict readmission risk for a patient."""
        encounters = store.rows("encounters", patient_id)
        conditions = store.rows("conditions", patient_id)
        medications = store.rows("medications", patient_id)

        risk_factors = []
        total_score = 0.0

        # Count hospital encounters
        hospital_encounters = [
            e for e in encounters
            if e.get("ENCOUNTERCLASS", "").lower() in ["inpatient", "emergency"]
        ]

        if len(hospital_encounters) >= 3:
            risk_factors.append(f"Multiple hospitalizations ({len(hospital_encounters)})")
            total_score += 0.25
        elif len(hospital_encounters) >= 2:
            risk_factors.append(f"Previous hospitalizations ({len(hospital_encounters)})")
            total_score += 0.15

        # Check for chronic conditions
        chronic_conditions = [
            "diabetes", "heart failure", "copd", "asthma", "chronic kidney",
            "hypertension", "atrial fibrillation", "depression"
        ]
        condition_descriptions = [c.get("DESCRIPTION", "").lower() for c in conditions]

        for chronic in chronic_conditions:
            if any(chronic in d for d in condition_descriptions):
                risk_factors.append(f"Chronic condition: {chronic}")
                total_score += 0.10

        # Check medication count
        if len(medications) >= 10:
            risk_factors.append(f"Polypharmacy ({len(medications)} medications)")
            total_score += 0.15
        elif len(medications) >= 5:
            risk_factors.append(f"Multiple medications ({len(medications)})")
            total_score += 0.10

        # Determine risk level
        if total_score >= 0.6:
            risk_level = "very_high"
        elif total_score >= 0.4:
            risk_level = "high"
        elif total_score >= 0.2:
            risk_level = "moderate"
        else:
            risk_level = "low"

        recommendations = self._generate_recommendations(risk_level, risk_factors)

        return RiskScore(
            patient_id=patient_id,
            risk_type="readmission",
            score=min(total_score, 1.0),
            risk_level=risk_level,
            factors=risk_factors,
            recommendations=recommendations,
            confidence=0.6,
            metadata={"hospital_encounters": len(hospital_encounters)},
        )

    def _generate_recommendations(self, risk_level: str, factors: list[str]) -> list[str]:
        """Generate recommendations based on risk level."""
        recommendations = []

        if risk_level in ["high", "very_high"]:
            recommendations.append("Post-discharge follow-up within 7 days")
            recommendations.append("Care coordination assignment")
            recommendations.append("Medication reconciliation")

        if risk_level == "moderate":
            recommendations.append("Follow-up within 30 days")
            recommendations.append("Patient education materials")

        if any("Polypharmacy" in f for f in factors):
            recommendations.append("Medication review by pharmacist")

        return recommendations


class PredictiveAnalyticsEngine:
    """Engine for running predictive analytics on patient data."""

    def __init__(self):
        self.diabetes_predictor = DiabetesRiskPredictor()
        self.cardiovascular_predictor = CardiovascularRiskPredictor()
        self.readmission_predictor = ReadmissionRiskPredictor()

    def assess_risks(self, store, patient_id: str) -> list[RiskScore]:
        """Assess all risks for a patient."""
        risks = []

        # Diabetes risk
        diabetes_risk = self.diabetes_predictor.predict(store, patient_id)
        risks.append(diabetes_risk)

        # Cardiovascular risk
        cv_risk = self.cardiovascular_predictor.predict(store, patient_id)
        risks.append(cv_risk)

        # Readmission risk
        readmission_risk = self.readmission_predictor.predict(store, patient_id)
        risks.append(readmission_risk)

        return risks

    def get_high_risk_patients(self, store, risk_type: str = "all") -> list[dict[str, Any]]:
        """Get patients with high risk scores."""
        high_risk = []

        if not store.tables:
            store.load()

        patients = store.tables.get("patients")
        if patients is None:
            return []

        for _, row in patients.iterrows():
            patient_id = row["Id"]
            risks = self.assess_risks(store, patient_id)

            for risk in risks:
                if risk.risk_level in ["high", "very_high"]:
                    if risk_type == "all" or risk.risk_type == risk_type:
                        high_risk.append({
                            "patient_id": patient_id,
                            "risk_type": risk.risk_type,
                            "score": risk.score,
                            "risk_level": risk.risk_level,
                            "factors": risk.factors,
                        })

        return sorted(high_risk, key=lambda x: x["score"], reverse=True)
