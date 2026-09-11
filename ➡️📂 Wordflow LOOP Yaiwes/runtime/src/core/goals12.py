"""Twelve deterministic GOAL gates for Wordflow code tasks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

GOALS12 = (
    "INPUT_LITERAL_CAPTURED",
    "PROVENANCE_VERIFIED",
    "TASK_CONTRACT_VALID",
    "DEPENDENCIES_MAPPED",
    "PLACEMENT_APPROVED",
    "REUSE_RESEARCH_COMPLETE",
    "SAFETY_GATE_PASS",
    "SANDBOX_GATE_PASS",
    "INDEPENDENT_REVIEW_PASS",
    "EVIDENCE_COMPLETE",
    "STATE_PERSISTED",
    "OUTPUT_ACCEPTANCE_PASS",
)


@dataclass(frozen=True)
class Goals12Result:
    passed: bool
    missing: Tuple[str, ...]
    status: str


def evaluate_goals12(
    evidence: Mapping[str, bool],
    *,
    council_checks: int,
    simulations: int,
    refutations: int,
    cross_check: bool,
) -> Goals12Result:
    missing = [goal for goal in GOALS12 if evidence.get(goal) is not True]
    if council_checks < 12:
        missing.append("COUNCIL12_INCOMPLETE")
    if simulations < 3:
        missing.append("SIMULATIONS_LT_3")
    if refutations < 3:
        missing.append("REFUTATIONS_LT_3")
    if cross_check is not True:
        missing.append("GLOBAL_CROSS_CHECK_MISSING")
    return Goals12Result(
        not missing,
        tuple(missing),
        "PASS" if not missing else "GAP",
    )
