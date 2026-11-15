# -*- coding: utf-8 -*-
"""
Entrypoint del módulo project_bootstrap
Enchufe Universal: wordflow.kernel.project_bootstrap
A8 — Integración ejecutable

Flujo:
  raw_input → InputHandler → KTP cycle → microflujos → ResourceBrain gate → Updater
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .ktp.engine import create_engine, KTPContext
from .input_handler import handle_input
from .microflows.runner import extract_goal, decompose_tasks, build_profile, run_microflujo
from .resource_brain import ResourceBrain
from .updater import IncrementalUpdater


def _bootstrap_resources(rb: ResourceBrain) -> None:
    for cap in [
        "extract_goal",
        "decompose_tasks",
        "build_profile",
        "build_architecture",
        "build_workflow",
        "build_pipeline",
        "build_capabilities",
        "append_trace",
    ]:
        rb.onboard(cap, kind="microflujo")


def run(
    raw_input: str,
    source: str = "chat",
    current_running: bool = False,
    states_path: Optional[str] = None,
) -> Dict[str, Any]:
    classification = handle_input(raw_input, source=source, current_running=current_running)
    if classification.should_pause:
        return {
            "status": "PAUSED",
            "reason": classification.notes,
            "input_block": classification.input_block.to_dict(),
            "derived_tasks": classification.derived_tasks,
        }

    rb = ResourceBrain()
    _bootstrap_resources(rb)
    needed = ["extract_goal", "decompose_tasks", "build_profile"]
    ready = rb.select_ready(needed)
    if set(needed) - set(ready):
        return {
            "status": "BLOCKED",
            "reason": f"capacidades no AVAILABLE: {set(needed) - set(ready)}",
            "available": rb.list_available(),
        }

    engine = create_engine(states_path)
    ctx = KTPContext(raw_input=raw_input)

    goal = extract_goal(raw_input)
    ctx.goal_struct = goal.to_dict()
    ctx = engine.transition(ctx, "TAREA", output_data=ctx.goal_struct, resources_used=["extract_goal"])

    tasks = decompose_tasks(goal)
    ctx.task_list = [t.to_dict() for t in tasks]
    ctx = engine.transition(ctx, "PLANIFICAR", output_data=ctx.task_list, resources_used=["decompose_tasks"])

    profile = build_profile(goal=goal)

    up = IncrementalUpdater()
    up.register("goal_struct", ctx.goal_struct)
    up.register("task_list", ctx.task_list)
    up.register("PROJECT_PROFILE", profile)
    update_goal = up.apply_update("goal_struct", ctx.goal_struct)

    return {
        "status": "OK",
        "input_block": classification.input_block.to_dict(),
        "ktp": engine.snapshot(ctx),
        "goal": goal.to_dict(),
        "tasks": [t.to_dict() for t in tasks],
        "profile": profile,
        "resources_available": rb.list_available(),
        "update": update_goal.to_dict(),
        "impact_targets": classification.impact_targets,
    }


if __name__ == "__main__":
    result = run("Necesito crear un sistema de autenticación OAuth2")
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
