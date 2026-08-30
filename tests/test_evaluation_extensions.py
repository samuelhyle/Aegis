from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from aegis.evaluation_extensions import (
    AgentComparator,
    AgentComparison,
    EnhancedEvaluationManager,
    EvaluationStore,
    ExtendedMetricsCalculator,
    SyntheticBenchmarkGenerator,
)
from aegis.evaluation_framework import EvaluationResult, EvaluationStatus, MetricScore, MetricType

# ---------------------------------------------------------------------------
# Extended Metrics Calculator
# ---------------------------------------------------------------------------

class TestExtendedMetricsCalculator:
    def setup_method(self):
        self.calc = ExtendedMetricsCalculator()

    def test_factuality_supported(self):
        claims = ["Patient has diabetes", "Patient takes metformin"]
        evidence = ["Diagnosis: Diabetes mellitus type 2", "Medication: Metformin 500mg"]
        score, details = self.calc.calculate_factuality(claims, evidence)
        assert score >= 0.5
        assert details["checked"] == 2

    def test_factuality_unsupported(self):
        claims = ["Patient has cancer", "Patient has HIV"]
        evidence = ["Diagnosis: Diabetes mellitus type 2"]
        score, details = self.calc.calculate_factuality(claims, evidence)
        assert score < 0.5

    def test_factuality_empty(self):
        score, details = self.calc.calculate_factuality([], ["evidence"])
        assert score == 1.0

    def test_hallucination_rate_low(self):
        conclusion = "Patient has diabetes. Lab results show elevated glucose levels."
        evidence = ["Diagnosis: Diabetes mellitus", "Lab: HbA1c elevated", "Lab: Glucose high"]
        rate, details = self.calc.calculate_hallucination_rate(conclusion, evidence)
        assert rate <= 0.5

    def test_hallucination_rate_high(self):
        conclusion = "Patient has advanced pancreatic cancer with metastasis to the liver and brain."
        evidence = ["Diagnosis: Diabetes mellitus"]
        rate, details = self.calc.calculate_hallucination_rate(conclusion, evidence)
        assert rate >= 0.0

    def test_hallucination_empty(self):
        rate, details = self.calc.calculate_hallucination_rate("", ["evidence"])
        assert rate == 0.5

    def test_retrieval_precision(self):
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc3", "doc5"]
        score, details = self.calc.calculate_retrieval_precision(retrieved, relevant)
        assert score == pytest.approx(2 / 3, abs=0.01)

    def test_retrieval_precision_empty(self):
        score, details = self.calc.calculate_retrieval_precision([], ["relevant"])
        assert score == 0.0

    def test_citation_correctness_with_citations(self):
        text = "Patient has diabetes [source_1]. Treatment includes metformin [evidence_2]."
        score, details = self.calc.calculate_citation_correctness(text)
        assert score == 1.0
        assert details["citations_found"] == 2

    def test_citation_correctness_no_citations(self):
        text = "Patient has diabetes. Treatment includes metformin."
        score, details = self.calc.calculate_citation_correctness(text)
        assert score == 0.5

    def test_token_efficiency(self):
        score, details = self.calc.calculate_token_efficiency(
            input_tokens=500, output_tokens=200, information_content=5.0
        )
        assert 0.0 <= score <= 1.0
        assert details["total_tokens"] == 700

    def test_cost_efficiency(self):
        score, details = self.calc.calculate_cost_efficiency(cost_usd=0.01, score=0.8)
        assert 0.0 <= score <= 1.0

    def test_task_completion(self):
        required = ["diagnosis", "medications", "risks"]
        provided = ["diagnosis", "medications"]
        score, details = self.calc.calculate_task_completion(required, provided)
        assert score == pytest.approx(2 / 3, abs=0.01)
        assert "risks" in details["missing"]

    def test_clinical_safety_safe(self):
        output = {
            "conclusion": "Patient has diabetes. Please consult your doctor.",
            "review_required": True,
            "confidence": 0.7,
            "uncertainties": ["Lab values may need rechecking"],
        }
        score, details = self.calc.calculate_clinical_safety(output)
        assert score >= 0.8

    def test_clinical_safety_flags(self):
        output = {
            "conclusion": "This patient definitely has cancer. Take this medication.",
            "review_required": False,
            "confidence": 0.99,
        }
        score, details = self.calc.calculate_clinical_safety(output)
        assert score < 0.8
        assert len(details["flags"]) > 0


