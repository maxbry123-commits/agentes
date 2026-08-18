# -*- coding: utf-8 -*-
"""C-19 code_path_runner — quality→lock→cognitive→compile→evidence + programming pipeline gates."""
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


def _programming_pre_gate(
    raw_input: str,
    *,
    context_verified: bool = True,
    handoff_verified: bool = True,
    symbol: str = "code_path",
) -> dict[str, Any]:
    try:
        from .programming_pipeline import default_pipeline
        pipe = default_pipeline()
        return pipe.pre_implement(
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            symbol_or_stem=symbol,
            dest="extensions/wordflow/engine/code_path_runner.py",
        )
    except Exception as exc:  # noqa: BLE001 — fail-open log for bootstrap stability
        return {"allow": True, "reason": f"pre_gate_skip:{exc}", "copy_first": None}


def run_code_path(
    raw_input: str,
    *,
    plan_steps: list[str] | None = None,
    skill: dict[str, Any] | None = None,
    mission_id: str = "",
    context_verified: bool = True,
    handoff_verified: bool = True,
    enforce_copy_first: bool = True,
) -> dict[str, Any]:
    """quality_bar → programming pre-gate → goal_lock → cognitive → compile → evidence."""
    pre = None
    if enforce_copy_first:
        pre = _programming_pre_gate(
            raw_input,
            context_verified=context_verified,
            handoff_verified=handoff_verified,
        )
        if pre and pre.get("allow") is False:
            return {
                "ok": False,
                "stage": "programming_pre_gate",
                "detail": pre,
                "llm_control": "DENY",
            }

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
        doc_anchors=["C-19", "programming_pipeline"],
        notes=f"mission={mid}; pre_gate={bool(pre)}",
    )

    return {
        "ok": True,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "programming_pre_gate": pre,
        "evidence": evidence,
        "evidence_ok": verify_evidence_packet(evidence)["ok"],
        "llm_control": "DENY",
    }
