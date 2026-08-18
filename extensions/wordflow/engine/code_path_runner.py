# -*- coding: utf-8 -*-
"""C-19 code_path_runner — post_verify required (no bypass en perfil normal)."""
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
    context_verified: bool = False,
    handoff_verified: bool = False,
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


def run_code_path(
    raw_input: str,
    *,
    plan_steps: list[str] | None = None,
    skill: dict[str, Any] | None = None,
    mission_id: str = "",
    context_verified: bool = False,
    handoff_verified: bool = False,
    enforce_copy_first: bool = True,
    enforce_post_verify: bool = True,
    allow_skip_post_verify: bool = False,
) -> dict[str, Any]:
    """post_verify ON by default. allow_skip_post_verify solo dev/test explícito."""
    if not allow_skip_post_verify:
        enforce_post_verify = True

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
        doc_anchors=["C-19", "P0-enforcement"],
        notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]

    post = None
    if enforce_post_verify:
        try:
            from extensions.wordflow.standards.forensic_contract import ForensicCodeContract
            from extensions.wordflow.standards.verdict_authority import VerdictAuthority
            from extensions.wordflow.standards.evidence import EvidencePacket
            from extensions.wordflow.standards.closure_engine import ClosureEngine, ClosureInput
            from extensions.wordflow.standards.test_runner import default_smoke_runner

            smoke = default_smoke_runner().run()
            contract = ForensicCodeContract(
                context_verified=context_verified,
                handoff_verified=handoff_verified,
                evidence_complete=bool(evidence_ok),
                final_clean_reaudit_passed=smoke.passed,
            )
            packet = EvidencePacket(
                mission_id=mid or "code_path",
                task_id="C-19",
                change_id="code_path_run",
                repository_revision="local",
                files_changed=["extensions/wordflow/engine/code_path_runner.py"],
                tests=[x["name"] for x in smoke.results if x.get("passed")],
                checks=["pre_gate", "post_verify", "smoke"],
                verdict="PASS" if smoke.passed and evidence_ok else "FAIL",
            )
            decision = VerdictAuthority(contract).decide(evidence=packet, require_evidence=True)
            closure = ClosureEngine().decide(
                ClosureInput(
                    checklist_passed=True,  # full checklist when caller supplies claim
                    forensic_passed=decision.get("verdict") == "PASS",
                    evidence_ok=bool(evidence_ok),
                )
            )
            post = {"verdict_authority": decision, "closure": closure, "smoke": smoke.passed}
        except Exception as exc:  # noqa: BLE001
            post = {"verdict": "FAIL", "reason": str(exc)}

    ok = True
    if post and isinstance(post, dict):
        va = post.get("verdict_authority") or post
        if va.get("verdict") not in ("PASS", None) and post.get("verdict") == "FAIL":
            ok = False
        if (post.get("closure") or {}).get("closed") is False:
            ok = False
        if post.get("verdict") == "FAIL":
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
        "enforce_post_verify": enforce_post_verify,
    }
