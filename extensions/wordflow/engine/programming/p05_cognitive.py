# -*- coding: utf-8 -*-
"""Process 05 — Cognitive loop + optional skill compile."""
from __future__ import annotations
from typing import Any
from .skill_compiler import compile_skill_to_code


def run_cognitive(* , raw_input: str, plan_steps: list[str] | None, mission_id: str, lock: dict[str, Any], skill: dict[str, Any] | None) -> dict[str, Any]:
    from extensions.wordflow.engine.cognitive_loop import run_cognitive_loop
    steps = plan_steps or ["analyze", "compile", "validate", "promote"]
    cog = run_cognitive_loop(topic=raw_input[:80], plan_steps=steps, mission_id=mission_id, goal_lock=lock, task_class="CODE")
    compiled = compile_skill_to_code(skill) if skill else None
    return {"cognitive": cog, "skill_compile": compiled}
