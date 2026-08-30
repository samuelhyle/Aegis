"""
Tests for Evaluation Framework

Comprehensive tests for the portfolio-grade evaluation system including:
- Benchmark dataset
- Metrics calculation
- Evaluation pipeline
- Reporting
- API endpoints
"""

import os
from unittest.mock import MagicMock

import pytest

# Set test environment
os.environ["AEGIS_AUTH_DISABLED"] = "true"
os.environ["AEGIS_RATE_LIMIT_DISABLED"] = "true"

from aegis.evaluation_framework import (
    BenchmarkDataset,
    BenchmarkReport,
    EvaluationCase,
    EvaluationManager,
    EvaluationPipeline,
    EvaluationReporter,
    EvaluationResult,
    EvaluationStatus,
    MetricsCalculator,
    MetricScore,
    MetricType,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def calculator():
    """Create a metrics calculator."""
    return MetricsCalculator()


@pytest.fixture
def pipeline():
    """Create an evaluation pipeline."""
    return EvaluationPipeline()


@pytest.fixture
def manager():
    """Create an evaluation manager."""
    return EvaluationManager()


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi.testclient import TestClient

    from aegis.api import app
    return TestClient(app)


@pytest.fixture
def sample_case():
    """Create a sample evaluation case."""
    return EvaluationCase(
        case_id="TEST001",
        patient_id="test_patient",
        question="What conditions does this patient have?",
        category="diagnosis",
        difficulty="easy",
        ground_truth={"conditions": ["Diabetes", "Hypertension"]},
        expected_findings=["diabetes", "hypertension"],
        expected_confidence_range=(0.6, 0.9),
    )


@pytest.fixture
def sample_result():
    """Create a sample evaluation result."""
    return EvaluationResult(
        case_id="TEST001",
        agent_name="test_agent",
        status=EvaluationStatus.COMPLETED,
        scores=[
            MetricScore(
                metric=MetricType.ACCURACY,
                score=0.8,
                explanation="Found 80% of expected findings",
            ),
            MetricScore(
                metric=MetricType.COMPLETENESS,
                score=0.7,
                explanation="Covered 70% of expected findings",
            ),
        ],
        overall_score=0.75,
        latency_ms=100.0,
    )


@pytest.fixture
def sample_report():
    """Create a sample benchmark report."""
    return BenchmarkReport(
        report_id="test_report",
        benchmark_name="Test Benchmark",
        agent_name="test_agent",
        total_cases=10,
        completed_cases=9,
        failed_cases=1,
        metric_scores={
            MetricType.ACCURACY: 0.8,
            MetricType.COMPLETENESS: 0.7,
            MetricType.GROUNDING: 0.75,
        },
        category_scores={
            "diagnosis": 0.8,
            "treatment": 0.7,
        },
        difficulty_scores={
            "easy": 0.9,
            "medium": 0.7,
            "hard": 0.5,
        },
        overall_score=0.75,
        latency_stats={
            "mean": 150.0,
            "median": 120.0,
            "p95": 300.0,
        },
        results=[],
    )


# ============================================================================
# Test Benchmark Dataset
# ============================================================================

class TestBenchmarkDataset:
    """Tests for BenchmarkDataset."""

    def test_get_all_cases(self):
        """Test getting all cases."""
        cases = BenchmarkDataset.get_cases()
        assert len(cases) > 0
        assert all(isinstance(c, EvaluationCase) for c in cases)

    def test_get_cases_by_category(self):
        """Test filtering by category."""
        cases = BenchmarkDataset.get_cases(category="diagnosis")
        assert all(c.category == "diagnosis" for c in cases)

    def test_get_cases_by_difficulty(self):
        """Test filtering by difficulty."""
        cases = BenchmarkDataset.get_cases(difficulty="easy")
        assert all(c.difficulty == "easy" for c in cases)

    def test_get_categories(self):
        """Test getting categories."""
        categories = BenchmarkDataset.get_categories()
        assert len(categories) > 0
        assert "diagnosis" in categories

    def test_get_difficulties(self):
        """Test getting difficulties."""
        difficulties = BenchmarkDataset.get_difficulties()
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties

    def test_case_structure(self, sample_case):
        """Test case structure."""
        assert sample_case.case_id == "TEST001"
        assert sample_case.category == "diagnosis"
        assert len(sample_case.expected_findings) > 0
        assert 0 <= sample_case.expected_confidence_range[0] <= 1
        assert 0 <= sample_case.expected_confidence_range[1] <= 1


# ============================================================================
# Test Metrics Calculator
# ============================================================================

class TestMetricsCalculator:
    """Tests for MetricsCalculator."""

    def test_accuracy_perfect(self, calculator):
        """Test perfect accuracy."""
        score = calculator.calculate_accuracy(
            ["diabetes", "hypertension"],
            ["diabetes", "hypertension"],
        )
        assert score == 1.0

    def test_accuracy_partial(self, calculator):
        """Test partial accuracy."""
        score = calculator.calculate_accuracy(
            ["diabetes", "hypertension", "obesity"],
            ["diabetes", "hypertension"],
        )
        assert 0.5 < score < 1.0

    def test_accuracy_none(self, calculator):
        """Test no accuracy."""
        score = calculator.calculate_accuracy(
            ["diabetes", "hypertension"],
            ["cancer", "asthma"],
        )
        assert score == 0.0

    def test_accuracy_empty_expected(self, calculator):
        """Test accuracy with empty expected."""
        score = calculator.calculate_accuracy([], ["diabetes"])
        assert score == 1.0

    def test_completeness_perfect(self, calculator):
        """Test perfect completeness."""
        score = calculator.calculate_completeness(
            ["diabetes", "hypertension"],
            ["Patient has diabetes and hypertension"],
        )
        assert score == 1.0

    def test_completeness_partial(self, calculator):
        """Test partial completeness."""
        score = calculator.calculate_completeness(
            ["diabetes", "hypertension", "obesity"],
            ["Patient has diabetes"],
        )
        assert 0 < score < 1

    def test_grounding_high(self, calculator):
        """Test high grounding."""
        score = calculator.calculate_grounding(
            ["Patient has diabetes", "Glucose levels elevated"],
            "Patient has diabetes with elevated glucose",
        )
        assert score > 0.5

    def test_grounding_low(self, calculator):
        """Test low grounding."""
        score = calculator.calculate_grounding(
            ["Patient has diabetes"],
            "Cancer treatment recommended",
        )
        assert score < 0.5

    def test_relevance_high(self, calculator):
        """Test high relevance."""
        score = calculator.calculate_relevance(
            "What conditions does this patient have?",
            ["Patient has diabetes", "Patient has hypertension"],
        )
        assert score > 0.5

    def test_confidence_calibration_in_range(self, calculator):
        """Test confidence calibration in range."""
        score = calculator.calculate_confidence_calibration(
            0.7, (0.6, 0.9)
        )
        assert score == 1.0

    def test_confidence_calibration_out_of_range(self, calculator):
        """Test confidence calibration out of range."""
        score = calculator.calculate_confidence_calibration(
            0.3, (0.6, 0.9)
        )
        assert score < 1.0

    def test_reasoning_quality(self, calculator):
        """Test reasoning quality calculation."""
        chain = [
            {"thought": "Analyzing conditions", "confidence": 0.7},
            {"thought": "Checking medications", "confidence": 0.8},
            {"thought": "Synthesizing findings", "confidence": 0.75},
        ]
        score = calculator.calculate_reasoning_quality(chain)
        assert 0 < score <= 1

    def test_safety_with_disclaimer(self, calculator):
        """Test safety with disclaimer."""
        output = {
            "conclusion": "This is not medical advice. Synthetic data used.",
            "review_required": True,
            "uncertainties": ["Need more data"],
        }
        score = calculator.calculate_safety(output)
        assert score > 0.5


# ============================================================================
# Test Evaluation Pipeline
# ============================================================================

class TestEvaluationPipeline:
    """Tests for EvaluationPipeline."""

    @pytest.mark.asyncio
    async def test_evaluate_case(self, pipeline, sample_case):
        """Test evaluating a single case."""
        # Create mock agent
        async def mock_agent(patient_id, question):
            return MagicMock(
                key_findings=["diabetes", "hypertension"],
                evidence=["Patient has diabetes", "Patient has hypertension"],
                summary="Patient has diabetes and hypertension",
                confidence=0.75,
                reasoning_chain=[],
                model_dump=lambda: {"summary": "test"},
            )

        result = await pipeline.evaluate_case(sample_case, mock_agent)

        assert result.status == EvaluationStatus.COMPLETED
        assert result.overall_score > 0
        assert len(result.scores) > 0

    @pytest.mark.asyncio
    async def test_evaluate_case_failure(self, pipeline, sample_case):
        """Test evaluating a case that fails."""
        async def failing_agent(patient_id, question):
            raise ValueError("Agent failed")

        result = await pipeline.evaluate_case(sample_case, failing_agent)

        assert result.status == EvaluationStatus.FAILED
        assert len(result.errors) > 0


# ============================================================================
# Test Evaluation Reporter
# ============================================================================

class TestEvaluationReporter:
    """Tests for EvaluationReporter."""

    def test_generate_text_report(self, sample_report):
        """Test text report generation."""
        reporter = EvaluationReporter()
        report_text = reporter.generate_text_report(sample_report)

        assert "AEGIS EVALUATION REPORT" in report_text
        assert "OVERVIEW" in report_text
        assert "METRIC SCORES" in report_text
        assert "Overall Score" in report_text

    def test_generate_json_report(self, sample_report):
        """Test JSON report generation."""
        reporter = EvaluationReporter()
        report_json = reporter.generate_json_report(sample_report)

        assert "report_id" in report_json
        assert "summary" in report_json
        assert "metric_scores" in report_json
        assert report_json["summary"]["overall_score"] == 0.75

    def test_generate_markdown_report(self, sample_report):
        """Test Markdown report generation."""
        reporter = EvaluationReporter()
        report_md = reporter.generate_markdown_report(sample_report)

        assert "# AEGIS Evaluation Report" in report_md
        assert "## Overview" in report_md
        assert "## Metric Scores" in report_md
        assert "## Category Performance" in report_md


# ============================================================================
# Test Evaluation Manager
# ============================================================================

class TestEvaluationManager:
    """Tests for EvaluationManager."""

    def test_compare_reports(self, manager, sample_report):
        """Test comparing reports."""
        report1 = sample_report
        report2 = BenchmarkReport(
            report_id="test_report_2",
            benchmark_name="Test Benchmark",
            agent_name="test_agent",
            total_cases=10,
            completed_cases=10,
            failed_cases=0,
            metric_scores={
                MetricType.ACCURACY: 0.9,
                MetricType.COMPLETENESS: 0.8,
                MetricType.GROUNDING: 0.85,
            },
            category_scores={
                "diagnosis": 0.9,
                "treatment": 0.8,
            },
            difficulty_scores={
                "easy": 0.95,
                "medium": 0.8,
                "hard": 0.6,
            },
            overall_score=0.85,
            latency_stats={"mean": 100.0},
            results=[],
        )

        comparison = manager.compare_reports(report1, report2)

        assert comparison["overall_change"] > 0
        assert "metric_changes" in comparison
        assert "category_changes" in comparison

    def test_get_performance_trends(self, manager):
        """Test getting performance trends."""
        # Add some history
        for i in range(3):
            report = BenchmarkReport(
                report_id=f"report_{i}",
                benchmark_name="Test",
                agent_name="test",
                total_cases=10,
                completed_cases=10,
                failed_cases=0,
                metric_scores={MetricType.ACCURACY: 0.7 + i * 0.05},
                category_scores={},
                difficulty_scores={},
                overall_score=0.7 + i * 0.05,
                latency_stats={},
                results=[],
            )
            manager.history.append(report)

        trends = manager.get_performance_trends()

        assert "overall_scores" in trends
        assert "metric_trends" in trends
        assert len(trends["overall_scores"]) == 3


# ============================================================================
# Test Metric Types
# ============================================================================

class TestMetricTypes:
    """Tests for metric types."""

    def test_metric_type_values(self):
        """Test metric type values."""
        assert MetricType.ACCURACY.value == "accuracy"
        assert MetricType.COMPLETENESS.value == "completeness"
        assert MetricType.GROUNDING.value == "grounding"
        assert MetricType.RELEVANCE.value == "relevance"
        assert MetricType.SAFETY.value == "safety"

    def test_evaluation_status_values(self):
        """Test evaluation status values."""
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.RUNNING.value == "running"
        assert EvaluationStatus.COMPLETED.value == "completed"
        assert EvaluationStatus.FAILED.value == "failed"


# ============================================================================
# Test Data Structures
# ============================================================================

class TestDataStructures:
    """Tests for data structures."""

    def test_metric_score(self):
        """Test MetricScore creation."""
        score = MetricScore(
            metric=MetricType.ACCURACY,
            score=0.85,
            explanation="Good accuracy",
        )
        assert score.metric == MetricType.ACCURACY
        assert score.score == 0.85

    def test_evaluation_case(self, sample_case):
        """Test EvaluationCase creation."""
        assert sample_case.case_id == "TEST001"
        assert len(sample_case.expected_findings) > 0

    def test_evaluation_result(self, sample_result):
        """Test EvaluationResult creation."""
        assert sample_result.status == EvaluationStatus.COMPLETED
        assert sample_result.overall_score == 0.75

    def test_benchmark_report(self, sample_report):
        """Test BenchmarkReport creation."""
        assert sample_report.total_cases == 10
        assert sample_report.overall_score == 0.75
        assert len(sample_report.metric_scores) > 0


# ============================================================================
# Test API Endpoints
# ============================================================================

class TestEvaluationAPI:
    """Tests for evaluation API endpoints."""

    def test_get_benchmark_cases(self, client):
        """Test getting benchmark cases."""
        response = client.get("/v2/evaluation/benchmark")
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert data["total"] > 0

    def test_get_benchmark_cases_filtered(self, client):
        """Test getting filtered benchmark cases."""
        response = client.get("/v2/evaluation/benchmark?category=diagnosis")
        assert response.status_code == 200
        data = response.json()
        assert all(c["category"] == "diagnosis" for c in data["cases"])

    def test_get_evaluation_metrics(self, client):
        """Test getting evaluation metrics."""
        response = client.get("/v2/evaluation/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert len(data["metrics"]) > 0

    def test_get_evaluation_history(self, client):
        """Test getting evaluation history."""
        response = client.get("/v2/evaluation/history")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data

    def test_get_evaluation_trends(self, client):
        """Test getting evaluation trends."""
        response = client.get("/v2/evaluation/trends")
        assert response.status_code == 200
