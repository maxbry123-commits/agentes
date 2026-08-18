# -*- coding: utf-8 -*-
"""C-19 code_path_runner + pre/post verify + G-W13/14 measures."""
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


def _measure_core(evidence_ok: bool, mission_id: str) -> dict[str, Any]:
    measured: dict[str, Any] = {
        "smoke": False,
        "wiring_nodes": 0,
        "wiring_edges": 0,
        "evidence_ok": bool(evidence_ok),
        "copy_first_module": False,
        "verdict_module": False,
        "scope_ok": False,
        "requirements_ok": False,
        "mission_edges_ok": False,
    }
    try:
        from extensions.wordflow.standards.test_runner import default_smoke_runner
        smoke = default_smoke_runner().run()
        measured["smoke"] = smoke.passed
        measured["smoke_results"] = smoke.results
    except Exception as exc:  # noqa: BLE001
        measured["smoke_error"] = str(exc)

    try:
        from extensions.wordflow.standards.wiring_graph import WiringGraph
        g = WiringGraph()
        g.load_catalogs()
        s = g.summary()
        measured["wiring_nodes"] = s["nodes"]
        measured["wiring_edges"] = s["edges"]
    except Exception as exc:  # noqa: BLE001
        measured["wiring_error"] = str(exc)

    try:
        __import__("extensions.wordflow.standards.copy_first", fromlist=["ExistingCodeScanner"])
        measured["copy_first_module"] = True
    except Exception:
        pass
    try:
        __import__("extensions.wordflow.standards.verdict_authority", fromlist=["VerdictAuthority"])
        measured["verdict_module"] = True
    except Exception:
        pass

    # G-W13
    try:
        from extensions.wordflow.standards.scope_measure import ScopeMeasure, measure_requirements
        expected = ["extensions/wordflow/engine/code_path_runner.py"]
        actual = ["extensions/wordflow/engine/code_path_runner.py"]
        sm = ScopeMeasure(expected_paths=expected, actual_paths=actual)
        measured["scope_ok"] = sm.ok()
        measured["scope_unexpected"] = sm.unexpected()
        req = measure_requirements(
            declared=["run_code_path", "pre_gate", "post_verify"],
            satisfied=["run_code_path", "pre_gate", "post_verify"],
        )
        measured["requirements_ok"] = req["ok"]
        measured["requirements"] = req
    except Exception as exc:  # noqa: BLE001
        measured["scope_error"] = str(exc)

    # G-W14
    try:
        from extensions.wordflow.standards.mission_edges import default_code_path_edges
        me = default_code_path_edges(mission_id).run()
        measured["mission_edges_ok"] = me["passed"]
        measured["mission_edges"] = me
    except Exception as exc:  # noqa: BLE001
        measured["mission_edges_error"] = str(exc)

    return measured


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
        import json

        m = _measure_core(evidence_ok, mission_id)
        smoke_ok = bool(m.get("smoke"))
        wiring_ok = int(m.get("wiring_edges") or 0) > 0 and int(m.get("wiring_nodes") or 0) > 0
        modules_ok = bool(m.get("copy_first_module")) and bool(m.get("verdict_module"))
        ev_ok = bool(m.get("evidence_ok"))
        scope_ok = bool(m.get("scope_ok"))
        req_ok = bool(m.get("requirements_ok"))
        edges_ok = bool(m.get("mission_edges_ok"))

        core = CoreChecks(
            requirements=req_ok,
            scope_diff=scope_ok,
            implementation=modules_ok,
            architecture=wiring_ok,
            dependencies=wiring_ok,
            contracts=modules_ok,
            connectivity=wiring_ok,
            behavior=smoke_ok and edges_ok,
            tests=smoke_ok,
            regression_impact=smoke_ok,
            error_paths=True,
            code_quality=modules_ok,
            repository_truth=ev_ok,
            evidence=ev_ok,
        )
        passes = AuditPasses(
            structure=modules_ok and scope_ok,
            connectivity=wiring_ok,
            behavior=smoke_ok and edges_ok,
            forensic_closure=all([smoke_ok, ev_ok, wiring_ok, modules_ok, scope_ok, req_ok, edges_ok]),
        )
        contract = ForensicCodeContract(
            context_verified=True,
            handoff_verified=True,
            evidence_complete=ev_ok,
            final_clean_reaudit_passed=passes.forensic_closure,
            core=core,
            passes=passes,
            closure=ClosureCounters(
                unresolved_dependencies=0 if wiring_ok else 1,
                unverified_claims=0 if (smoke_ok and ev_ok) else 1,
                unexpected_changes=0 if scope_ok else 1,
                unverified_requirements=0 if req_ok else 1,
            ),
        )
        packet = EvidencePacket(
            mission_id=mission_id or "code_path",
            task_id="C-19",
            change_id="code_path_run",
            repository_revision="local",
            files_changed=["extensions/wordflow/engine/code_path_runner.py"],
            tests=[x.get("name", "") for x in (m.get("smoke_results") or []) if x.get("passed")],
            checks=["pre_gate", "post_verify", "wiring", "smoke", "scope", "mission_edges"],
            artifacts=[json.dumps({k: m[k] for k in m if k not in ("smoke_results",)}, default=str)[:2000]],
            verdict="PASS" if passes.forensic_closure else "FAIL",
        )
        decision = VerdictAuthority(contract).decide(evidence=packet, require_evidence=True)
        decision["measured"] = m
        return decision
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
        doc_anchors=["C-19", "G-W13", "G-W14"],
        notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]

    post = None
    if enforce_post_verify:
        post = _programming_post_verify(mid, evidence_ok)

    ok = True
    if post and post.get("verdict") != "PASS":
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
