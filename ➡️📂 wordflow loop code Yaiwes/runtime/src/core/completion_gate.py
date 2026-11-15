"""Deterministic completion gate for YAIWES programming nodes.

This is an additive gate: legacy nodes without a ``completion_contract`` keep their
existing behavior. Nodes that opt in cannot reach DONE merely because a handler
returned a dictionary. They must satisfy explicit acceptance criteria and evidence.

The frontend profile intentionally requires runtime/browser/interaction/mobile
proof. Source code or build success alone is never a frontend PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class CompletionGateError(ValueError):
    """Fail-closed completion contract or evidence error."""


BACKEND_REQUIRED_EVIDENCE = (
    "source_code_pass",
    "execution_pass",
    "tests_pass",
    "output_captured",
)

FRONTEND_REQUIRED_EVIDENCE = (
    "source_code_pass",
    "build_pass",
    "runtime_pass",
    "browser_pass",
    "interaction_pass",
    "console_checked",
    "dom_or_visual_evidence",
    "mobile_touch_pass",
)


@dataclass(frozen=True)
class CompletionDecision:
    profile: str
    goal: str
    acceptance_total: int
    acceptance_passed: int
    required_evidence: tuple[str, ...]
    missing_acceptance: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    passed: bool
    reason: str


def _normalize_acceptance(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CompletionGateError("ACCEPTANCE_MUST_BE_LIST")
    items = tuple(str(item).strip() for item in value if str(item).strip())
    if not items:
        raise CompletionGateError("ACCEPTANCE_REQUIRED")
    if len(set(items)) != len(items):
        raise CompletionGateError("ACCEPTANCE_DUPLICATE")
    return items


def _required_for_profile(profile: str) -> tuple[str, ...]:
    normalized = profile.strip().lower()
    if normalized == "backend":
        return BACKEND_REQUIRED_EVIDENCE
    if normalized == "frontend":
        return FRONTEND_REQUIRED_EVIDENCE
    raise CompletionGateError("UNKNOWN_COMPLETION_PROFILE:" + normalized)


def evaluate_completion(
    contract: Mapping[str, Any], result: Mapping[str, Any]
) -> CompletionDecision:
    """Evaluate a node result against an explicit goal/acceptance/evidence contract."""
    if not isinstance(contract, Mapping):
        raise CompletionGateError("COMPLETION_CONTRACT_MUST_BE_MAPPING")
    if not isinstance(result, Mapping):
        raise CompletionGateError("RESULT_MUST_BE_MAPPING")

    goal = str(contract.get("goal", "")).strip()
    if not goal:
        raise CompletionGateError("GOAL_REQUIRED")

    profile = str(contract.get("profile", "")).strip().lower()
    required_evidence = _required_for_profile(profile)
    acceptance = _normalize_acceptance(contract.get("acceptance", ()))

    acceptance_results = result.get("acceptance", {})
    evidence = result.get("evidence", {})
    if not isinstance(acceptance_results, Mapping):
        raise CompletionGateError("RESULT_ACCEPTANCE_MUST_BE_MAPPING")
    if not isinstance(evidence, Mapping):
        raise CompletionGateError("RESULT_EVIDENCE_MUST_BE_MAPPING")

    missing_acceptance = tuple(
        item for item in acceptance if acceptance_results.get(item) is not True
    )
    missing_evidence = tuple(
        key for key in required_evidence if evidence.get(key) is not True
    )
    passed = not missing_acceptance and not missing_evidence
    reason = "PASS_ACCEPTANCE_AND_EVIDENCE" if passed else "INCOMPLETE_ACCEPTANCE_OR_EVIDENCE"

    return CompletionDecision(
        profile=profile,
        goal=goal,
        acceptance_total=len(acceptance),
        acceptance_passed=len(acceptance) - len(missing_acceptance),
        required_evidence=required_evidence,
        missing_acceptance=missing_acceptance,
        missing_evidence=missing_evidence,
        passed=passed,
        reason=reason,
    )


def require_completion(
    contract: Mapping[str, Any], result: Mapping[str, Any]
) -> CompletionDecision:
    """Return the decision or fail closed before a node can be marked DONE."""
    decision = evaluate_completion(contract, result)
    if not decision.passed:
        details = []
        if decision.missing_acceptance:
            details.append("acceptance=" + ",".join(decision.missing_acceptance))
        if decision.missing_evidence:
            details.append("evidence=" + ",".join(decision.missing_evidence))
        raise CompletionGateError("COMPLETION_GATE_FAIL:" + ";".join(details))
    return decision
