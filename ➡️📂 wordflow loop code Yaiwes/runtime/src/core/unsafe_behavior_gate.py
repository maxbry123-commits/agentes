from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .file_audit_contract import AuditResult, RiskLevel


class UnsafeBehaviorGateError(ValueError):
    """Fail-closed error for invalid neutralization evidence."""


@dataclass(frozen=True)
class NeutralizationEvidence:
    risk: str
    benign_substitution: str
    justification: str


@dataclass(frozen=True)
class UnsafeBehaviorDecision:
    contract: str
    original_sha256: str
    candidate_sha256: str
    original_risks: tuple[str, ...]
    candidate_risks: tuple[str, ...]
    neutralized_risks: tuple[str, ...]
    pre_execution_gate_pass: bool
    execution_authorized: bool
    requires_sandbox_review: bool
    reason: str


class UnsafeBehaviorGate:
    """Deterministic pre-execution gate for risky code replacement.

    The gate never mutates or executes source code. It accepts only an independently
    re-audited candidate whose dangerous behavior disappeared and whose substitution
    is justified per original risk. Passing this gate is not execution permission:
    sandbox/reviewer/deployment gates remain mandatory.
    """

    CONTRACT = "yaiwes.unsafe_behavior_gate/v1"

    def evaluate(
        self,
        original: AuditResult,
        candidate: AuditResult,
        evidence: Sequence[NeutralizationEvidence],
    ) -> UnsafeBehaviorDecision:
        original_risks = tuple(sorted(set(original.risks)))
        candidate_risks = tuple(sorted(set(candidate.risks)))

        if original.sha256 == candidate.sha256 and original_risks:
            raise UnsafeBehaviorGateError("RISKY_SOURCE_NOT_CHANGED")

        evidence_by_risk = self._normalize_evidence(evidence)
        missing = tuple(risk for risk in original_risks if risk not in evidence_by_risk)
        if missing:
            raise UnsafeBehaviorGateError("NEUTRALIZATION_EVIDENCE_MISSING:" + ",".join(missing))

        if candidate_risks:
            return self._decision(
                original,
                candidate,
                original_risks,
                candidate_risks,
                (),
                False,
                "CANDIDATE_STILL_RISKY",
            )

        if candidate.risk_level is not RiskLevel.LOW:
            return self._decision(
                original,
                candidate,
                original_risks,
                candidate_risks,
                (),
                False,
                "CANDIDATE_RISK_LEVEL_NOT_LOW",
            )

        neutralized = tuple(sorted(original_risks))
        return self._decision(
            original,
            candidate,
            original_risks,
            candidate_risks,
            neutralized,
            True,
            "SAFE_CANDIDATE_REQUIRES_SANDBOX_REVIEW",
        )

    @staticmethod
    def _normalize_evidence(
        evidence: Sequence[NeutralizationEvidence],
    ) -> Mapping[str, NeutralizationEvidence]:
        result: dict[str, NeutralizationEvidence] = {}
        for item in evidence:
            if not isinstance(item, NeutralizationEvidence):
                raise UnsafeBehaviorGateError("NEUTRALIZATION_EVIDENCE_SCHEMA_INVALID")
            risk = item.risk.strip()
            substitution = item.benign_substitution.strip()
            justification = item.justification.strip()
            if not risk or not substitution or not justification:
                raise UnsafeBehaviorGateError("NEUTRALIZATION_EVIDENCE_INCOMPLETE")
            if risk in result:
                raise UnsafeBehaviorGateError("NEUTRALIZATION_EVIDENCE_DUPLICATE:" + risk)
            result[risk] = item
        return result

    def _decision(
        self,
        original: AuditResult,
        candidate: AuditResult,
        original_risks: tuple[str, ...],
        candidate_risks: tuple[str, ...],
        neutralized_risks: tuple[str, ...],
        passed: bool,
        reason: str,
    ) -> UnsafeBehaviorDecision:
        return UnsafeBehaviorDecision(
            contract=self.CONTRACT,
            original_sha256=original.sha256,
            candidate_sha256=candidate.sha256,
            original_risks=original_risks,
            candidate_risks=candidate_risks,
            neutralized_risks=neutralized_risks,
            pre_execution_gate_pass=passed,
            execution_authorized=False,
            requires_sandbox_review=True,
            reason=reason,
        )
