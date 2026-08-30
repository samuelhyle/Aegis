from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Confidence Thresholds
# ---------------------------------------------------------------------------

class ConfidenceTier(StrEnum):
    """Confidence tiers with corresponding actions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


@dataclass
class ConfidenceThresholds:
    """Configurable confidence thresholds for gating."""
    high: float = 0.85
    medium: float = 0.70
    low: float = 0.50
    block_below: float = 0.30

    def classify(self, confidence: float) -> ConfidenceTier:
        if confidence >= self.high:
            return ConfidenceTier.HIGH
        if confidence >= self.medium:
            return ConfidenceTier.MEDIUM
        if confidence >= self.low:
            return ConfidenceTier.LOW
        return ConfidenceTier.CRITICAL

    def should_block(self, confidence: float) -> bool:
        return confidence < self.block_below

    def requires_review(self, confidence: float) -> bool:
        return confidence < self.high


@dataclass
class ConfidenceGate:
    """Enforces confidence thresholds on investigation outputs."""
    thresholds: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)

    def evaluate(
        self, confidence: float, is_medical: bool = True
    ) -> dict[str, Any]:
        tier = self.thresholds.classify(confidence)
        blocked = self.thresholds.should_block(confidence)
        needs_review = self.thresholds.requires_review(confidence)

        if is_medical and confidence < self.thresholds.high:
            needs_review = True

        return {
            "tier": tier.value,
            "confidence": confidence,
            "blocked": blocked,
            "review_required": needs_review,
            "message": self._message(tier, blocked, needs_review),
        }

    @staticmethod
    def _message(
        tier: ConfidenceTier, blocked: bool, review_required: bool
    ) -> str:
        if blocked:
            return "Confidence too low. Output blocked. Requires manual review."
        if review_required:
            return f"Confidence tier: {tier.value}. Human review required."
        return f"Confidence tier: {tier.value}. Auto-approved."


# ---------------------------------------------------------------------------
# Contradiction Detection
# ---------------------------------------------------------------------------

class ContradictionSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Contradiction:
    """A detected contradiction between statements."""
    statement_a: str
    statement_b: str
    source_a: str
    source_b: str
    severity: ContradictionSeverity
    explanation: str
    topic: str = ""


class ContradictionDetector:
    """Detects contradictions between agent conclusions and evidence."""

    NEGATION_PAIRS = [
        ("normal", "abnormal"),
        ("normal", "elevated"),
        ("normal", "decreased"),
        ("high", "low"),
        ("elevated", "decreased"),
        ("positive", "negative"),
        ("acute", "chronic"),
        ("present", "absent"),
        ("increased", "decreased"),
        ("stable", "unstable"),
        ("safe", "unsafe"),
        ("effective", "ineffective"),
        ("improving", "deteriorating"),
    ]

    MEDICAL_CONTRADICTION_PATTERNS = [
        (r"no\s+evidence\s+of\s+\w+", r"evidence\s+of\s+\w+"),
        (r"normal\s+\w+", r"abnormal\s+\w+"),
        (r"normal\s+\w+", r"elevated\s+\w+"),
        (r"(\w+)\s+resolved", r"(\w+)\s+active"),
        (r"no\s+medication", r"currently\s+on\s+medication"),
        (r"low\s+risk", r"high\s+risk"),
        (r"improving", r"deteriorating"),
    ]

    def detect_contradictions(
        self,
        statements: list[dict[str, Any]],
    ) -> list[Contradiction]:
        contradictions = []

        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                a = statements[i]
                b = statements[j]
                found = self._check_pair(a, b)
                contradictions.extend(found)

        return contradictions

    def _check_pair(
        self, a: dict[str, Any], b: dict[str, Any]
    ) -> list[Contradiction]:
        text_a = a.get("text", "").lower()
        text_b = b.get("text", "").lower()
        source_a = a.get("source", "unknown")
        source_b = b.get("source", "unknown")
        contradictions = []

        for neg, pos in self.NEGATION_PAIRS:
            if neg in text_a and pos in text_b:
                contradictions.append(Contradiction(
                    statement_a=a.get("text", ""),
                    statement_b=b.get("text", ""),
                    source_a=source_a,
                    source_b=source_b,
                    severity=ContradictionSeverity.MEDIUM,
                    explanation=f"Statement A uses '{neg}' while B uses '{pos}'",
                ))

        for pattern_a, pattern_b in self.MEDICAL_CONTRADICTION_PATTERNS:
            if re.search(pattern_a, text_a) and re.search(pattern_b, text_b):
                contradictions.append(Contradiction(
                    statement_a=a.get("text", ""),
                    statement_b=b.get("text", ""),
                    source_a=source_a,
                    source_b=source_b,
                    severity=ContradictionSeverity.HIGH,
                    explanation=f"Pattern-based contradiction: '{pattern_a}' vs '{pattern_b}'",
                ))

        return contradictions

    def check_conclusion_vs_evidence(
        self,
        conclusion: str,
        evidence: list[str],
        source_id: str = "conclusion",
    ) -> list[Contradiction]:
        contradictions = []
        conclusion_lower = conclusion.lower()

        for ev in evidence:
            ev_lower = ev.lower()
            for neg, pos in self.NEGATION_PAIRS:
                if (neg in conclusion_lower and pos in ev_lower) or (
                    pos in conclusion_lower and neg in ev_lower
                ):
                    contradictions.append(Contradiction(
                        statement_a=conclusion,
                        statement_b=ev,
                        source_a=source_id,
                        source_b="evidence",
                        severity=ContradictionSeverity.HIGH,
                        explanation=f"Conclusion uses '{neg if neg in conclusion_lower else pos}' but evidence suggests '{pos if neg in conclusion_lower else neg}'",
                    ))

        return contradictions

    def score_contradictions(
        self, contradictions: list[Contradiction]
    ) -> dict[str, Any]:
        if not contradictions:
            return {"count": 0, "severity": "none", "score": 0.0}

        severity_weights = {
            ContradictionSeverity.LOW: 0.25,
            ContradictionSeverity.MEDIUM: 0.50,
            ContradictionSeverity.HIGH: 0.75,
            ContradictionSeverity.CRITICAL: 1.0,
        }

        total = sum(severity_weights[c.severity] for c in contradictions)
        avg = total / len(contradictions)

        if avg >= 0.75:
            severity = "critical"
        elif avg >= 0.50:
            severity = "high"
        elif avg >= 0.25:
            severity = "medium"
        else:
            severity = "low"

        return {
            "count": len(contradictions),
            "severity": severity,
            "score": round(avg, 3),
            "details": [
                {
                    "sources": f"{c.source_a} vs {c.source_b}",
                    "severity": c.severity.value,
                    "explanation": c.explanation,
                }
                for c in contradictions[:10]
            ],
        }


# ---------------------------------------------------------------------------
# Prompt Injection Defenses
# ---------------------------------------------------------------------------

class InjectionSeverity(StrEnum):
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"


@dataclass
class InjectionResult:
    """Result of prompt injection check."""
    safe: bool
    detections: list[dict[str, Any]]
    sanitized_input: str
    risk_score: float = 0.0


class PromptInjectionDefender:
    """Detects and mitigates prompt injection attacks."""

    BLOCKED_PATTERNS = [
        (r"ignore\s+(all\s+)?previous\s+instructions", 0.95),
        (r"ignore\s+(all\s+)?prior\s+instructions", 0.95),
        (r"disregard\s+(all\s+)?instructions", 0.90),
        (r"forget\s+(all\s+)?instructions", 0.90),
        (r"override\s+(all\s+)?instructions", 0.90),
        (r"you\s+are\s+now\s+(a|an)\s+\w+", 0.70),
        (r"act\s+as\s+(a|an)\s+\w+\s+instead", 0.80),
        (r"pretend\s+you\s+are\s+(a|an)\s+\w+", 0.80),
        (r"from\s+now\s+on\s+you\s+are", 0.85),
        (r"new\s+instructions:", 0.75),
        (r"system\s*:\s*", 0.60),
        (r"assistant\s*:\s*", 0.50),
        (r"\[INST\]", 0.85),
        (r"<<SYS>>", 0.85),
        (r"<\|im_start\|>", 0.85),
        (r"<\|im_end\|>", 0.85),
        (r"###\s*system", 0.70),
        (r"###\s*assistant", 0.60),
    ]

    CLINICAL_BOUNDARY_PATTERNS = [
        r"(?i)what\s+are\s+your\s+instructions",
        r"(?i)reveal\s+(your\s+)?(system|prompt|instructions)",
        r"(?i)show\s+me\s+(your\s+)?(system|prompt|instructions)",
        r"(?i)print\s+(your\s+)?(system|prompt|instructions)",
        r"(?i)repeat\s+(your\s+)?(system|prompt|instructions)",
        r"(?i)what\s+(system|prompt)\s+(do\s+you|are\s+you)\s+(running|using)",
    ]

    def check(self, user_input: str) -> InjectionResult:
        detections = []
        max_risk = 0.0

        for pattern, risk in self.BLOCKED_PATTERNS:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "risk_score": risk,
                    "action": "block" if risk >= 0.8 else "warn",
                })
                max_risk = max(max_risk, risk)

        for pattern in self.CLINICAL_BOUNDARY_PATTERNS:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                detections.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "risk_score": 0.7,
                    "action": "warn",
                })
                max_risk = max(max_risk, 0.7)

        sanitized = self._sanitize(user_input)
        safe = max_risk < 0.8

        return InjectionResult(
            safe=safe,
            detections=detections,
            sanitized_input=sanitized,
            risk_score=max_risk,
        )

    def _sanitize(self, text: str) -> str:
        sanitized = text
        sanitized = re.sub(r"<<SYS>>.*?</<SYS>>", "[REDACTED]", sanitized, flags=re.DOTALL)
        sanitized = re.sub(r"\[INST\].*?\[/INST\]", "[REDACTED]", sanitized, flags=re.DOTALL)
        sanitized = re.sub(r"<\|im_start\|>.*?<\|im_end\|>", "[REDACTED]", sanitized, flags=re.DOTALL)
        return sanitized

    def validate_prompt_length(self, prompt: str, max_tokens: int = 4000) -> dict[str, Any]:
        est_tokens = len(prompt.split()) * 1.3
        valid = est_tokens <= max_tokens
        return {
            "valid": valid,
            "estimated_tokens": int(est_tokens),
            "max_tokens": max_tokens,
            "utilization": round(est_tokens / max_tokens, 2),
        }


# ---------------------------------------------------------------------------
# PII Checks
# ---------------------------------------------------------------------------

class PIIType(StrEnum):
    SSN = "ssn"
    PHONE = "phone"
    EMAIL = "email"
    NAME = "name"
    DOB = "dob"
    MRN = "mrn"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"


@dataclass
class PIIDetection:
    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float
    redacted: str


class PIIDetector:
    """Detects and redacts PII in text."""

    PATTERNS = {
        PIIType.SSN: (
            r"\b\d{3}-\d{2}-\d{4}\b",
            0.95,
        ),
        PIIType.PHONE: (
            r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            0.85,
        ),
        PIIType.EMAIL: (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            0.95,
        ),
        PIIType.DOB: (
            r"\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/\d{4}\b",
            0.80,
        ),
        PIIType.DOB: (
            r"\b\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b",
            0.80,
        ),
        PIIType.MRN: (
            r"\bMRN[:\s]*\d{6,10}\b",
            0.75,
        ),
        PIIType.IP_ADDRESS: (
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            0.70,
        ),
    }

    def detect(self, text: str) -> list[PIIDetection]:
        detections = []

        for pii_type, (pattern, confidence) in self.PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                redacted = f"[{pii_type.value.upper()}-REDACTED]"
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                    redacted=redacted,
                ))

        return sorted(detections, key=lambda d: d.start)

    def redact(self, text: str) -> tuple[str, list[PIIDetection]]:
        detections = self.detect(text)
        if not detections:
            return text, []

        redacted_parts = []
        last_end = 0

        for det in detections:
            redacted_parts.append(text[last_end:det.start])
            redacted_parts.append(det.redacted)
            last_end = det.end

        redacted_parts.append(text[last_end:])
        return "".join(redacted_parts), detections

    def has_pii(self, text: str, min_confidence: float = 0.7) -> bool:
        return any(d.confidence >= min_confidence for d in self.detect(text))


# ---------------------------------------------------------------------------
# Human-in-the-Loop Gate
# ---------------------------------------------------------------------------

class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


@dataclass
class HumanGateDecision:
    """Decision from the human-in-the-loop gate."""
    status: ReviewStatus
    confidence_tier: ConfidenceTier
    contradictions: dict[str, Any]
    injection_check: InjectionResult
    pii_check: bool
    requires_review: bool
    block_reasons: list[str]
    report_id: str = ""


class HumanApprovalGate:
    """Enforces human review for investigations."""

    def __init__(
        self,
        confidence_thresholds: ConfidenceThresholds | None = None,
    ):
        self.confidence_gate = ConfidenceGate(
            confidence_thresholds or ConfidenceThresholds()
        )
        self.contradiction_detector = ContradictionDetector()
        self.injection_defender = PromptInjectionDefender()
        self.pii_detector = PIIDetector()

    def evaluate(
        self,
        confidence: float,
        conclusion: str,
        evidence: list[str],
        user_question: str = "",
        report_id: str = "",
    ) -> HumanGateDecision:
        conf_eval = self.confidence_gate.evaluate(confidence)

        contradiction_statements = [{"text": conclusion, "source": "conclusion"}]
        for i, ev in enumerate(evidence[:10]):
            contradiction_statements.append({"text": ev, "source": f"evidence_{i}"})

        contradictions = self.contradiction_detector.detect_contradictions(
            contradiction_statements
        )
        contradiction_score = self.contradiction_detector.score_contradictions(contradictions)

        injection_result = self.injection_defender.check(user_question) if user_question else InjectionResult(
            safe=True, detections=[], sanitized_input=user_question, risk_score=0.0
        )

        pii_present = self.pii_detector.has_pii(conclusion)

        block_reasons = []
        if conf_eval["blocked"]:
            block_reasons.append(f"Confidence too low ({confidence:.2f})")
        if contradiction_score["severity"] in ("critical", "high"):
            block_reasons.append(f"High-severity contradictions detected ({contradiction_score['count']} issues)")
        if not injection_result.safe:
            block_reasons.append("Prompt injection detected in user input")
        if pii_present:
            block_reasons.append("PII detected in conclusion output")

        requires_review = conf_eval["review_required"] or len(block_reasons) > 0

        return HumanGateDecision(
            status=ReviewStatus.PENDING if requires_review else ReviewStatus.APPROVED,
            confidence_tier=self.confidence_gate.thresholds.classify(confidence),
            contradictions=contradiction_score,
            injection_check=injection_result,
            pii_check=pii_present,
            requires_review=requires_review,
            block_reasons=block_reasons,
            report_id=report_id,
        )


# ---------------------------------------------------------------------------
# Audit Logger (file-backed)
# ---------------------------------------------------------------------------

class AuditSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    event_id: str
    event_type: str
    severity: AuditSeverity
    message: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    trace_id: str = ""
    ip_address: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "user_id": self.user_id,
            "trace_id": self.trace_id,
            "ip_address": self.ip_address,
        }


class SafetyAuditLogger:
    """Audit logger with integrity verification via hash chaining."""

    def __init__(self, log_file: str | None = None, max_entries: int = 50000):
        self._entries: list[AuditEntry] = []
        self._log_file = log_file
        self._max_entries = max_entries
        self._chain_hash: str = "genesis"

    def log(
        self,
        event_type: str,
        severity: AuditSeverity,
        message: str,
        details: dict[str, Any] | None = None,
        user_id: str = "",
        trace_id: str = "",
        ip_address: str = "",
    ) -> AuditEntry:
        import uuid
        entry = AuditEntry(
            event_id=str(uuid.uuid4())[:12],
            event_type=event_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
            user_id=user_id,
            trace_id=trace_id,
            ip_address=ip_address,
        )

        prev_hash = self._chain_hash
        entry_data = f"{entry.event_id}:{entry.event_type}:{entry.timestamp.isoformat()}:{prev_hash}"
        self._chain_hash = hashlib.sha256(entry_data.encode()).hexdigest()[:16]

        self._entries.append(entry)

        if self._log_file:
            self._append_to_file(entry)

        return entry

    def _append_to_file(self, entry: AuditEntry) -> None:
        import json
        try:
            with open(self._log_file, "a") as f:
                data = entry.to_dict()
                data["chain_hash"] = self._chain_hash
                f.write(json.dumps(data) + "\n")
        except Exception:
            pass

    def verify_integrity(self) -> dict[str, Any]:
        if not self._entries:
            return {"valid": True, "entries": 0}

        chain = "genesis"

        for i, entry in enumerate(self._entries):
            prev_hash = chain
            entry_data = f"{entry.event_id}:{entry.event_type}:{entry.timestamp.isoformat()}:{prev_hash}"
            expected = hashlib.sha256(entry_data.encode()).hexdigest()[:16]
            chain = expected

        valid = self._chain_hash == chain
        return {
            "valid": valid,
            "entries": len(self._entries),
            "last_hash": self._chain_hash,
        }

    def query(
        self,
        event_type: str | None = None,
        severity: AuditSeverity | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        results = self._entries

        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if severity:
            results = [e for e in results if e.severity == severity]
        if trace_id:
            results = [e for e in results if e.trace_id == trace_id]

        return results[-limit:]

    def export(self, format: str = "json") -> str:
        if format == "json":
            import json
            return json.dumps([e.to_dict() for e in self._entries], indent=2)
        elif format == "csv":
            lines = ["event_id,event_type,severity,message,timestamp,trace_id"]
            for e in self._entries:
                lines.append(
                    f"{e.event_id},{e.event_type},{e.severity.value},"
                    f'"{e.message}",{e.timestamp.isoformat()},{e.trace_id}'
                )
            return "\n".join(lines)
        return ""


# ---------------------------------------------------------------------------
# Safety Gate Integration
# ---------------------------------------------------------------------------

class SafetyGate:
    """Unified safety gate combining all Phase 4 safety components."""

    def __init__(
        self,
        confidence_thresholds: ConfidenceThresholds | None = None,
        audit_log: SafetyAuditLogger | None = None,
    ):
        self.confidence_gate = ConfidenceGate(confidence_thresholds or ConfidenceThresholds())
        self.contradiction_detector = ContradictionDetector()
        self.injection_defender = PromptInjectionDefender()
        self.pii_detector = PIIDetector()
        self.human_gate = HumanApprovalGate(confidence_thresholds)
        self.audit_logger = audit_log or SafetyAuditLogger()

    def check_input(self, user_input: str, trace_id: str = "") -> dict[str, Any]:
        injection = self.injection_defender.check(user_input)
        length_check = self.injection_defender.validate_prompt_length(user_input)
        pii_detections = self.pii_detector.detect(user_input)

        safe = injection.safe and length_check["valid"]
        risk_score = injection.risk_score

        self.audit_logger.log(
            event_type="input_check",
            severity=AuditSeverity.WARNING if not safe else AuditSeverity.INFO,
            message=f"Input check: safe={safe}, risk={risk_score:.2f}",
            details={
                "injection_safe": injection.safe,
                "length_valid": length_check["valid"],
                "pii_found": len(pii_detections),
                "detections": len(injection.detections),
            },
            trace_id=trace_id,
        )

        return {
            "safe": safe,
            "injection_check": {
                "safe": injection.safe,
                "risk_score": injection.risk_score,
                "detections": injection.detections,
                "sanitized": injection.sanitized_input,
            },
            "length_check": length_check,
            "pii_check": {
                "has_pii": len(pii_detections) > 0,
                "count": len(pii_detections),
                "types": [d.pii_type.value for d in pii_detections],
            },
        }

    def check_output(
        self,
        confidence: float,
        conclusion: str,
        evidence: list[str],
        user_question: str = "",
        trace_id: str = "",
        patient_id: str = "",
    ) -> dict[str, Any]:
        gate_decision = self.human_gate.evaluate(
            confidence=confidence,
            conclusion=conclusion,
            evidence=evidence,
            user_question=user_question,
            report_id=trace_id,
        )

        redacted_conclusion, pii_detections = self.pii_detector.redact(conclusion)

        self.audit_logger.log(
            event_type="output_check",
            severity=(
                AuditSeverity.CRITICAL if gate_decision.block_reasons
                else AuditSeverity.INFO
            ),
            message=f"Output check: status={gate_decision.status.value}, tier={gate_decision.confidence_tier.value}",
            details={
                "confidence": confidence,
                "tier": gate_decision.confidence_tier.value,
                "contradictions": gate_decision.contradictions,
                "pii_redacted": len(pii_detections),
                "block_reasons": gate_decision.block_reasons,
                "requires_review": gate_decision.requires_review,
                "patient_id": patient_id,
            },
            trace_id=trace_id,
        )

        return {
            "safe": not gate_decision.block_reasons,
            "status": gate_decision.status.value,
            "confidence_tier": gate_decision.confidence_tier.value,
            "requires_review": gate_decision.requires_review,
            "contradictions": gate_decision.contradictions,
            "injection_safe": gate_decision.injection_check.safe,
            "pii_detected": gate_decision.pii_check,
            "pii_redacted_conclusion": redacted_conclusion,
            "block_reasons": gate_decision.block_reasons,
        }


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

safety_gate = SafetyGate()