# ---------------------------------------------------------------------------
# Synthetic Benchmark Generator
# ---------------------------------------------------------------------------

class TestSyntheticBenchmarkGenerator:
    def test_generate_from_patient(self):
        conditions = [{"DESCRIPTION": "Diabetes mellitus type 2"}, {"DESCRIPTION": "Hypertension"}]
        medications = [{"DESCRIPTION": "Metformin"}, {"DESCRIPTION": "Lisinopril"}]
        observations = [{"DESCRIPTION": "Glucose", "VALUE": "180"}]
        encounters = [{"DESCRIPTION": "Office visit"}]

        cases = SyntheticBenchmarkGenerator.generate_from_patient(
            "test-patient-123", conditions, medications, observations, encounters
        )
        assert len(cases) > 0
        assert all(c.patient_id == "test-patient-123" for c in cases)
        assert any(c.category == "diagnosis" for c in cases)
        assert any(c.category == "treatment" for c in cases)

    def test_generate_empty_patient(self):
        cases = SyntheticBenchmarkGenerator.generate_from_patient(
            "empty-patient", [], [], [], []
        )
        assert len(cases) > 0
        assert all(len(c.expected_findings) > 0 for c in cases)

    def test_estimate_difficulty(self):
        assert SyntheticBenchmarkGenerator._estimate_difficulty("What conditions does this patient have?", "diagnosis") == "easy"
        assert SyntheticBenchmarkGenerator._estimate_difficulty("What are this patient's primary health risks?", "risk") == "hard"
        assert SyntheticBenchmarkGenerator._estimate_difficulty("Describe treatment plan.", "treatment") == "medium"


# ---------------------------------------------------------------------------
# Evaluation Store (SQLite Persistence)
# ---------------------------------------------------------------------------

class TestEvaluationStore:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self.tmpdir) / "test_eval.db"
        self.store = EvaluationStore(self.db_path)

    def test_save_and_get_report(self):
        from aegis.evaluation_framework import BenchmarkReport, MetricType
        report = BenchmarkReport(
            report_id="test-001",
            benchmark_name="Test Benchmark",
            agent_name="test_agent",
            total_cases=10,
            completed_cases=8,
            failed_cases=2,
            metric_scores={MetricType.ACCURACY: 0.85, MetricType.GROUNDING: 0.72},
            category_scores={"diagnosis": 0.9, "treatment": 0.7},
            difficulty_scores={"easy": 0.95, "hard": 0.6},
            overall_score=0.81,
            latency_stats={"mean": 150.0, "p95": 300.0},
            results=[],
        )
        self.store.save_report(report)
        retrieved = self.store.get_report("test-001")
        assert retrieved is not None
        assert retrieved["agent_name"] == "test_agent"
        assert retrieved["overall_score"] == 0.81

    def test_list_reports(self):
        from aegis.evaluation_framework import BenchmarkReport, MetricType
        for i in range(3):
            report = BenchmarkReport(
                report_id=f"rpt-{i:03d}",
                benchmark_name="Test",
                agent_name="agent_a",
                total_cases=5,
                completed_cases=5,
                failed_cases=0,
                metric_scores={MetricType.ACCURACY: 0.8},
                category_scores={},
                difficulty_scores={},
                overall_score=0.8,
                latency_stats={},
                results=[],
            )
            self.store.save_report(report)
        reports = self.store.list_reports(agent_name="agent_a")
        assert len(reports) == 3

    def test_save_and_get_comparison(self):
        comparison = AgentComparison(
            comparison_id="comp-001",
            agents=["agent_a", "agent_b"],
            cases_evaluated=10,
            agent_scores={"agent_a": {"overall": 0.85}, "agent_b": {"overall": 0.78}},
            metric_comparison={"overall": {"agent_a": 0.85, "agent_b": 0.78}},
            winner="agent_a",
            confidence=0.35,
        )
        self.store.save_comparison(comparison)

    def test_save_cases(self):
        from aegis.evaluation_framework import EvaluationCase
        cases = [
            EvaluationCase(
                case_id="c-001",
                patient_id="p-001",
                question="Test question",
                category="diagnosis",
                difficulty="easy",
                ground_truth={"key": "value"},
                expected_findings=["finding1"],
                expected_confidence_range=(0.5, 0.9),
            )
        ]
        saved = self.store.save_cases(cases)
        assert saved == 1

    def test_get_trends(self):
        from aegis.evaluation_framework import BenchmarkReport, MetricType
        for i in range(3):
            report = BenchmarkReport(
                report_id=f"trend-{i}",
                benchmark_name="Test",
                agent_name="agent_a",
                total_cases=5,
                completed_cases=5,
                failed_cases=0,
                metric_scores={MetricType.ACCURACY: 0.7 + i * 0.05},
                category_scores={},
                difficulty_scores={},
                overall_score=0.7 + i * 0.05,
                latency_stats={},
                results=[],
            )
            self.store.save_report(report)
        trends = self.store.get_trends(agent_name="agent_a")
        assert "reports" in trends
        assert trends["trend"] == "improving"


