"""Hard boundary between deterministic authority and LLM advisory work."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

ACTION_POLICY: Dict[str, str] = {
    "analyze_file": "LLM_ALLOWED",
    "draft_code": "LLM_ALLOWED",
    "council_opinion": "LLM_ALLOWED",
    "research_summary": "LLM_ALLOWED",
    "authorize_execution": "DETERMINISTIC",
    "select_target_path": "DETERMINISTIC",
    "schedule_dag": "DETERMINISTIC",
    "state_transition": "DETERMINISTIC",
    "sandbox_policy": "DETERMINISTIC",
    "promote_deployment": "DETERMINISTIC",
    "hash_verify": "DETERMINISTIC",
}


@dataclass(frozen=True)
class BoundaryDecision:
    allowed: bool
    authority: str
    reason: str


def enforce_boundary(action: str, actor: str) -> BoundaryDecision:
    if action not in ACTION_POLICY:
        return BoundaryDecision(False, "UNKNOWN", "ACTION_NOT_ALLOWLISTED")
    authority = ACTION_POLICY[action]
    normalized_actor = actor.upper()
    if authority == "DETERMINISTIC" and normalized_actor in {"LLM", "AGENT_LLM"}:
        return BoundaryDecision(
            False,
            authority,
            "LLM_CANNOT_AUTHORIZE_DETERMINISTIC_ACTION",
        )
    if authority == "LLM_ALLOWED" and normalized_actor not in {
        "LLM",
        "AGENT_LLM",
        "DETERMINISTIC",
    }:
        return BoundaryDecision(False, authority, "ACTOR_NOT_ALLOWED")
    return BoundaryDecision(True, authority, "POLICY_ALLOWED")
