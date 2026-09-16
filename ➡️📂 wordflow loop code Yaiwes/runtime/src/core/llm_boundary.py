"""Executable boundary between deterministic authority and LLM advisory work.

``allowed`` means that the trusted caller may invoke the requested operation;
it never means that an advisory LLM response has granted execution authority.
Unknown actions and actors fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, TypeVar

ACTION_POLICY: Mapping[str, str] = MappingProxyType({
    "analyze_file": "LLM_ALLOWED",
    "classify_semantics": "LLM_ALLOWED",
    "generate_candidate": "LLM_ALLOWED",
    "draft_code": "LLM_ALLOWED",
    "council_opinion": "LLM_ALLOWED",
    "research_summary": "LLM_ALLOWED",
    "synthesize_requirements": "LLM_ALLOWED",
    "authorize_execution": "DETERMINISTIC",
    "evaluate_gate": "DETERMINISTIC",
    "persist_checkpoint": "DETERMINISTIC",
    "persist_evidence": "DETERMINISTIC",
    "rollback_deployment": "DETERMINISTIC",
    "route_task": "DETERMINISTIC",
    "select_target_path": "DETERMINISTIC",
    "schedule_dag": "DETERMINISTIC",
    "state_transition": "DETERMINISTIC",
    "sandbox_policy": "DETERMINISTIC",
    "promote_deployment": "DETERMINISTIC",
    "hash_verify": "DETERMINISTIC",
    "validate_contract": "DETERMINISTIC",
    "validate_schema": "DETERMINISTIC",
})

DETERMINISTIC_ACTORS = frozenset({"DETERMINISTIC", "DETERMINISTIC_RUNTIME"})
LLM_ACTORS = frozenset({"LLM", "AGENT_LLM"})
KNOWN_ACTORS = DETERMINISTIC_ACTORS | LLM_ACTORS
T = TypeVar("T")


@dataclass(frozen=True)
class BoundaryDecision:
    allowed: bool
    authority: str
    reason: str


def enforce_boundary(action: str, actor: str) -> BoundaryDecision:
    if action not in ACTION_POLICY:
        return BoundaryDecision(False, "UNKNOWN", "ACTION_NOT_ALLOWLISTED")
    authority = ACTION_POLICY[action]
    normalized_actor = actor.strip().upper()
    if normalized_actor not in KNOWN_ACTORS:
        return BoundaryDecision(False, authority, "ACTOR_NOT_ALLOWLISTED")
    if authority == "DETERMINISTIC" and normalized_actor not in DETERMINISTIC_ACTORS:
        return BoundaryDecision(
            False,
            authority,
            "LLM_CANNOT_AUTHORIZE_DETERMINISTIC_ACTION",
        )
    return BoundaryDecision(True, authority, "POLICY_ALLOWED")


class BoundaryViolation(PermissionError):
    """Raised before a guarded callback when the boundary rejects the caller."""


def execute_with_boundary(
    action: str,
    actor: str,
    callback: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Run ``callback`` only after the deterministic boundary allows the call."""
    decision = enforce_boundary(action, actor)
    if not decision.allowed:
        raise BoundaryViolation(f"{decision.reason}:{action}")
    return callback(*args, **kwargs)
