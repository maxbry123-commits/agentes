"""Deterministic no-value gate for proposed capabilities/components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

CONTRACT = "yaiwes.no_value_gap/v1"


@dataclass(frozen=True)
class ValueAssessment:
    component: str
    unique_capabilities: int
    overlap_capabilities: int
    maintenance_risk: int
    security_risk: int
    integration_cost: int
    reviewer_verdict: str = "PENDING"
    reviewer_id: str = ""
    reviewer_independent: bool = False


@dataclass(frozen=True)
class ValueDecision:
    verdict: str
    reason_codes: Tuple[str, ...]
    execution_authorized: bool = False
    deployment_authorized: bool = False


def decide_value(assessment: ValueAssessment) -> ValueDecision:
    if not assessment.component.strip():
        raise ValueError("component required")
    scores = (
        assessment.unique_capabilities,
        assessment.overlap_capabilities,
        assessment.maintenance_risk,
        assessment.security_risk,
        assessment.integration_cost,
    )
    if min(scores) < 0:
        raise ValueError("scores must be >= 0")
    if not assessment.reviewer_id.strip() or not assessment.reviewer_independent:
        return ValueDecision("REVIEW_REQUIRED", ("INDEPENDENT_REVIEW_REQUIRED",))
    if assessment.reviewer_verdict not in {"APPROVE", "REJECT", "RESEARCH_MORE"}:
        return ValueDecision("REVIEW_REQUIRED", ("INVALID_REVIEWER_VERDICT",))

    reasons = []
    if assessment.security_risk >= 8:
        reasons.append("SECURITY_RISK_TOO_HIGH")
    if assessment.unique_capabilities == 0 and assessment.overlap_capabilities > 0:
        reasons.extend(("NO_UNIQUE_CAPABILITY", "DUPLICATES_EXISTING_CAPABILITY"))
    if assessment.unique_capabilities <= 1 and assessment.integration_cost + assessment.maintenance_risk >= 12:
        reasons.append("COST_RISK_EXCEEDS_INCREMENTAL_VALUE")

    if reasons:
        if assessment.reviewer_verdict != "REJECT":
            return ValueDecision("REVIEW_REQUIRED", tuple(reasons + ["REVIEWER_REJECTION_REQUIRED"]))
        return ValueDecision("NO_VALUE_GAP", tuple(dict.fromkeys(reasons)))
    if assessment.reviewer_verdict == "RESEARCH_MORE":
        return ValueDecision("RESEARCH_MORE", ("REVIEWER_REQUESTED_MORE_RESEARCH",))
    if assessment.reviewer_verdict == "REJECT":
        return ValueDecision("REVIEW_REQUIRED", ("REJECTION_WITHOUT_DETERMINISTIC_SIGNAL",))
    return ValueDecision("VALUE_CONFIRMED", ("UNIQUE_VALUE_PRESENT", "REVIEWER_APPROVED"))


def gap_markdown(
    assessment: ValueAssessment,
    decision: ValueDecision,
    alternatives: Tuple[str, ...],
) -> str:
    cleaned = tuple(a.strip() for a in alternatives if a and a.strip())
    if decision.verdict == "NO_VALUE_GAP" and not cleaned:
        raise ValueError("NO_VALUE_GAP requires at least one alternative")
    return (
        f"# NO_VALUE_GAP — {assessment.component}\n\n"
        f"- contract: `{CONTRACT}`\n"
        f"- verdict: `{decision.verdict}`\n"
        f"- reasons: {', '.join(decision.reason_codes)}\n"
        f"- unique_capabilities: {assessment.unique_capabilities}\n"
        f"- overlap_capabilities: {assessment.overlap_capabilities}\n"
        f"- maintenance_risk: {assessment.maintenance_risk}\n"
        f"- security_risk: {assessment.security_risk}\n"
        f"- integration_cost: {assessment.integration_cost}\n"
        f"- reviewer_id: `{assessment.reviewer_id}`\n"
        f"- reviewer_independent: `{str(assessment.reviewer_independent).lower()}`\n"
        f"- reviewer_verdict: `{assessment.reviewer_verdict}`\n"
        f"- alternatives: {', '.join(cleaned) if cleaned else 'NONE'}\n"
        f"- execution_authorized: `false`\n"
        f"- deployment_authorized: `false`\n"
    )
