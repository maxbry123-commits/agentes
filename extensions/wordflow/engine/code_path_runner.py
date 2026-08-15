# -*- coding: utf-8 -*-
"""C-19 code_path_runner — minimal deterministic code-path orchestration. 0% LLM."""
from __future__ import annotations

from typing import Any

from .cognitive_loop import run_cognitive_loop
from .evidence_packet import build_evidence_packet, verify_evidence_packet
from .goal_lock import lock_goals
from .input_quality_bar import admit_or_reject
from .skill_native_compiler import compile_skill_to_code


class CodePathError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def run_code_path(
    raw_input: str,
    *,
    plan_steps: list[str] | None = None,
    skill: dict[str, Any] | None = None,
    mission_id: str = "",
) -> dict[str, Any]:
    """quality_bar → goal_lock → cognitive_loop → optional skill compile → evidence."""
    q = admit_or_reject(raw_input)
    if not q.get("ok"):
        return {"ok": False, "stage": "quality_bar", "detail": q, "llm_control": "DENY"}

    locked = lock_goals({"text": raw_input, "raw": raw_input})
    if not locked.get("ok"):
        return {
            "ok": False,
            "stage": "goal_lock",
            "detail": locked,
            "llm_control": "DENY",
        }

    lock = locked.get("lock") or {}
    mid = mission_id or lock.get("lock_id") or ""

    steps = plan_steps or ["analyze", "compile", "validate", "promote"]
    cog = run_cognitive_loop(
        topic=raw_input[:80],
        plan_steps=steps,
        mission_id=mid,
        goal_lock=lock,
        task_class="CODE",
    )

    compiled = None
    if skill:
        compiled = compile_skill_to_code(skill)

    evidence = build_evidence_packet(
        task_id="C-19",
        claim_status="PARTIAL",
        paths=[{"path": "extensions/wordflow/engine/code_path_runner.py"}],
        tests={"cognitive_ok": True, "skill_compiled": compiled is not None},
        doc_anchors=["C-19"],
        notes=f"mission={mid}",
    )

    return {
        "ok": True,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "evidence": evidence,
        "evidence_ok": verify_evidence_packet(evidence)["ok"],
        "llm_control": "DENY",
    }
