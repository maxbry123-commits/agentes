# -*- coding: utf-8 -*-
"""C-19 code_path_runner — FAIL-CLOSED forensic enforcement.
NO VERIFIED CONTEXT → NO PROGRAMMING.
REQUIRED gates no bypass (ni flag dev).
"""
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
    context_verified: bool = False,
    handoff_verified: bool = False,
    # forensic measures supplied by caller/CI — never LLM self-cert alone
    core_measures: dict[str, bool] | None = None,
    connectivity: dict[str, bool] | None = None,
    counters: dict[str, int] | None = None,
    evidence_complete: bool = False,
    final_clean_reaudit_passed: bool = False,
    quality_dag_ok: bool = False,
) -> dict[str, Any]:
    from extensions.wordflow.standards.forensic_core import (
        ForensicProgrammingEnforcer,
        ForensicEnforcementState,
        CoreCheckResult,
        ClosureCounters,
        CORE_IDS,
        CONNECTIVITY_CHAIN,
    )

    enforcer = ForensicProgrammingEnforcer()
    block = enforcer.require_context(context_verified, handoff_verified)
    if block:
        return {"ok": False, "stage": "context", "detail": block, "llm_control": "DENY", "verdict": "BLOCK"}

    q = admit_or_reject(raw_input)
    if not q.get("ok"):
        return {"ok": False, "stage": "quality_bar", "detail": q, "llm_control": "DENY", "verdict": "FAIL"}

    locked = lock_goals({"text": raw_input, "raw": raw_input})
    if not locked.get("ok"):
        return {"ok": False, "stage": "goal_lock", "detail": locked, "llm_control": "DENY", "verdict": "FAIL"}

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
        doc_anchors=["C-19", "FORENSIC_ENFORCEMENT"],
        notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]

    # Build enforcement state — missing CORE measure = FAIL (required_without_handler)
    measures = core_measures or {}
    core_results = []
    for cid in CORE_IDS:
        # default False: must be explicitly measured True
        core_results.append(
            CoreCheckResult(cid, bool(measures.get(cid, False)), evidence=str(measures.get(cid + "_evidence", "")))
        )

    conn = {k: bool((connectivity or {}).get(k, False)) for k in CONNECTIVITY_CHAIN}
    ctr_in = counters or {}
    ctr = ClosureCounters(
        gaps=int(ctr_in.get("gaps", 0)),
        blocking_gaps=int(ctr_in.get("blocking_gaps", 0)),
        broken_connections=int(ctr_in.get("broken_connections", 0)),
        unexplained_orphans=int(ctr_in.get("unexplained_orphans", 0)),
        unreachable_required_paths=int(ctr_in.get("unreachable_required_paths", 0)),
        unresolved_dependencies=int(ctr_in.get("unresolved_dependencies", 0)),
        unverified_paths=int(ctr_in.get("unverified_paths", 0)),
        unverified_requirements=int(ctr_in.get("unverified_requirements", 0)),
        unverified_claims=int(ctr_in.get("unverified_claims", 0)),
        pending_fixes=int(ctr_in.get("pending_fixes", 0)),
        new_gaps_after_fix=int(ctr_in.get("new_gaps_after_fix", 0)),
        unexpected_changes=int(ctr_in.get("unexpected_changes", 0)),
    )

    state = ForensicEnforcementState(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        core_results=core_results,
        connectivity=conn,
        counters=ctr,
        evidence_complete=bool(evidence_complete and evidence_ok),
        final_clean_reaudit_passed=bool(final_clean_reaudit_passed),
        quality_dag_ok=bool(quality_dag_ok),
        claim_used_as_pass=False,
    )
    forensic = enforcer.evaluate(state)

    ok = forensic.get("verdict") == "PASS"
    return {
        "ok": ok,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "evidence": evidence,
        "evidence_ok": evidence_ok,
        "forensic": forensic,
        "llm_control": "DENY",
        "verdict": forensic.get("verdict"),
    }
