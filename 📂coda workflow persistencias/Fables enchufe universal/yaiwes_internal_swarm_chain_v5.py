from __future__ import annotations

import json
from pathlib import Path

import yaiwes_coda_research_gate_v71 as research_gate


def run_swarm(registry_path, state_root, task_id, payload=None):
    """Canonical compatibility entrypoint for the 24-CODA workflow.

    The registry contract remains V5-compatible, but execution is routed through
    the V7.1 fail-closed research gate. That gate performs research/tool
    discovery before every CODA and delegates each task-solving step to the
    existing real internal workflow executor.
    """
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("count") != 24:
        raise ValueError("canonical registry must contain 24 components")

    report = research_gate.run_coda_chain(
        Path(state_root),
        task_id,
        dict(payload or {}),
    )
    if report.get("real_internal_workflows_executed") != 24:
        raise RuntimeError("real internal workflow requirement not satisfied")
    if report.get("research_cycles") != 24 or not report.get("research_fail_closed"):
        raise RuntimeError("24 real research cycles are required")

    evidence = [
        item.get("internal_state", item)
        for item in report.get("evidence", [])
    ]
    if len(evidence) != 24 or not all(item.get("status") == "RELEASED" for item in evidence):
        raise RuntimeError("canonical 24-CODA release contract not satisfied")

    # The research gate only returns after the V7 bus has validated handoff
    # continuity and delivered component 24 to the universal plug.
    return {
        "task_id": task_id,
        "components_completed": report["components"],
        "evidence": evidence,
        "status": report["status"],
        "handoff_continuity": True,
        "research_cycles": report["research_cycles"],
        "research_fail_closed": True,
        "universal_plug_after_component_24": report["universal_plug_after_component_24"],
    }
