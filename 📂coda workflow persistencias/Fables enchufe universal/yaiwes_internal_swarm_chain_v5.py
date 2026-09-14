from __future__ import annotations

import json
from pathlib import Path

from yaiwes_real_workflow_chain_v63 import run_linear_chain


def run_swarm(registry_path, state_root, task_id, payload=None):
    """Compatibility entrypoint that delegates to the real 24-link chain.

    The registry is validated for count only. Component execution is performed
    by the canonical internal-workflow runner; this module no longer implements
    checkpoint-only behavior.
    """
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("count") != 24:
        raise ValueError("canonical registry must contain 24 components")
    report = run_linear_chain(Path(state_root), task_id, dict(payload or {}))
    if report.get("real_internal_workflows_executed") != 24:
        raise RuntimeError("real internal workflow requirement not satisfied")
    return {
        "task_id": task_id,
        "components_completed": report["components"],
        "evidence": report["evidence"],
        "status": report["status"],
        "handoff_continuity": report["handoff_continuity"],
        "universal_plug_after_component_24": report["universal_plug_after_component_24"],
    }
