# -*- coding: utf-8 -*-
"""wave4_runtime — T28. Mission + Sheriff + Evidence orchestration. 0% LLM."""
from __future__ import annotations

from typing import Any

from .evidence_graph import EvidenceGraph
from .execution_facade import ExecutionFacade
from .mission import enforce_mission, mission_from_raw


def run_mission_safe(
    raw_input: str,
    *,
    risk_score: int = 0,
    band: str = "",
    kind: str = "noop",
    facade: ExecutionFacade | None = None,
    resource_id: str | None = None,
    engine_id: str | None = None,
    prompt: str = "",
) -> dict[str, Any]:
    """Build mission → enforce sheriff → record evidence → optional facade route."""
    mission = mission_from_raw(raw_input)
    if not mission.get("ok"):
        return {"ok": False, "stage": "mission", "detail": mission}

    graph = EvidenceGraph(mission_id=mission["mission_id"])
    n_mission = graph.add_node("mission", {"mission_id": mission["mission_id"]})
    n_lock = graph.add_node("lock", mission["lock"], ref_id=mission["lock"].get("lock_id"))
    graph.link(n_mission["node_id"], n_lock["node_id"], rel="binds")

    enforced = enforce_mission(mission, risk_score=risk_score, band=band)
    n_sheriff = graph.add_node("sheriff", enforced)
    graph.link(n_lock["node_id"], n_sheriff["node_id"], rel="gated_by")

    if not enforced.get("ok"):
        return {
            "ok": False,
            "stage": "sheriff",
            "mission_id": mission["mission_id"],
            "enforced": enforced,
            "evidence": graph.snapshot(),
        }

    route_result = None
    if kind not in ("noop", "", "local"):
        fac = facade or ExecutionFacade()
        route_result = fac.route(
            mission["lock"],
            kind=kind,
            resource_id=resource_id,
            engine_id=engine_id or "fake_static",
            prompt=prompt,
        )
        n_res = graph.add_node("result", route_result)
        graph.link(n_sheriff["node_id"], n_res["node_id"], rel="allows")
        if not route_result.get("ok"):
            return {
                "ok": False,
                "stage": "route",
                "mission_id": mission["mission_id"],
                "enforced": enforced,
                "route": route_result,
                "evidence": graph.snapshot(),
            }

    return {
        "ok": True,
        "stage": "done",
        "mission_id": mission["mission_id"],
        "enforced": enforced,
        "route": route_result,
        "evidence": graph.snapshot(),
    }
