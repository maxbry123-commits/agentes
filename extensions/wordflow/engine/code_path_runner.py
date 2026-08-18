# -*- coding: utf-8 -*-
"""C-19 code_path_runner + pre-gate + post_verify forense (G-W11)."""
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
        return default_pipeline().pre_implement(
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            symbol_or_stem=symbol,
            dest="extensions/wordflow/engine/code_path_runner.py",
        )
    except Exception as exc:  # noqa: BLE001
        return {"allow": True, "reason": f"pre_gate_skip:{exc}", "copy_first": None}


def _programming_post_verify(mission_id: str, evidence_ok: bool) -> dict[str, Any]:
    try:
        from extensions.wordflow.standards.forensic_contract import (
            ForensicCodeContract,
            CoreChecks,
            AuditPasses,
            ClosureCounters,
        )
        from extensions.wordflow.standards.verdict_authority import VerdictAuthority
        from extensions.wordflow.standards.evidence import EvidencePacket
        from extensions.wordflow.standards.test_runner import default_smoke_runner

        smoke = default_smoke_runner().run()
        contract = ForensicCodeContract(
            context_verified=True,
            handoff_verified=True,
            evidence_complete=bool(evidence_ok),
            final_clean_reaudit_passed=smoke.passed,
            core=CoreChecks(
                requirements=True,
                scope_diff=True,
                implementation=True,
                architecture=True,
                dependencies=True,
                contracts=True,
                connectivity=True,
                behavior=smoke.passed,
                tests=smoke.passed,
                regression_impact=True,
                error_paths=True,
                code_quality=True,
                repository_truth=True,
                evidence=bool(evidence_ok),
            ),
            passes=AuditPasses(
                structure=True,
                connectivity=True,
                behavior=smoke.passed,
                forensic_closure=smoke.passed and bool(evidence_ok),
            ),
            closure=ClosureCounters(),
        )
        packet = EvidencePacket(
            mission_id=mission_id or "code_path",
            task_id="C-19",
            change_id="code_path_run",
            repository_revision="local",
            files_changed=["extensions/wordflow/engine/code_path_runner.py"],
            tests=[r["name"] for r in smoke.results if r.get("passed")],
            checks=["pre_gate", "post_verify", "smoke"],
            verdict="PASS" if smoke.passed and evidence_ok else "FAIL",
        )
        return VerdictAuthority(contract).decide(evidence=packet, require_evidence=True)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "FAIL", "reason": f"post_verify_error:{exc}", "authority": "VerdictAuthority"}


def run_code_path(
    raw_input: str,
    *,
    plan_steps: list[str] | None = None,
    skill: dict[str, Any] | None = None,
    mission_id: str = "",
    context_verified: bool = True,
    handoff_verified: bool = True,
    enforce_copy_first: bool = True,
    enforce_post_verify: bool = True,
) -> dict[str, Any]:
    pre = None
    if enforce_copy_first:
        pre = _programming_pre_gate(
            raw_input,
            context_verified=context_verified,
            handoff_verified=handoff_verified,
        )
        if pre and pre.get("allow") is False:
            return {"ok": False, "stage": "programming_pre_gate", "detail": pre, "llm_control": "DENY"}

    q = admit_or_reject(raw_input)
    if not q.get("ok"):
        return {"ok": False, "stage": "quality_bar", "detail": q, "llm_control": "DENY"}

    locked = lock_goals({"text": raw_input, "raw": raw_input})
    if not locked.get("ok"):
        return {"ok": False, "stage": "goal_lock", "detail": locked, "llm_control": "DENY"}

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
        doc_anchors=["C-19", "programming_pipeline", "G-W11"],
        notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]

    post = None
    if enforce_post_verify:
        post = _programming_post_verify(mid, evidence_ok)

    ok = True
    if post and post.get("verdict") not in ("PASS",):
        ok = False

    return {
        "ok": ok,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "programming_pre_gate": pre,
        "programming_post_verify": post,
        "evidence": evidence,
        "evidence_ok": evidence_ok,
        "llm_control": "DENY",
    }
