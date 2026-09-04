# -*- coding: utf-8 -*-
"""C-09 cognitive_loop — deterministic wire of planning chain. 0% LLM."""
from __future__ import annotations

from typing import Any

from extensions.wordflow.context.builder import build_context
from extensions.wordflow.engine.evidence_packet import build_evidence_packet
from extensions.wordflow.engine.role_analyzer import build_council_contract
from extensions.wordflow.planner.mission_planner import plan_from_council


class CognitiveLoopError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def run_cognitive_loop(
    *,
    topic: str,
    plan_steps: list[Any],
    mission_id: str = "",
    goal_lock: dict[str, Any] | None = None,
    task_class: str = "CODE",
    risks: list[str] | None = None,
    blackboard: Any = None,
    policies: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One deterministic cycle: Context → CouncilContract → TaskGraph → Evidence."""
    if not plan_steps:
        raise CognitiveLoopError("PLAN_STEPS_EMPTY")

    ctx = build_context(
        mission={"mission_id": mission_id} if mission_id else None,
        goal_lock=goal_lock or ({"lock_id": mission_id} if mission_id else None),
        policies=policies,
        blackboard=blackboard,
    )
    if not ctx.get("ok"):
        raise CognitiveLoopError("CONTEXT_FAILED")

    council = build_council_contract(
        topic=topic,
        plan=plan_steps,
        task_class=task_class,
        risks=risks,
        mission_id=mission_id or ctx["context"].get("mission_id", ""),
    )
    if not council.get("ok"):
        raise CognitiveLoopError("COUNCIL_FAILED", council.get("reason_code", ""))

    graph = plan_from_council(council)
    if not graph.get("ok"):
        raise CognitiveLoopError("GRAPH_FAILED")

    evidence = build_evidence_packet(
        task_id="C-09",
        claim_status="PARTIAL",
        paths=[{"path": "extensions/wordflow/engine/cognitive_loop.py"}],
        tests={"node_count": graph.get("node_count", 0)},
        doc_anchors=["C-09", topic],
        notes=f"graph_id={graph.get('graph_id')}",
    )

    return {
        "ok": True,
        "context": ctx["context"],
        "council": council,
        "task_graph": graph,
        "evidence": evidence,
        "llm_control": "DENY",
    }
