# -*- coding: utf-8 -*-
"""publish_path — T43. Mission → Sheriff → DNA → GitHubPublisher. 0% LLM."""
from __future__ import annotations

from typing import Any

from .dna_handoff import build_dna_handoff
from .evidence_graph import EvidenceGraph
from .github_publisher import GitHubPublisher, MapCredentialStore, validate_contract
from .mission import enforce_mission, mission_from_raw


def publish_after_mission(
    raw_input: str,
    contract: dict[str, Any],
    *,
    risk_score: int = 0,
    band: str = "",
    credential_map: dict[str, str] | None = None,
    publisher: GitHubPublisher | None = None,
) -> dict[str, Any]:
    """Only publish if mission+sheriff ALLOW and contract valid."""
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

    v = validate_contract(contract)
    if not v.get("ok"):
        return {"ok": False, "stage": "contract", "detail": v}

    dna_pkg = build_dna_handoff(
        mission["lock"],
        policies={"llm": "DENY", "publish": True},
        next_step="github_publish",
    )
    if not dna_pkg.get("ok"):
        return {"ok": False, "stage": "dna", "detail": dna_pkg}

    pub = publisher or GitHubPublisher(
        credentials=MapCredentialStore(credential_map or {}),
    )
    result = pub.publish(contract)

    graph = EvidenceGraph(mission_id=mission["mission_id"])
    n_m = graph.add_node("mission", {"mission_id": mission["mission_id"]})
    n_s = graph.add_node("sheriff", enforced)
    n_d = graph.add_node("note", {"dna_id": dna_pkg.get("dna_id")})
    n_r = graph.add_node("result", result)
    graph.link(n_m["node_id"], n_s["node_id"], rel="enforced")
    graph.link(n_s["node_id"], n_d["node_id"], rel="dna")
    graph.link(n_d["node_id"], n_r["node_id"], rel="publish")

    return {
        "ok": bool(result.get("ok")),
        "stage": "publish",
        "mission_id": mission["mission_id"],
        "dna_id": dna_pkg.get("dna_id"),
        "publish": result,
        "evidence": graph.snapshot(),
    }
