"""Comprehensive tests for the AEGIS store module."""
from aegis.store import SyntheaStore


class TestSyntheaStore:
    """Tests for SyntheaStore."""

    def test_load_tables(self):
        """Test that all tables are loaded."""
        store = SyntheaStore("data/synthea")
        tables = store.load()
        assert "patients" in tables
        assert "encounters" in tables
        assert "conditions" in tables
        assert "medications" in tables
        assert "observations" in tables

    def test_patient_count(self):
        """Test patient count."""
        store = SyntheaStore("data/synthea")
        store.load()
        count = store.patient_count()
        assert count > 0
        assert count == len(store.tables["patients"])

    def test_table_stats(self):
        """Test table statistics."""
        store = SyntheaStore("data/synthea")
        store.load()
        stats = store.table_stats()
        assert "patients" in stats
        assert stats["patients"] > 0

    def test_patient_found(self):
        """Test finding an existing patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient_id = store.tables["patients"]["Id"].iloc[0]
        patient = store.patient(first_patient_id)
        assert patient
        assert "Id" in patient

    def test_patient_not_found(self):
        """Test that nonexistent patient returns empty dict."""
        store = SyntheaStore("data/synthea")
        store.load()
        patient = store.patient("nonexistent-patient-id")
        assert patient == {}

    def test_rows_with_valid_patient(self):
        """Test getting rows for a valid patient."""
        store = SyntheaStore("data/synthea")
        store.load()
        first_patient_id = store.tables["patients"]["Id"].iloc[0]
        conditions = store.rows("conditions", first_patient_id)
        assert isinstance(conditions, list)

    def test_rows_with_invalid_table(self):
        """Test getting rows from nonexistent table."""
        store = SyntheaStore("data/synthea")
        store.load()
        rows = store.rows("nonexistent_table", "some-patient")
        assert rows == []

    def test_search(self):
        """Test searching a table."""
        store = SyntheaStore("data/synthea")
        store.load()
        # Search for a common condition
        results = store.search("conditions", "DESCRIPTION", "education")
        assert isinstance(results, list)

    def test_lazy_loading(self):
        """Test that tables are loaded lazily."""
        store = SyntheaStore("data/synthea")
        assert not store._loaded
        store.load()
        assert store._loaded

    def test_double_load(self):
        """Test that loading twice doesn't reload."""
        store = SyntheaStore("data/synthea")
        tables1 = store.load()
        tables2 = store.load()
        assert tables1 is tables2
