from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Institution:
    """A participating institution in federated learning."""
    institution_id: str
    name: str
    endpoint: str
    public_key: str = ""
    status: str = "active"  # active, inactive, pending
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelUpdate:
    """A model update from an institution."""
    update_id: str
    institution_id: str
    round_number: int
    model_weights: dict[str, Any] = field(default_factory=dict)
    gradient_updates: dict[str, Any] = field(default_factory=dict)
    sample_count: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signature: str = ""


@dataclass
class FederatedRound:
    """A round of federated learning."""
    round_id: str
    round_number: int
    status: str = "pending"  # pending, in_progress, completed, failed
    participating_institutions: list[str] = field(default_factory=list)
    updates_received: list[ModelUpdate] = field(default_factory=list)
    aggregated_model: dict[str, Any] = field(default_factory=dict)
    global_metrics: dict[str, float] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class PrivacyBudget:
    """Privacy budget for differential privacy."""
    epsilon: float = 1.0  # Privacy budget
    delta: float = 1e-5  # Failure probability
    consumed_epsilon: float = 0.0
    consumed_delta: float = 0.0
    remaining_epsilon: float = 1.0
    remaining_delta: float = 1e-5


class DifferentialPrivacyMechanism:
    """Differential privacy mechanism for federated learning."""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplacian noise for differential privacy."""
        import random
        scale = sensitivity / self.epsilon
        noise = random.gauss(0, scale)
        return value + noise

    def add_noise_to_vector(self, vector: list[float], sensitivity: float = 1.0) -> list[float]:
        """Add noise to a vector of values."""
        return [self.add_noise(v, sensitivity) for v in vector]

    def clip_gradient(self, gradient: list[float], max_norm: float = 1.0) -> list[float]:
        """Clip gradient to bound sensitivity."""
        norm = sum(g ** 2 for g in gradient) ** 0.5
        if norm > max_norm:
            scale = max_norm / norm
            return [g * scale for g in gradient]
        return gradient

    def compute_privacy_budget(self, num_rounds: int, sample_rate: float) -> PrivacyBudget:
        """Compute privacy budget for given number of rounds."""
        # Simplified composition theorem
        consumed_epsilon = num_rounds * sample_rate * self.epsilon
        consumed_delta = num_rounds * self.delta

        return PrivacyBudget(
            epsilon=self.epsilon,
            delta=self.delta,
            consumed_epsilon=consumed_epsilon,
            consumed_delta=consumed_delta,
            remaining_epsilon=max(0, self.epsilon - consumed_epsilon),
            remaining_delta=max(0, self.delta - consumed_delta),
        )


class SecureAggregator:
    """Secure aggregation for federated learning."""

    def __init__(self):
        self.aggregation_methods = {
            "federated_averaging": self.federated_averaging,
            "weighted_averaging": self.weighted_averaging,
            "median_aggregation": self.median_aggregation,
        }

    def federated_averaging(self, updates: list[ModelUpdate]) -> dict[str, Any]:
        """Aggregate model updates using federated averaging."""
        if not updates:
            return {}

        # Simple averaging of weights
        aggregated = {}
        num_updates = len(updates)

        for update in updates:
            for key, value in update.model_weights.items():
                if key not in aggregated:
                    aggregated[key] = 0.0
                aggregated[key] += value / num_updates

        return aggregated

    def weighted_averaging(self, updates: list[ModelUpdate]) -> dict[str, Any]:
        """Aggregate model updates using weighted averaging based on sample count."""
        if not updates:
            return {}

        total_samples = sum(u.sample_count for u in updates)
        if total_samples == 0:
            return self.federated_averaging(updates)

        aggregated = {}
        for update in updates:
            weight = update.sample_count / total_samples
            for key, value in update.model_weights.items():
                if key not in aggregated:
                    aggregated[key] = 0.0
                aggregated[key] += value * weight

        return aggregated

    def median_aggregation(self, updates: list[ModelUpdate]) -> dict[str, Any]:
        """Aggregate model updates using coordinate-wise median."""
        if not updates:
            return {}

        aggregated = {}
        for key in updates[0].model_weights:
            values = sorted(u.model_weights.get(key, 0.0) for u in updates)
            mid = len(values) // 2
            if len(values) % 2 == 0:
                aggregated[key] = (values[mid - 1] + values[mid]) / 2
            else:
                aggregated[key] = values[mid]

        return aggregated

    def aggregate(self, updates: list[ModelUpdate], method: str = "federated_averaging") -> dict[str, Any]:
        """Aggregate updates using specified method."""
        if method not in self.aggregation_methods:
            raise ValueError(f"Unknown aggregation method: {method}")
        return self.aggregation_methods[method](updates)


class FederatedLearningCoordinator:
    """Coordinator for federated learning across institutions."""

    def __init__(self):
        self.institutions: dict[str, Institution] = {}
        self.rounds: list[FederatedRound] = []
        self.current_round: FederatedRound | None = None
        self.global_model: dict[str, Any] = {}
        self.privacy_mechanism = DifferentialPrivacyMechanism()
        self.secure_aggregator = SecureAggregator()
        self.privacy_budget = PrivacyBudget()

    def register_institution(self, institution: Institution) -> None:
        """Register a new institution for federated learning."""
        self.institutions[institution.institution_id] = institution

    def start_round(self, round_number: int) -> FederatedRound:
        """Start a new federated learning round."""
        round_id = str(uuid4())
        participating = [inst.institution_id for inst in self.institutions.values() if inst.status == "active"]

        self.current_round = FederatedRound(
            round_id=round_id,
            round_number=round_number,
            status="in_progress",
            participating_institutions=participating,
            started_at=datetime.now(timezone.utc),
        )

        self.rounds.append(self.current_round)
        return self.current_round

    def submit_update(self, update: ModelUpdate) -> bool:
        """Submit a model update from an institution."""
        if not self.current_round or self.current_round.status != "in_progress":
            return False

        if update.institution_id not in self.current_round.participating_institutions:
            return False

        # Apply differential privacy
        if self.privacy_mechanism:
            for key in update.model_weights:
                if isinstance(update.model_weights[key], (int, float)):
                    update.model_weights[key] = self.privacy_mechanism.add_noise(
                        update.model_weights[key]
                    )

        self.current_round.updates_received.append(update)
        return True

    def complete_round(self, aggregation_method: str = "federated_averaging") -> dict[str, Any]:
        """Complete the current round and aggregate updates."""
        if not self.current_round:
            return {}

        # Aggregate updates
        aggregated = self.secure_aggregator.aggregate(
            self.current_round.updates_received,
            aggregation_method,
        )

        # Update global model
        self.global_model = aggregated

        # Compute global metrics
        metrics = self._compute_global_metrics(self.current_round.updates_received)

        # Update round status
        self.current_round.aggregated_model = aggregated
        self.current_round.global_metrics = metrics
        self.current_round.status = "completed"
        self.current_round.completed_at = datetime.now(timezone.utc)

        # Update privacy budget
        self.privacy_budget = self.privacy_mechanism.compute_privacy_budget(
            len(self.rounds),
            1.0 / len(self.institutions) if self.institutions else 1.0,
        )

        return aggregated

    def _compute_global_metrics(self, updates: list[ModelUpdate]) -> dict[str, float]:
        """Compute global metrics from institution updates."""
        if not updates:
            return {}

        # Average metrics across institutions
        all_metrics: dict[str, list[float]] = {}
        for update in updates:
            for key, value in update.metrics.items():
                if key not in all_metrics:
                    all_metrics[key] = []
                all_metrics[key].append(value)

        return {key: sum(values) / len(values) for key, values in all_metrics.items()}

    def get_global_model(self) -> dict[str, Any]:
        """Get the current global model."""
        return self.global_model

    def get_round_history(self) -> list[dict[str, Any]]:
        """Get history of all rounds."""
        return [
            {
                "round_id": r.round_id,
                "round_number": r.round_number,
                "status": r.status,
                "participants": len(r.participating_institutions),
                "updates_received": len(r.updates_received),
                "global_metrics": r.global_metrics,
            }
            for r in self.rounds
        ]

    def get_privacy_status(self) -> dict[str, Any]:
        """Get current privacy budget status."""
        return {
            "epsilon": self.privacy_budget.epsilon,
            "delta": self.privacy_budget.delta,
            "consumed_epsilon": self.privacy_budget.consumed_epsilon,
            "consumed_delta": self.privacy_budget.consumed_delta,
            "remaining_epsilon": self.privacy_budget.remaining_epsilon,
            "remaining_delta": self.privacy_budget.remaining_delta,
        }


class DataAnonymizer:
    """Anonymize patient data for privacy protection."""

    def __init__(self):
        self.salt = os.urandom(32).hex()

    def hash_identifier(self, identifier: str) -> str:
        """Hash an identifier with salt for anonymization."""
        return hashlib.sha256(f"{self.salt}{identifier}".encode()).hexdigest()

    def anonymize_patient(self, patient: dict[str, Any]) -> dict[str, Any]:
        """Anonymize a patient record."""
        anonymized = patient.copy()

        # Hash direct identifiers
        if "Id" in anonymized:
            anonymized["Id"] = self.hash_identifier(anonymized["Id"])
        if "SSN" in anonymized:
            anonymized["SSN"] = self.hash_identifier(anonymized["SSN"])
        if "DRIVERS" in anonymized:
            anonymized["DRIVERS"] = self.hash_identifier(anonymized["DRIVERS"])
        if "PASSPORT" in anonymized:
            anonymized["PASSPORT"] = self.hash_identifier(anonymized["PASSPORT"])

        # Generalize quasi-identifiers
        if "BIRTHDATE" in anonymized:
            # Keep only birth year
            try:
                anonymized["BIRTHDATE"] = anonymized["BIRTHDATE"][:4] + "-01-01"
            except (ValueError, IndexError):
                pass

        if "ZIP" in anonymized:
            # Keep only first 3 digits
            try:
                zip_str = str(anonymized["ZIP"])
                anonymized["ZIP"] = zip_str[:3] + "00"
            except (ValueError, IndexError):
                pass

        # Remove free-text fields
        for text_field in ["ADDRESS", "CITY", "COUNTY"]:
            if text_field in anonymized:
                del anonymized[text_field]

        return anonymized

    def anonymize_dataset(self, patients: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anonymize a dataset of patients."""
        return [self.anonymize_patient(p) for p in patients]


class AuditLogger:
    """Audit logger for federated learning operations."""

    def __init__(self):
        self.audit_log: list[dict[str, Any]] = []

    def log_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Log an audit event."""
        self.audit_log.append({
            "event_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        })

    def log_institution_registration(self, institution: Institution) -> None:
        """Log institution registration."""
        self.log_event("institution_registered", {
            "institution_id": institution.institution_id,
            "name": institution.name,
        })

    def log_round_start(self, round_id: str, participants: list[str]) -> None:
        """Log round start."""
        self.log_event("round_started", {
            "round_id": round_id,
            "participants": participants,
        })

    def log_update_received(self, update: ModelUpdate) -> None:
        """Log model update received."""
        self.log_event("update_received", {
            "update_id": update.update_id,
            "institution_id": update.institution_id,
            "sample_count": update.sample_count,
        })

    def log_round_completed(self, round_id: str, metrics: dict[str, float]) -> None:
        """Log round completion."""
        self.log_event("round_completed", {
            "round_id": round_id,
            "metrics": metrics,
        })

    def get_audit_log(self, event_type: str | None = None) -> list[dict[str, Any]]:
        """Get audit log entries."""
        if event_type:
            return [e for e in self.audit_log if e["event_type"] == event_type]
        return self.audit_log
