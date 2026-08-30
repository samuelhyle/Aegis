from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pandas as pd


class SyntheaStore:
    """Data store for Synthea CSV files with lazy loading and caching."""

    TABLES: ClassVar[list[str]] = [
        "patients", "encounters", "conditions", "medications",
        "observations", "procedures", "allergies", "careplans",
        "immunizations",
    ]

    def __init__(self, data_dir: str = "data/synthea", ttl: int = 300):
        self.data_dir = Path(data_dir)
        self.tables: dict[str, pd.DataFrame] = {}
        self._loaded = False
        self._ttl = ttl  # Time to live in seconds
        self._load_time: float | None = None

    def load(self) -> dict[str, pd.DataFrame]:
        """Load all available Synthea CSV files with TTL-based caching."""
        current_time = __import__("time").time()

        # Return cached data if still valid
        if self._loaded and self._load_time and (current_time - self._load_time) < self._ttl:
            return self.tables

        if self._loaded and not self._load_time:
            # Force reload if no load time recorded
            self._loaded = False

        self.tables = {}
        for name in self.TABLES:
            path = self.data_dir / f"{name}.csv"
            if path.exists():
                try:
                    df = pd.read_csv(path)
                    if not df.empty:
                        self.tables[name] = df
                except Exception as e:
                    print(f"Warning: Failed to load {path}: {e}")

        self._loaded = True
        self._load_time = current_time
        return self.tables

    def patient(self, patient_id: str) -> dict[str, Any]:
        """Get a patient record by ID."""
        if not self._loaded:
            self.load()

        df = self.tables.get("patients")
        if df is None:
            return {}

        row = df[df["Id"].astype(str) == str(patient_id)]
        return row.iloc[0].to_dict() if not row.empty else {}

    def rows(self, table: str, patient_id: str) -> list[dict[str, Any]]:
        """Get all rows for a patient from a specific table."""
        if not self._loaded:
            self.load()

        df = self.tables.get(table)
        if df is None or "PATIENT" not in df.columns:
            return []

        return df[df["PATIENT"].astype(str) == str(patient_id)].to_dict("records")

    def patient_count(self) -> int:
        """Get the number of patients in the dataset."""
        if not self._loaded:
            self.load()

        df = self.tables.get("patients")
        return len(df) if df is not None else 0

    def table_stats(self) -> dict[str, int]:
        """Get row counts for all loaded tables."""
        if not self._loaded:
            self.load()

        return {name: len(df) for name, df in self.tables.items()}

    def search(self, table: str, column: str, value: str) -> list[dict[str, Any]]:
        """Search a table for rows where column contains value."""
        if not self._loaded:
            self.load()

        df = self.tables.get(table)
        if df is None or column not in df.columns:
            return []

        mask = df[column].astype(str).str.contains(value, case=False, na=False)
        return df[mask].to_dict("records")

    def invalidate_cache(self, patient_id: str | None = None) -> None:
        """Invalidate cached data, optionally for a specific patient."""
        self._loaded = False
        self._load_time = None
        self.tables = {}
