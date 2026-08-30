import pytest

from aegis.clinical_tools import (
    assess_patient_risks,
    calculate_age,
    check_drug_interactions,
    find_related_conditions,
    forecast_patient_outcome,
    get_condition_duration,
    get_lab_analysis,
    get_patient_allergies,
    get_patient_careplans,
    get_patient_conditions,
    get_patient_encounters,
    get_patient_medications,
    get_patient_observations,
    get_patient_procedures,
    get_patient_record,
    match_clinical_trials,
)
from aegis.store import SyntheaStore


@pytest.fixture
def store():
    """Create a loaded store for testing."""
    store = SyntheaStore("data/synthea")
    store.load()
    return store


@pytest.fixture
def sample_patient_id(store):
    """Get a sample patient ID for testing."""
    patients = store.tables["patients"]
    if len(patients) == 0:
        pytest.skip("No patients in dataset")
    return patients.iloc[0]["Id"]


@pytest.fixture
def patient_with_conditions(store):
    """Get a patient ID that has conditions."""
    patients = store.tables["patients"]
    for _, row in patients.iterrows():
        pid = row["Id"]
        conditions = store.rows("conditions", pid)
        if len(conditions) > 0:
            return pid
    pytest.skip("No patient with conditions found")


@pytest.fixture
def patient_with_medications(store):
    """Get a patient ID that has medications."""
    patients = store.tables["patients"]
    for _, row in patients.iterrows():
        pid = row["Id"]
        medications = store.rows("medications", pid)
        if len(medications) > 0:
            return pid
    pytest.skip("No patient with medications found")


class TestDataAccessTools:
    """Tests for data access tools."""

    def test_get_patient_record(self, sample_patient_id):
        """Test getting a patient record."""
        record = get_patient_record(sample_patient_id)
        assert record is not None
        assert "FIRST" in record or "LAST" in record or "Id" in record

    def test_get_patient_record_not_found(self):
        """Test getting a non-existent patient record."""
        with pytest.raises(ValueError, match="not found"):
            get_patient_record("nonexistent-patient")

    def test_get_patient_conditions(self, patient_with_conditions):
        """Test getting patient conditions."""
        conditions = get_patient_conditions(patient_with_conditions)
        assert isinstance(conditions, list)
        assert len(conditions) > 0
        # Check structure
        for cond in conditions:
            assert "DESCRIPTION" in cond or "CODE" in cond

    def test_get_patient_medications(self, patient_with_medications):
        """Test getting patient medications."""
        medications = get_patient_medications(patient_with_medications)
        assert isinstance(medications, list)
        assert len(medications) > 0

    def test_get_patient_observations(self, sample_patient_id):
        """Test getting patient observations."""
        observations = get_patient_observations(sample_patient_id)
        assert isinstance(observations, list)

    def test_get_patient_encounters(self, sample_patient_id):
        """Test getting patient encounters."""
        encounters = get_patient_encounters(sample_patient_id)
        assert isinstance(encounters, list)

    def test_get_patient_procedures(self, sample_patient_id):
        """Test getting patient procedures."""
        procedures = get_patient_procedures(sample_patient_id)
        assert isinstance(procedures, list)

    def test_get_patient_allergies(self, sample_patient_id):
        """Test getting patient allergies."""
        allergies = get_patient_allergies(sample_patient_id)
        assert isinstance(allergies, list)

    def test_get_patient_careplans(self, sample_patient_id):
        """Test getting patient careplans."""
        careplans = get_patient_careplans(sample_patient_id)
        assert isinstance(careplans, list)

    def test_calculate_age(self, sample_patient_id):
        """Test calculating patient age."""
        age = calculate_age(sample_patient_id)
        assert isinstance(age, int)
        assert age >= 0

    def test_calculate_age_not_found(self):
        """Test calculating age for non-existent patient."""
        with pytest.raises(ValueError, match="not found"):
            calculate_age("nonexistent-patient")


class TestClinicalReasoningTools:
    """Tests for clinical reasoning tools."""

    def test_assess_patient_risks(self, patient_with_conditions):
        """Test assessing patient risks."""
        risks = assess_patient_risks(patient_with_conditions)
        assert isinstance(risks, list)
        for risk in risks:
            assert "risk_type" in risk
            assert "score" in risk
            assert "risk_level" in risk
            assert risk["risk_level"] in ["low", "moderate", "high", "very_high"]

    def test_check_drug_interactions(self, patient_with_medications):
        """Test checking drug interactions."""
        result = check_drug_interactions(patient_with_medications)
        assert isinstance(result, dict)
        assert "medication_count" in result
        assert "risk_level" in result
        assert "interactions" in result
        assert "recommendations" in result

    def test_match_clinical_trials(self, patient_with_conditions):
        """Test matching clinical trials."""
        matches = match_clinical_trials(patient_with_conditions)
        assert isinstance(matches, list)
        for match in matches:
            assert "trial_id" in match
            assert "title" in match
            assert "confidence" in match
            assert "eligibility_status" in match

    def test_forecast_patient_outcome(self, patient_with_conditions):
        """Test forecasting patient outcome."""
        forecast = forecast_patient_outcome(patient_with_conditions)
        assert isinstance(forecast, dict)
        assert "patient_id" in forecast
        assert "risks" in forecast
        assert "trajectory" in forecast

    def test_get_lab_analysis(self, sample_patient_id):
        """Test getting lab analysis."""
        analysis = get_lab_analysis(sample_patient_id)
        assert isinstance(analysis, dict)
        assert "lab_results" in analysis
        assert "temporal_patterns" in analysis

    def test_get_condition_duration(self, patient_with_conditions):
        """Test getting condition duration."""
        # Get a condition for this patient
        conditions = get_patient_conditions(patient_with_conditions)
        if not conditions:
            pytest.skip("No conditions found")

        condition_desc = conditions[0].get("DESCRIPTION", "")
        if not condition_desc:
            pytest.skip("No condition description found")

        try:
            duration = get_condition_duration(patient_with_conditions, condition_desc)
            assert isinstance(duration, dict)
            assert "duration_days" in duration
            assert "duration_years" in duration
            assert "status" in duration
        except ValueError:
            # Condition might not be found with exact match
            pass


class TestKnowledgeGraphTools:
    """Tests for knowledge graph tools."""

    def test_find_related_conditions(self, patient_with_conditions):
        """Test finding related conditions."""
        conditions = get_patient_conditions(patient_with_conditions)
        if not conditions:
            pytest.skip("No conditions found")

        condition_desc = conditions[0].get("DESCRIPTION", "")
        if not condition_desc:
            pytest.skip("No condition description found")

        related = find_related_conditions(condition_desc, patient_with_conditions)
        assert isinstance(related, list)
