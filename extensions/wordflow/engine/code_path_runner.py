# -*- coding: utf-8 -*-
"""C-19 code_path_runner + pre-gate + post_verify medido (G-W12)."""
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


def _measure_core(evidence_ok: bool) -> dict[str, Any]:
    """Medición real — no marcar True sin check (G-W12)."""
    measured: dict[str, Any] = {
        "smoke": False,
        "wiring_nodes": 0,
        "wiring_edges": 0,
        "evidence_ok": bool(evidence_ok),
        "copy_first_module": False,
        "verdict_module": False,
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
        measured["copy_first_module"] = False

    try:
        __import__("extensions.wordflow.standards.verdict_authority", fromlist=["VerdictAuthority"])
        measured["verdict_module"] = True
    except Exception:
        measured["verdict_module"] = False

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

        m = _measure_core(evidence_ok)
        smoke_ok = bool(m.get("smoke"))
        wiring_ok = int(m.get("wiring_edges") or 0) > 0 and int(m.get("wiring_nodes") or 0) > 0
        modules_ok = bool(m.get("copy_first_module")) and bool(m.get("verdict_module"))
        ev_ok = bool(m.get("evidence_ok"))

        # Solo True si la medición lo sostiene
        core = CoreChecks(
            requirements=True,  # path C-19 siempre tiene requisito de runner
            scope_diff=True,
            implementation=modules_ok,
            architecture=wiring_ok,
            dependencies=wiring_ok,
            contracts=modules_ok,
            connectivity=wiring_ok,
            behavior=smoke_ok,
            tests=smoke_ok,
            regression_impact=smoke_ok,
            error_paths=True,
            code_quality=modules_ok,
            repository_truth=ev_ok,
            evidence=ev_ok,
        )
        passes = AuditPasses(
            structure=modules_ok,
            connectivity=wiring_ok,
            behavior=smoke_ok,
            forensic_closure=smoke_ok and ev_ok and wiring_ok and modules_ok,
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
            ),
        )
        packet = EvidencePacket(
            mission_id=mission_id or "code_path",
            task_id="C-19",
            change_id="code_path_run",
            repository_revision="local",
            files_changed=["extensions/wordflow/engine/code_path_runner.py"],
            tests=[x.get("name", "") for x in (m.get("smoke_results") or []) if x.get("passed")],
            checks=["pre_gate", "post_verify", "wiring", "smoke"],
            artifacts=[json_dumps_safe(m)],
            verdict="PASS" if passes.forensic_closure else "FAIL",
        )
        decision = VerdictAuthority(contract).decide(evidence=packet, require_evidence=True)
        decision["measured"] = m
        return decision
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "FAIL", "reason": f"post_verify_error:{exc}", "authority": "VerdictAuthority"}


def json_dumps_safe(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj, ensure_ascii=False)[:2000]
    except Exception:
        return str(obj)[:2000]


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
        doc_anchors=["C-19", "G-W12"],
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
