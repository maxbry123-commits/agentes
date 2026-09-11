"""Deterministic no-value gate for proposed capabilities/components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ValueAssessment:
    component: str
    unique_capabilities: int
    overlap_capabilities: int
    maintenance_risk: int
    security_risk: int
    integration_cost: int
    reviewer_verdict: str = "PENDING"


@dataclass(frozen=True)
class ValueDecision:
    verdict: str
    reason_codes: Tuple[str, ...]


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
    if assessment.security_risk >= 8:
        return ValueDecision("NO_VALUE_GAP", ("SECURITY_RISK_TOO_HIGH",))
    if assessment.unique_capabilities == 0 and assessment.overlap_capabilities > 0:
        return ValueDecision(
            "NO_VALUE_GAP",
            ("NO_UNIQUE_CAPABILITY", "DUPLICATES_EXISTING_CAPABILITY"),
        )
    if (
        assessment.unique_capabilities <= 1
        and assessment.integration_cost + assessment.maintenance_risk >= 12
    ):
        return ValueDecision(
            "NO_VALUE_GAP",
            ("COST_RISK_EXCEEDS_INCREMENTAL_VALUE",),
        )
    if assessment.reviewer_verdict != "APPROVE":
        return ValueDecision("REVIEW_REQUIRED", ("INDEPENDENT_REVIEW_REQUIRED",))
    return ValueDecision(
        "VALUE_CONFIRMED",
        ("UNIQUE_VALUE_PRESENT", "REVIEWER_APPROVED"),
    )


def gap_markdown(
    assessment: ValueAssessment,
    decision: ValueDecision,
    alternatives: Tuple[str, ...],
) -> str:
    return (
        f"# NO_VALUE_GAP — {assessment.component}\n\n"
        f"- verdict: `{decision.verdict}`\n"
        f"- reasons: {', '.join(decision.reason_codes)}\n"
        f"- unique_capabilities: {assessment.unique_capabilities}\n"
        f"- overlap_capabilities: {assessment.overlap_capabilities}\n"
        f"- maintenance_risk: {assessment.maintenance_risk}\n"
        f"- security_risk: {assessment.security_risk}\n"
        f"- integration_cost: {assessment.integration_cost}\n"
        f"- reviewer: `{assessment.reviewer_verdict}`\n"
        f"- alternatives: {', '.join(alternatives) if alternatives else 'NONE'}\n"
    )