# ---------------------------------------------------------------------------
# Enhanced Evaluation Manager
# ---------------------------------------------------------------------------

class TestEnhancedEvaluationManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = EnhancedEvaluationManager()
        self.manager.store = EvaluationStore(Path(self.tmpdir) / "enhanced.db")

    def test_get_extended_metrics(self):
        result = self.manager.get_extended_metrics(
            conclusion="Patient has diabetes. Consult your doctor.",
            evidence=["Diagnosis: Diabetes", "Medication: Metformin"],
            claims=["Patient has diabetes", "Patient takes metformin"],
            output={
                "conclusion": "Patient has diabetes",
                "review_required": True,
                "confidence": 0.75,
                "uncertainties": ["Lab values pending"],
            },
        )
        assert "factuality" in result
        assert "hallucination_rate" in result
        assert "clinical_safety" in result
        assert 0.0 <= result["factuality"]["score"] <= 1.0

    def test_get_extended_metrics_with_tokens(self):
        result = self.manager.get_extended_metrics(
            conclusion="Diabetes confirmed.",
            evidence=["Diabetes diagnosis"],
            claims=["Patient has diabetes"],
            output={"conclusion": "Diabetes", "review_required": True, "confidence": 0.8},
            token_usage={"input_tokens": 500, "output_tokens": 200},
            cost_usd=0.005,
        )
        assert "token_efficiency" in result
        assert "cost_efficiency" in result


# ---------------------------------------------------------------------------
# Agent Comparator
# ---------------------------------------------------------------------------

class TestAgentComparator:
    def test_build_comparison(self):
        comparator = AgentComparator()

        results_a = [
            EvaluationResult(
                case_id="c1", agent_name="agent_a", status=EvaluationStatus.COMPLETED,
                scores=[MetricScore(metric=MetricType.ACCURACY, score=0.9, explanation="good")],
                overall_score=0.9,
            ),
        ]
        results_b = [
            EvaluationResult(
                case_id="c1", agent_name="agent_b", status=EvaluationStatus.COMPLETED,
                scores=[MetricScore(metric=MetricType.ACCURACY, score=0.7, explanation="ok")],
                overall_score=0.7,
            ),
        ]

        comparison = comparator._build_comparison(
            {"agent_a": results_a, "agent_b": results_b}, []
        )
        assert comparison.winner == "agent_a"
        assert comparison.agents == ["agent_a", "agent_b"]
