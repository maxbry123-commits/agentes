"""Deterministic architecture placement classifier for Wordflow LOOP Yaiwes.

Maps a capability to A..G architectural destinations using explicit signals only.
No network I/O, no LLM decision, no deployment. Ambiguous or weak evidence fails
closed to PLACEMENT_REVIEW_REQUIRED.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

Placement = Literal[
    "A_KERNEL",
    "B_EXTENSION_KERNEL",
    "C_REASONING_LAYER",
    "D_WORDFLOW",
    "E_POOL",
    "F_TOOLS",
    "G_OTHER",
    "PLACEMENT_REVIEW_REQUIRED",
]
Lifecycle = Literal["process", "persistent", "session", "task", "request", "ephemeral", "unknown"]
Execution = Literal["core", "extension", "reasoning", "workflow", "pool", "tool", "other", "unknown"]


class PlacementError(ValueError):
    """Fail-closed validation error."""


@dataclass(frozen=True)
class PlacementRequest:
    capability: str
    privileged: bool = False
    lifecycle: Lifecycle = "unknown"
    execution: Execution = "unknown"
    stateful: bool = False
    latency_critical: bool = False
    kernel_invariant: bool = False
    reasoning: bool = False
    agent_chain: bool = False
    fanout: bool = False
    reusable_tool: bool = False
    external_io: bool = False
    other_location: str = ""
    other_justification: str = ""


@dataclass(frozen=True)
class PlacementDecision:
    placement: Placement
    reason_codes: Tuple[str, ...]
    scores: Dict[str, int]


def classify_placement(req: PlacementRequest) -> PlacementDecision:
    if not req.capability.strip():
        raise PlacementError("capability is required")

    scores: Dict[str, int] = {
        "A_KERNEL": 0,
        "B_EXTENSION_KERNEL": 0,
        "C_REASONING_LAYER": 0,
        "D_WORDFLOW": 0,
        "E_POOL": 0,
        "F_TOOLS": 0,
    }
    reasons: List[Tuple[str, str]] = []

    def add(placement: str, weight: int, reason: str) -> None:
        scores[placement] += weight
        reasons.append((placement, reason))

    if req.kernel_invariant:
        add("A_KERNEL", 6, "KERNEL_INVARIANT")
    if req.privileged:
        add("A_KERNEL", 2, "PRIVILEGED_CORE_CANDIDATE")
        add("B_EXTENSION_KERNEL", 3, "PRIVILEGED_EXTENSION_CANDIDATE")
    if req.lifecycle == "process":
        add("A_KERNEL", 2, "PROCESS_LIFECYCLE")
    if req.lifecycle == "persistent":
        add("B_EXTENSION_KERNEL", 2, "PERSISTENT_EXTENSION_LIFECYCLE")
    if req.execution == "core":
        add("A_KERNEL", 5, "EXECUTION_CORE")
    if req.execution == "extension":
        add("B_EXTENSION_KERNEL", 5, "EXECUTION_EXTENSION")

    if req.reasoning:
        add("C_REASONING_LAYER", 5, "SEMANTIC_REASONING")
    if req.execution == "reasoning":
        add("C_REASONING_LAYER", 5, "EXECUTION_REASONING")

    if req.agent_chain:
        add("D_WORDFLOW", 5, "AGENT_CHAIN")
    if req.execution == "workflow":
        add("D_WORDFLOW", 5, "EXECUTION_WORKFLOW")
    if req.lifecycle == "task":
        add("D_WORDFLOW", 1, "TASK_LIFECYCLE")

    if req.fanout:
        add("E_POOL", 5, "FANOUT_CONCURRENCY")
    if req.execution == "pool":
        add("E_POOL", 5, "EXECUTION_POOL")
    if req.stateful and req.fanout:
        add("E_POOL", 1, "STATEFUL_POOL")

    if req.reusable_tool:
        add("F_TOOLS", 5, "REUSABLE_TOOL")
    if req.execution == "tool":
        add("F_TOOLS", 5, "EXECUTION_TOOL")
    if req.external_io:
        add("F_TOOLS", 2, "EXTERNAL_IO_ADAPTER")

    if req.latency_critical and req.kernel_invariant:
        add("A_KERNEL", 1, "LATENCY_CRITICAL_INVARIANT")

    if req.other_location or req.execution == "other":
        if req.other_location.strip() and req.other_justification.strip():
            return PlacementDecision("G_OTHER", ("EXPLICIT_OTHER_LOCATION",), scores)
        return PlacementDecision(
            "PLACEMENT_REVIEW_REQUIRED",
            ("OTHER_REQUIRES_LOCATION_AND_JUSTIFICATION",),
            scores,
        )

    max_score = max(scores.values())
    winners = sorted(p for p, score in scores.items() if score == max_score and score > 0)
    if max_score < 4 or len(winners) != 1:
        return PlacementDecision(
            "PLACEMENT_REVIEW_REQUIRED",
            ("INSUFFICIENT_OR_CONFLICTING_SIGNALS",),
            scores,
        )

    winner = winners[0]
    winner_reasons = tuple(code for placement, code in reasons if placement == winner)
    return PlacementDecision(winner, winner_reasons, scores)
