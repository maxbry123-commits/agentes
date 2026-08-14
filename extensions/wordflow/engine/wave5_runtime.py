# -*- coding: utf-8 -*-
"""wave5_runtime — T32. Mission + ExpertRouter + DecisionGate. 0% LLM."""
from __future__ import annotations

from typing import Any

from .evidence_graph import EvidenceGraph
from .expert_router import route_and_decide
from .mission import enforce_mission, mission_from_raw
from .task_classifier import classify_task


def run_with_panel(
    raw_input: str,
    topic: str,
    *,
    risk_score: int = 0,
    band: str = "",
    task_class: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mission enforce → classify → expert route+decide → evidence."""
    mission = mission_from_raw(raw_input)
    if not mission.get("ok"):
        return {"ok": False, "stage": "mission", "detail": mission}

    enforced = enforce_mission(mission, risk_score=risk_score, band=band)
    if not enforced.get("ok"):
        return {
            "ok": False,
            "stage": "sheriff",
            "mission_id": mission["mission_id"],
            "enforced": enforced,
        }

    lock = mission["lock"]
    cls = task_class or classify_task(
        topic or lock.get("objective") or "",
        lock=lock,
    )
    if isinstance(cls, dict):
        class_name = str(cls.get("class") or cls.get("task_class") or "DEFAULT")
    else:
        class_name = str(cls)

    ctx = dict(context or {})
    ctx.setdefault("risk_score", risk_score)
    if risk_score >= 8:
        ctx["risk_high"] = True

    decision = route_and_decide(topic, task_class=class_name, context=ctx)

    graph = EvidenceGraph(mission_id=mission["mission_id"])
    n_m = graph.add_node("mission", {"mission_id": mission["mission_id"]})
    n_s = graph.add_node("sheriff", enforced)
    n_p = graph.add_node("result", decision)
    graph.link(n_m["node_id"], n_s["node_id"], rel="enforced")
    graph.link(n_s["node_id"], n_p["node_id"], rel="panel")

    return {
        "ok": bool(decision.get("ok")),
        "stage": "panel_done",
        "mission_id": mission["mission_id"],
        "task_class": class_name,
        "enforced": enforced,
        "decision": decision,
        "evidence": graph.snapshot(),
    }
