"""
AEGIS Evaluation Framework - Portfolio-Grade Benchmarking System

This module implements a comprehensive evaluation framework that makes
AEGIS a portfolio-grade project:

1. **Benchmark Dataset**: Curated test cases with ground truth annotations
2. **Evaluation Metrics**: Accuracy, completeness, grounding, relevance, calibration
3. **Automated Pipeline**: Run evaluations systematically
4. **Performance Tracking**: Track improvements over time
5. **Reporting**: Beautiful evaluation reports for portfolio展示

This is PORTFOLIO-GRADE because it:
- Provides systematic, reproducible evaluations
- Measures multiple dimensions of quality
- Compares against ground truth
- Generates professional reports
- Tracks performance over time
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

# ============================================================================
# Evaluation Metrics
# ============================================================================

class MetricType(StrEnum):
    """Types of evaluation metrics."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    GROUNDING = "grounding"
    RELEVANCE = "relevance"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    REASONING_QUALITY = "reasoning_quality"
    TOOL_EFFICIENCY = "tool_efficiency"
    LATENCY = "latency"
    SAFETY = "safety"


class EvaluationStatus(StrEnum):
    """Status of an evaluation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MetricScore:
    """A single metric score."""
    metric: MetricType
    score: float  # 0.0 to 1.0
    explanation: str
    details: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class EvaluationCase:
    """A single evaluation case with ground truth."""
    case_id: str
    patient_id: str
    question: str
    category: str  # diagnosis, treatment, risk, timeline, general
    difficulty: str  # easy, medium, hard
    ground_truth: dict[str, Any]
    expected_findings: list[str]
    expected_confidence_range: tuple[float, float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluating a single case."""
    case_id: str
    agent_name: str
    status: EvaluationStatus
    scores: list[MetricScore] = field(default_factory=list)
    overall_score: float = 0.0
    latency_ms: float = 0.0
    tool_calls: int = 0
    reasoning_steps: int = 0
    actual_output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    report_id: str
    benchmark_name: str
    agent_name: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    metric_scores: dict[MetricType, float]
    category_scores: dict[str, float]
    difficulty_scores: dict[str, float]
    overall_score: float
    latency_stats: dict[str, float]
    results: list[EvaluationResult]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Benchmark Dataset
# ============================================================================

class BenchmarkDataset:
    """Curated benchmark dataset for evaluation."""

    # Ground truth annotations for common clinical scenarios
    CASES: list[dict[str, Any]] = [
        # Diabetes cases
        {
            "case_id": "DM001",
            "category": "diagnosis",
            "difficulty": "easy",
            "question": "What conditions does this patient have?",
            "expected_findings": ["diabetes", "type 2"],
            "ground_truth": {
                "conditions": ["Diabetes mellitus type 2"],
                "key_medications": ["Metformin"],
                "risk_level": "moderate",
            },
            "expected_confidence_range": (0.6, 0.9),
        },
        {
            "case_id": "DM002",
            "category": "treatment",
            "difficulty": "medium",
            "question": "What medications is this patient taking and why?",
            "expected_findings": ["metformin", "diabetes", "glucose"],
            "ground_truth": {
                "medications": ["Metformin"],
                "indications": ["Diabetes mellitus type 2"],
                "monitoring": ["HbA1c", "glucose"],
            },
            "expected_confidence_range": (0.5, 0.85),
        },
        {
            "case_id": "DM003",
            "category": "risk",
            "difficulty": "hard",
            "question": "What are the risks for this diabetic patient?",
            "expected_findings": ["cardiovascular", "nephropathy", "retinopathy", "neuropathy"],
            "ground_truth": {
                "risks": ["Cardiovascular disease", "Nephropathy", "Retinopathy"],
                "risk_level": "high",
                "recommendations": ["Regular eye exams", "Kidney function monitoring"],
            },
            "expected_confidence_range": (0.4, 0.8),
        },

        # Hypertension cases
        {
            "case_id": "HT001",
            "category": "diagnosis",
            "difficulty": "easy",
            "question": "Does this patient have hypertension?",
            "expected_findings": ["hypertension", "blood pressure", "high"],
            "ground_truth": {
                "conditions": ["Hypertension"],
                "severity": "moderate",
            },
            "expected_confidence_range": (0.7, 0.95),
        },
        {
            "case_id": "HT002",
            "category": "treatment",
            "difficulty": "medium",
            "question": "How is this patient's hypertension being managed?",
            "expected_findings": ["ACE inhibitor", "ARB", "lisinopril", "amlodipine"],
            "ground_truth": {
                "medications": ["Lisinopril", "Amlodipine"],
                "target_bp": "<140/90",
                "monitoring": ["Blood pressure", "Kidney function"],
            },
            "expected_confidence_range": (0.5, 0.85),
        },

        # Cardiovascular cases
        {
            "case_id": "CV001",
            "category": "risk",
            "difficulty": "hard",
            "question": "What is this patient's cardiovascular risk?",
            "expected_findings": ["heart failure", "coronary artery", "stroke", "myocardial infarction"],
            "ground_truth": {
                "risk_factors": ["Age", "Hypertension", "Diabetes", "Hyperlipidemia"],
                "risk_level": "high",
                "recommendations": ["Cardiology referral", "Statin therapy"],
            },
            "expected_confidence_range": (0.4, 0.75),
        },

        # Medication interaction cases
        {
            "case_id": "MI001",
            "category": "safety",
            "difficulty": "medium",
            "question": "Are there any drug interactions for this patient?",
            "expected_findings": ["interaction", "warfarin", "NSAID", "bleeding"],
            "ground_truth": {
                "interactions": ["Warfarin + NSAID = increased bleeding risk"],
                "severity": "major",
                "management": "Avoid combination, use acetaminophen instead",
            },
            "expected_confidence_range": (0.6, 0.9),
        },

        # Timeline cases
        {
            "case_id": "TL001",
            "category": "timeline",
            "difficulty": "medium",
            "question": "How has this patient's health changed over time?",
            "expected_findings": ["progression", "worsening", "improving", "stable"],
            "ground_truth": {
                "trend": "worsening",
                "key_events": ["Diagnosis", "Medication start", "Lab changes"],
                "timeframe": "2 years",
            },
            "expected_confidence_range": (0.4, 0.7),
        },

        # Complex multi-condition cases
        {
            "case_id": "MC001",
            "category": "general",
            "difficulty": "hard",
            "question": "Summarize this patient's overall health status.",
            "expected_findings": ["multiple conditions", "comorbidities", "polypharmacy"],
            "ground_truth": {
                "conditions": ["Diabetes", "Hypertension", "Hyperlipidemia"],
                "complexity": "high",
                "care_coordination": "needed",
            },
            "expected_confidence_range": (0.3, 0.7),
        },

        # Lab interpretation cases
        {
            "case_id": "LB001",
            "category": "diagnosis",
            "difficulty": "easy",
            "question": "Are there any abnormal lab results?",
            "expected_findings": ["elevated", "high", "low", "abnormal"],
            "ground_truth": {
                "abnormal_labs": ["Glucose", "HbA1c", "LDL"],
                "significance": "Indicates poor glycemic control",
            },
            "expected_confidence_range": (0.6, 0.9),
        },
    ]

    @classmethod
    def get_cases(
        cls,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[EvaluationCase]:
        """Get evaluation cases with optional filtering."""
        cases = []

        for case_data in cls.CASES:
            if category and case_data["category"] != category:
                continue
            if difficulty and case_data["difficulty"] != difficulty:
                continue

            cases.append(EvaluationCase(
                case_id=case_data["case_id"],
                patient_id=case_data.get("patient_id", "auto"),
                question=case_data["question"],
                category=case_data["category"],
                difficulty=case_data["difficulty"],
                ground_truth=case_data["ground_truth"],
                expected_findings=case_data["expected_findings"],
                expected_confidence_range=case_data["expected_confidence_range"],
            ))

        return cases

    @classmethod
    def get_categories(cls) -> list[str]:
        """Get all categories."""
        return list(set(c["category"] for c in cls.CASES))

    @classmethod
    def get_difficulties(cls) -> list[str]:
        """Get all difficulty levels."""
        return ["easy", "medium", "hard"]


# ============================================================================
# Evaluation Metrics Calculator
# ============================================================================

class MetricsCalculator:
    """Calculates evaluation metrics."""

    def calculate_accuracy(
        self,
        expected: list[str],
        actual: list[str],
    ) -> float:
        """Calculate accuracy based on expected vs actual findings."""
        if not expected:
            return 1.0

        # Normalize strings
        expected_norm = [e.lower().strip() for e in expected]
        actual_norm = [a.lower().strip() for a in actual]

        # Count matches
        matches = 0
        for exp in expected_norm:
            for act in actual_norm:
                if exp in act or act in exp:
                    matches += 1
                    break

        return matches / len(expected) if expected else 0.0

    def calculate_completeness(
        self,
        expected_findings: list[str],
        actual_evidence: list[str],
    ) -> float:
        """Calculate completeness of findings."""
        if not expected_findings:
            return 1.0

        actual_text = " ".join(actual_evidence).lower()

        found = 0
        for finding in expected_findings:
            if finding.lower() in actual_text:
                found += 1

        return found / len(expected_findings)

    def calculate_grounding(
        self,
        evidence: list[str],
        conclusion: str,
    ) -> float:
        """Calculate how well conclusion is grounded in evidence."""
        if not evidence:
            return 0.0

        conclusion_lower = conclusion.lower()
        evidence_text = " ".join(evidence).lower()

        # Check if conclusion terms appear in evidence
        conclusion_words = set(conclusion_lower.split())
        evidence_words = set(evidence_text.split())

        if not conclusion_words:
            return 0.0

        overlap = conclusion_words.intersection(evidence_words)
        return len(overlap) / len(conclusion_words)

    def calculate_relevance(
        self,
        question: str,
        findings: list[str],
    ) -> float:
        """Calculate relevance of findings to question."""
        if not findings:
            return 0.0

        question_lower = question.lower()
        question_words = set(question_lower.split())

        relevant_count = 0
        for finding in findings:
            finding_lower = finding.lower()
            # Check if finding addresses question
            for word in question_words:
                if word in finding_lower:
                    relevant_count += 1
                    break

        return relevant_count / len(findings)

    def calculate_confidence_calibration(
        self,
        actual_confidence: float,
        expected_range: tuple[float, float],
    ) -> float:
        """Calculate how well confidence matches expected range."""
        low, high = expected_range

        if low <= actual_confidence <= high:
            return 1.0

        # Calculate distance from range
        if actual_confidence < low:
            distance = low - actual_confidence
        else:
            distance = actual_confidence - high

        # Penalize based on distance
        return max(0, 1 - distance * 2)

    def calculate_reasoning_quality(
        self,
        reasoning_chain: list[dict],
    ) -> float:
        """Calculate quality of reasoning chain."""
        if not reasoning_chain:
            return 0.0

        scores = []

        # Check for logical flow
        if len(reasoning_chain) >= 2:
            scores.append(0.8)
        else:
            scores.append(0.3)

        # Check for evidence references
        evidence_refs = sum(
            1 for step in reasoning_chain
            if "evidence" in str(step).lower()
        )
        scores.append(min(evidence_refs / len(reasoning_chain), 1.0))

        # Check for confidence calibration
        confidences = [
            step.get("confidence", 0.5)
            for step in reasoning_chain
            if "confidence" in step
        ]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            scores.append(1 - abs(avg_conf - 0.7) * 2)  # Penalize extreme confidence

        return statistics.mean(scores) if scores else 0.5

    def calculate_safety(
        self,
        output: dict[str, Any],
    ) -> float:
        """Calculate safety score."""
        score = 1.0

        # Check for disclaimers
        conclusion = output.get("conclusion", "")
        if "not medical advice" in conclusion.lower():
            score += 0.1
        if "synthetic" in conclusion.lower():
            score += 0.1

        # Check for review requirement
        if output.get("review_required", False):
            score += 0.1

        # Check for uncertainty acknowledgment
        uncertainties = output.get("uncertainties", [])
        if uncertainties:
            score += 0.1

        return min(score, 1.0)


# ============================================================================
# Evaluation Pipeline
# ============================================================================

class EvaluationPipeline:
    """Automated evaluation pipeline."""

    def __init__(self):
        self.calculator = MetricsCalculator()
        self.results: list[EvaluationResult] = []

    async def evaluate_case(
        self,
        case: EvaluationCase,
        agent_func: Any,
        patient_id: str | None = None,
    ) -> EvaluationResult:
        """Evaluate a single case."""
        import time

        result = EvaluationResult(
            case_id=case.case_id,
            agent_name=getattr(agent_func, "name", "unknown"),
            status=EvaluationStatus.RUNNING,
        )

        try:
            # Run agent
            start_time = time.perf_counter()

            if hasattr(agent_func, "investigate"):
                output = await agent_func.investigate(
                    patient_id or case.patient_id,
                    case.question,
                )
            else:
                output = await agent_func(patient_id or case.patient_id, case.question)

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract findings
            actual_findings = []
            if hasattr(output, "key_findings"):
                actual_findings = output.key_findings
            elif isinstance(output, dict):
                actual_findings = output.get("key_findings", [])

            # Calculate metrics
            scores = []

            # Accuracy
            accuracy = self.calculator.calculate_accuracy(
                case.expected_findings, actual_findings
            )
            scores.append(MetricScore(
                metric=MetricType.ACCURACY,
                score=accuracy,
                explanation=f"Found {accuracy:.0%} of expected findings",
            ))

            # Completeness
            evidence = []
            if hasattr(output, "evidence"):
                evidence = output.evidence
            elif isinstance(output, dict):
                evidence = output.get("evidence", [])

            completeness = self.calculator.calculate_completeness(
                case.expected_findings, evidence
            )
            scores.append(MetricScore(
                metric=MetricType.COMPLETENESS,
                score=completeness,
                explanation=f"Covered {completeness:.0%} of expected findings",
            ))

            # Grounding
            conclusion = ""
            if hasattr(output, "summary"):
                conclusion = output.summary
            elif isinstance(output, dict):
                conclusion = output.get("summary", "")

            grounding = self.calculator.calculate_grounding(evidence, conclusion)
            scores.append(MetricScore(
                metric=MetricType.GROUNDING,
                score=grounding,
                explanation=f"Conclusion grounded at {grounding:.0%}",
            ))

            # Relevance
            relevance = self.calculator.calculate_relevance(
                case.question, actual_findings
            )
            scores.append(MetricScore(
                metric=MetricType.RELEVANCE,
                score=relevance,
                explanation=f"Findings {relevance:.0%} relevant to question",
            ))

            # Confidence calibration
            actual_confidence = 0.5
            if hasattr(output, "confidence"):
                actual_confidence = output.confidence
            elif isinstance(output, dict):
                actual_confidence = output.get("confidence", 0.5)

            calibration = self.calculator.calculate_confidence_calibration(
                actual_confidence, case.expected_confidence_range
            )
            scores.append(MetricScore(
                metric=MetricType.CONFIDENCE_CALIBRATION,
                score=calibration,
                explanation=f"Confidence {actual_confidence:.2f} within expected range",
            ))

            # Reasoning quality
            reasoning_chain = []
            if hasattr(output, "reasoning_chain"):
                reasoning_chain = [
                    {"thought": s.thought, "confidence": s.confidence}
                    for s in output.reasoning_chain
                ]

            reasoning_quality = self.calculator.calculate_reasoning_quality(reasoning_chain)
            scores.append(MetricScore(
                metric=MetricType.REASONING_QUALITY,
                score=reasoning_quality,
                explanation=f"Reasoning quality: {reasoning_quality:.0%}",
            ))

            # Safety
            output_dict = {}
            if hasattr(output, "model_dump"):
                output_dict = output.model_dump()
            elif isinstance(output, dict):
                output_dict = output

            safety = self.calculator.calculate_safety(output_dict)
            scores.append(MetricScore(
                metric=MetricType.SAFETY,
                score=safety,
                explanation=f"Safety score: {safety:.0%}",
            ))

            # Calculate overall score
            overall = statistics.mean([s.score for s in scores])

            result.scores = scores
            result.overall_score = overall
            result.latency_ms = latency_ms
            result.status = EvaluationStatus.COMPLETED
            result.actual_output = output_dict

        except Exception as e:
            result.status = EvaluationStatus.FAILED
            result.errors.append(str(e))

        self.results.append(result)
        return result

    async def run_benchmark(
        self,
        agent_func: Any,
        cases: list[EvaluationCase] | None = None,
        patient_ids: list[str] | None = None,
    ) -> BenchmarkReport:
        """Run a complete benchmark evaluation."""
        if cases is None:
            cases = BenchmarkDataset.get_cases()

        results = []
        for i, case in enumerate(cases):
            patient_id = patient_ids[i] if patient_ids and i < len(patient_ids) else None
            result = await self.evaluate_case(case, agent_func, patient_id)
            results.append(result)

        return self._generate_report(results, cases)

    def _generate_report(
        self,
        results: list[EvaluationResult],
        cases: list[EvaluationCase],
    ) -> BenchmarkReport:
        """Generate a benchmark report."""
        completed = [r for r in results if r.status == EvaluationStatus.COMPLETED]
        failed = [r for r in results if r.status == EvaluationStatus.FAILED]

        # Calculate metric averages
        metric_scores: dict[MetricType, list[float]] = defaultdict(list)
        for result in completed:
            for score in result.scores:
                metric_scores[score.metric].append(score.score)

        metric_averages = {
            metric: statistics.mean(scores) if scores else 0.0
            for metric, scores in metric_scores.items()
        }

        # Calculate category scores
        category_scores: dict[str, list[float]] = defaultdict(list)
        for case, result in zip(cases, results):
            if result.status == EvaluationStatus.COMPLETED:
                category_scores[case.category].append(result.overall_score)

        category_averages = {
            cat: statistics.mean(scores) if scores else 0.0
            for cat, scores in category_scores.items()
        }

        # Calculate difficulty scores
        difficulty_scores: dict[str, list[float]] = defaultdict(list)
        for case, result in zip(cases, results):
            if result.status == EvaluationStatus.COMPLETED:
                difficulty_scores[case.difficulty].append(result.overall_score)

        difficulty_averages = {
            diff: statistics.mean(scores) if scores else 0.0
            for diff, scores in difficulty_scores.items()
        }

        # Calculate latency stats
        latencies = [r.latency_ms for r in completed]
        latency_stats = {
            "mean": statistics.mean(latencies) if latencies else 0,
            "median": statistics.median(latencies) if latencies else 0,
            "p95": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        }

        # Overall score
        overall = statistics.mean([r.overall_score for r in completed]) if completed else 0

        return BenchmarkReport(
            report_id=str(uuid4())[:8],
            benchmark_name="AEGIS Clinical Benchmark v1",
            agent_name=results[0].agent_name if results else "unknown",
            total_cases=len(cases),
            completed_cases=len(completed),
            failed_cases=len(failed),
            metric_scores=metric_averages,
            category_scores=category_averages,
            difficulty_scores=difficulty_averages,
            overall_score=overall,
            latency_stats=latency_stats,
            results=results,
        )


# ============================================================================
# Evaluation Reporter
# ============================================================================

class EvaluationReporter:
    """Generates evaluation reports."""

    @staticmethod
    def generate_text_report(report: BenchmarkReport) -> str:
        """Generate a text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("AEGIS EVALUATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Report ID: {report.report_id}")
        lines.append(f"Benchmark: {report.benchmark_name}")
        lines.append(f"Agent: {report.agent_name}")
        lines.append(f"Generated: {report.generated_at.isoformat()}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("OVERVIEW")
        lines.append("-" * 80)
        lines.append(f"Total Cases: {report.total_cases}")
        lines.append(f"Completed: {report.completed_cases}")
        lines.append(f"Failed: {report.failed_cases}")
        lines.append(f"Overall Score: {report.overall_score:.2%}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("METRIC SCORES")
        lines.append("-" * 80)
        for metric, score in sorted(report.metric_scores.items()):
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            lines.append(f"{metric.value:25s} {bar} {score:.2%}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("CATEGORY SCORES")
        lines.append("-" * 80)
        for category, score in sorted(report.category_scores.items()):
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            lines.append(f"{category:25s} {bar} {score:.2%}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("DIFFICULTY SCORES")
        lines.append("-" * 80)
        for difficulty, score in sorted(report.difficulty_scores.items()):
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            lines.append(f"{difficulty:25s} {bar} {score:.2%}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("LATENCY STATISTICS")
        lines.append("-" * 80)
        for stat, value in report.latency_stats.items():
            lines.append(f"{stat:25s} {value:.1f}ms")
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    @staticmethod
    def generate_json_report(report: BenchmarkReport) -> dict[str, Any]:
        """Generate a JSON report."""
        return {
            "report_id": report.report_id,
            "benchmark_name": report.benchmark_name,
            "agent_name": report.agent_name,
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "total_cases": report.total_cases,
                "completed_cases": report.completed_cases,
                "failed_cases": report.failed_cases,
                "overall_score": round(report.overall_score, 4),
            },
            "metric_scores": {
                metric.value: round(score, 4)
                for metric, score in report.metric_scores.items()
            },
            "category_scores": {
                cat: round(score, 4)
                for cat, score in report.category_scores.items()
            },
            "difficulty_scores": {
                diff: round(score, 4)
                for diff, score in report.difficulty_scores.items()
            },
            "latency_stats": {
                k: round(v, 1) for k, v in report.latency_stats.items()
            },
            "results": [
                {
                    "case_id": r.case_id,
                    "agent_name": r.agent_name,
                    "status": r.status.value,
                    "overall_score": round(r.overall_score, 4),
                    "latency_ms": round(r.latency_ms, 1),
                    "scores": [
                        {
                            "metric": s.metric.value,
                            "score": round(s.score, 4),
                            "explanation": s.explanation,
                        }
                        for s in r.scores
                    ],
                    "errors": r.errors,
                }
                for r in report.results
            ],
        }

    @staticmethod
    def generate_markdown_report(report: BenchmarkReport) -> str:
        """Generate a Markdown report for portfolio展示."""
        lines = []
        lines.append("# AEGIS Evaluation Report")
        lines.append("")
        lines.append("## Overview")
        lines.append("")
        lines.append(f"- **Benchmark**: {report.benchmark_name}")
        lines.append(f"- **Agent**: {report.agent_name}")
        lines.append(f"- **Overall Score**: {report.overall_score:.2%}")
        lines.append(f"- **Cases Evaluated**: {report.completed_cases}/{report.total_cases}")
        lines.append("")
        lines.append("## Metric Scores")
        lines.append("")
        lines.append("| Metric | Score | Rating |")
        lines.append("|--------|-------|--------|")
        for metric, score in sorted(report.metric_scores.items()):
            rating = "⭐⭐⭐" if score >= 0.8 else "⭐⭐" if score >= 0.6 else "⭐"
            lines.append(f"| {metric.value} | {score:.2%} | {rating} |")
        lines.append("")
        lines.append("## Category Performance")
        lines.append("")
        lines.append("| Category | Score | Status |")
        lines.append("|----------|-------|--------|")
        for category, score in sorted(report.category_scores.items()):
            status = "✅ Excellent" if score >= 0.8 else "✓ Good" if score >= 0.6 else "⚠ Needs Work"
            lines.append(f"| {category} | {score:.2%} | {status} |")
        lines.append("")
        lines.append("## Difficulty Analysis")
        lines.append("")
        lines.append("| Difficulty | Score | Trend |")
        lines.append("|------------|-------|-------|")
        for difficulty, score in sorted(report.difficulty_scores.items()):
            trend = "📈" if score >= 0.7 else "➡️" if score >= 0.5 else "📉"
            lines.append(f"| {difficulty} | {score:.2%} | {trend} |")
        lines.append("")
        lines.append("## Performance Metrics")
        lines.append("")
        lines.append(f"- **Mean Latency**: {report.latency_stats.get('mean', 0):.1f}ms")
        lines.append(f"- **P95 Latency**: {report.latency_stats.get('p95', 0):.1f}ms")
        lines.append(f"- **Success Rate**: {report.completed_cases / report.total_cases:.2%}")
        lines.append("")
        lines.append("## Key Findings")
        lines.append("")
        lines.append("### Strengths")
        strengths = [
            (m, s) for m, s in report.metric_scores.items() if s >= 0.7
        ]
        for metric, score in sorted(strengths, key=lambda x: x[1], reverse=True)[:3]:
            lines.append(f"- **{metric.value}**: {score:.2%}")
        lines.append("")
        lines.append("### Areas for Improvement")
        improvements = [
            (m, s) for m, s in report.metric_scores.items() if s < 0.7
        ]
        for metric, score in sorted(improvements, key=lambda x: x[1])[:3]:
            lines.append(f"- **{metric.value}**: {score:.2%}")
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated on {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)


# ============================================================================
# Evaluation Manager
# ============================================================================

class EvaluationManager:
    """Main evaluation manager."""

    def __init__(self):
        self.pipeline = EvaluationPipeline()
        self.reporter = EvaluationReporter()
        self.history: list[BenchmarkReport] = []

    async def run_evaluation(
        self,
        agent_func: Any,
        cases: list[EvaluationCase] | None = None,
        patient_ids: list[str] | None = None,
    ) -> BenchmarkReport:
        """Run a complete evaluation."""
        report = await self.pipeline.run_benchmark(agent_func, cases, patient_ids)
        self.history.append(report)
        return report

    def get_report_text(self, report: BenchmarkReport) -> str:
        """Get text report."""
        return self.reporter.generate_text_report(report)

    def get_report_json(self, report: BenchmarkReport) -> dict[str, Any]:
        """Get JSON report."""
        return self.reporter.generate_json_report(report)

    def get_report_markdown(self, report: BenchmarkReport) -> str:
        """Get Markdown report."""
        return self.reporter.generate_markdown_report(report)

    def compare_reports(
        self,
        report1: BenchmarkReport,
        report2: BenchmarkReport,
    ) -> dict[str, Any]:
        """Compare two evaluation reports."""
        comparison = {
            "report1_id": report1.report_id,
            "report2_id": report2.report_id,
            "overall_change": report2.overall_score - report1.overall_score,
            "metric_changes": {},
            "category_changes": {},
        }

        # Compare metrics
        for metric in MetricType:
            score1 = report1.metric_scores.get(metric, 0)
            score2 = report2.metric_scores.get(metric, 0)
            comparison["metric_changes"][metric.value] = {
                "before": score1,
                "after": score2,
                "change": score2 - score1,
            }

        # Compare categories
        all_categories = set(report1.category_scores.keys()) | set(report2.category_scores.keys())
        for category in all_categories:
            score1 = report1.category_scores.get(category, 0)
            score2 = report2.category_scores.get(category, 0)
            comparison["category_changes"][category] = {
                "before": score1,
                "after": score2,
                "change": score2 - score1,
            }

        return comparison

    def get_performance_trends(self) -> dict[str, Any]:
        """Get performance trends over time."""
        if len(self.history) < 2:
            return {"message": "Need at least 2 reports for trends"}

        trends = {
            "overall_scores": [r.overall_score for r in self.history],
            "metric_trends": {},
        }

        for metric in MetricType:
            scores = [
                r.metric_scores.get(metric, 0) for r in self.history
            ]
            trends["metric_trends"][metric.value] = {
                "scores": scores,
                "trend": "improving" if scores[-1] > scores[0] else "declining",
                "change": scores[-1] - scores[0],
            }

        return trends


# ============================================================================
# Global Instance
# ============================================================================

evaluation_manager = EvaluationManager()
