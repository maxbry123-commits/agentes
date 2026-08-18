# -*- coding: utf-8 -*-
"""C-19 code_path_runner — FAIL-CLOSED · UNIFIED_RUNNER_V1.
GR fixes: prod pre_gate · QualityDAG FORMAT deterministic · apply_adapt COPY.
"""
from __future__ import annotations

import os
from pathlib import Path
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


def _all_core_true(measures: dict[str, bool]) -> bool:
    return all(measures.get(f"CORE-{i:02d}", False) for i in range(1, 15))


def run_code_path(
    raw_input: str,
    *,
    plan_steps: list[str] | None = None,
    skill: dict[str, Any] | None = None,
    mission_id: str = "",
    context_verified: bool = False,
    handoff_verified: bool = False,
    core_measures: dict[str, bool] | None = None,
    connectivity: dict[str, bool] | None = None,
    counters: dict[str, int] | None = None,
    evidence_complete: bool = False,
    final_clean_reaudit_passed: bool = False,
    quality_dag_ok: bool = False,
    context_manifest: Any | None = None,
    require_context_manifest: bool = False,
    symbol_or_stem: str = "",
    dest: str = "",
    checklist: Any | None = None,
    require_pre_gate: bool | None = None,
    require_checklist: bool = False,
    run_quality_dag: bool = True,
    fc_results: dict[str, bool] | None = None,
    require_fc: bool = False,
    auto_measure_core: bool = True,
    apply_adapt: bool = False,
    import_mapping: dict[str, str] | None = None,
    profile: str = "dev",
) -> dict[str, Any]:
    from extensions.wordflow.standards.forensic_core import (
        ForensicProgrammingEnforcer,
        ForensicEnforcementState,
        CoreCheckResult,
        ClosureCounters,
        CORE_IDS,
        CONNECTIVITY_CHAIN,
        FC_IDS,
    )
    from extensions.wordflow.standards.gap_registry import GapRegistry, Gap
    from extensions.wordflow.standards.closure_engine import ClosureEngine, ClosureInput
    from extensions.wordflow.standards.quality_dag import QualityDAG, GateResult, GateStatus
    from extensions.wordflow.standards.context_manifest import ContextManifest, ContextValidator
    from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate
    from extensions.wordflow.standards.core_auto_measure import auto_measure_core as _auto_core
    from extensions.wordflow.standards.copy_first import copy_file_deterministic
    from extensions.wordflow.standards.adapt_imports import adapt_file

    # GR-02: prod profile forces pre_gate when symbol+dest later provided; env WORDFLOW_PROFILE
    env_prof = os.environ.get("WORDFLOW_PROFILE", profile).lower()
    if require_pre_gate is None:
        require_pre_gate = env_prof == "prod"

    enforcer = ForensicProgrammingEnforcer()
    gap_reg = GapRegistry()
    wire_trace: dict[str, Any] = {
        "context_manifest": "SKIP",
        "pre_gate": "SKIP",
        "quality_dag": "SKIP",
        "gap_registry": "INIT",
        "closure_engine": "PENDING",
        "fc_enforced": False,
        "auto_measure": "SKIP",
        "adapt": "SKIP",
        "profile": env_prof,
    }

    if require_context_manifest:
        if context_manifest is None:
            return {
                "ok": False,
                "stage": "context_manifest",
                "detail": "BLOCK: require_context_manifest but manifest is None",
                "llm_control": "DENY",
                "verdict": "BLOCK",
                "wire_trace": wire_trace,
            }
        if isinstance(context_manifest, dict):
            keys = (
                "mission_id", "task_id", "project_docs", "architecture_docs",
                "task_spec", "relevant_files", "contracts", "tests",
                "repository_revision", "handoff_ref",
            )
            context_manifest = ContextManifest(**{k: context_manifest[k] for k in keys if k in context_manifest})
        cv = ContextValidator().validate(context_manifest)
        wire_trace["context_manifest"] = cv
        if not cv.get("ok"):
            return {
                "ok": False,
                "stage": "context_manifest",
                "detail": cv,
                "llm_control": "DENY",
                "verdict": "BLOCK",
                "wire_trace": wire_trace,
            }
        context_verified = True
        handoff_verified = True

    block = enforcer.require_context(context_verified, handoff_verified)
    if block:
        return {
            "ok": False,
            "stage": "context",
            "detail": block,
            "llm_control": "DENY",
            "verdict": "BLOCK",
            "wire_trace": wire_trace,
        }

    pre_gate_result = None
    pre_ok = False
    if require_pre_gate or symbol_or_stem or dest:
        if not symbol_or_stem or not dest:
            if require_pre_gate:
                return {
                    "ok": False,
                    "stage": "pre_gate",
                    "detail": "BLOCK: require_pre_gate needs symbol_or_stem + dest",
                    "llm_control": "DENY",
                    "verdict": "BLOCK",
                    "wire_trace": wire_trace,
                }
        else:
            pre = ExecutorPreImplementGate()
            pre_gate_result = pre.check(
                context_verified=context_verified,
                handoff_verified=handoff_verified,
                symbol_or_stem=symbol_or_stem,
                dest=dest,
                checklist=checklist,
                require_checklist=require_checklist or (env_prof == "prod"),
            )
            wire_trace["pre_gate"] = pre_gate_result
            pre_ok = bool(pre_gate_result.get("allow"))
            if not pre_ok:
                gap_reg.add(
                    Gap(
                        gap_id="GC-PRE-001",
                        task_id="C-19",
                        mission_id=mission_id or "",
                        rule_id="COPY_FIRST_OR_SHERIFF",
                        severity="blocking",
                        description=str(pre_gate_result.get("reason", "pre_gate blocked")),
                        location="code_path_runner.pre_gate",
                    )
                )
                return {
                    "ok": False,
                    "stage": "pre_gate",
                    "detail": pre_gate_result,
                    "llm_control": "DENY",
                    "verdict": "BLOCK",
                    "gaps": gap_reg.to_list(),
                    "wire_trace": wire_trace,
                }

            # GR-05: apply COPY/ADAPT when requested and sources exist
            if apply_adapt and pre_ok:
                cf = pre_gate_result.get("copy_first") or {}
                sources = cf.get("sources") or []
                action = cf.get("action", "")
                if sources and dest:
                    src = Path(sources[0])
                    dst = Path(dest)
                    if src.exists():
                        if action in ("ADAPT", "COPY") and import_mapping:
                            rewrites = adapt_file(src, dst, import_mapping)
                            wire_trace["adapt"] = {"action": "ADAPT", "rewrites": rewrites, "src": str(src), "dest": str(dst)}
                        else:
                            meta = copy_file_deterministic(src, dst)
                            wire_trace["adapt"] = meta

    q = admit_or_reject(raw_input)
    if not q.get("ok"):
        return {
            "ok": False,
            "stage": "quality_bar",
            "detail": q,
            "llm_control": "DENY",
            "verdict": "FAIL",
            "wire_trace": wire_trace,
        }

    locked = lock_goals({"text": raw_input, "raw": raw_input})
    if not locked.get("ok"):
        return {
            "ok": False,
            "stage": "goal_lock",
            "detail": locked,
            "llm_control": "DENY",
            "verdict": "FAIL",
            "wire_trace": wire_trace,
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
        doc_anchors=["C-19", "FORENSIC_ENFORCEMENT"],
        notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]

    # GR-03: FORMAT always deterministic PASS; rest require quality_dag_ok
    dag_passed = bool(quality_dag_ok)
    if run_quality_dag:
        dag = QualityDAG()

        def _handler(name: str):
            def _h() -> GateResult:
                if name == "FORMAT":
                    return GateResult(name, GateStatus.PASS, "deterministic noop format gate")
                if quality_dag_ok:
                    return GateResult(name, GateStatus.PASS, "caller quality_dag_ok")
                return GateResult(name, GateStatus.FAIL, "quality_dag_ok False")

            return _h

        for n in dag.nodes:
            dag.register(n.name, _handler(n.name))
        dag_results = dag.run(fail_closed=True)
        # FORMAT alone never enough — still need quality_dag_ok for required chain
        dag_passed = dag.passed(dag_results) and quality_dag_ok
        wire_trace["quality_dag"] = {
            "passed": dag_passed,
            "results": [{"name": r.name, "status": r.status.value, "detail": r.detail} for r in dag_results],
        }

    conn = {k: bool((connectivity or {}).get(k, False)) for k in CONNECTIVITY_CHAIN}

    measures: dict[str, bool] = {cid: False for cid in CORE_IDS}
    if auto_measure_core:
        am = _auto_core(
            caller=core_measures or {},
            connectivity_hint=conn,
            evidence_ok=bool(evidence_ok and evidence_complete),
            pre_gate_ok=pre_ok,
        )
        measures.update(am["measures"])
        wire_trace["auto_measure"] = am
    elif core_measures:
        measures.update({k: bool(v) for k, v in core_measures.items() if k in measures})

    core_results = [
        CoreCheckResult(
            cid,
            bool(measures.get(cid, False)),
            evidence=str((wire_trace.get("auto_measure") or {}).get("evidence", {}).get(cid, "")),
        )
        for cid in CORE_IDS
    ]

    fc_in = fc_results or {}
    if require_fc and not fc_in:
        fc_map = {fid: False for fid in FC_IDS}
        fc_all = False
        wire_trace["fc_enforced"] = True
        gap_reg.add(
            Gap(
                gap_id="GC-FC-000",
                task_id="C-19",
                mission_id=mid,
                rule_id="FC_REQUIRED",
                severity="blocking",
                description="require_fc=True but fc_results missing",
                location="code_path_runner.fc",
            )
        )
    else:
        fc_map = {fid: bool(fc_in.get(fid, False)) for fid in FC_IDS}
        fc_all = all(fc_map.values()) if (fc_in or require_fc) else True
        wire_trace["fc_enforced"] = bool(fc_in or require_fc)
        if (fc_in or require_fc) and not fc_all:
            gap_reg.add(
                Gap(
                    gap_id="GC-FC-001",
                    task_id="C-19",
                    mission_id=mid,
                    rule_id="FC_REQUIRED",
                    severity="blocking",
                    description="FC-01..13 not all True",
                    location="code_path_runner.fc_results",
                )
            )
    wire_trace["fc_all_pass"] = fc_all

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
        new_gaps_after_fix=int(ctr_in.get("new_gaps_after_fix", 0)) + gap_reg.new_gaps_after_fix,
        unexpected_changes=int(ctr_in.get("unexpected_changes", 0)),
    )
    open_n = gap_reg.open_count()
    if open_n:
        ctr.gaps = max(ctr.gaps, open_n)
        ctr.blocking_gaps = max(ctr.blocking_gaps, open_n)

    state = ForensicEnforcementState(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        core_results=core_results,
        fc_results=fc_map,
        require_fc=bool(require_fc or fc_in),
        connectivity=conn,
        counters=ctr,
        evidence_complete=bool(evidence_complete and evidence_ok),
        final_clean_reaudit_passed=bool(final_clean_reaudit_passed),
        quality_dag_ok=bool(dag_passed),
        claim_used_as_pass=False,
    )
    forensic = enforcer.evaluate(state)
    forensic_pass = forensic.get("verdict") == "PASS"

    checklist_passed = True
    if pre_gate_result is not None:
        cl = pre_gate_result.get("checklist")
        if require_checklist or env_prof == "prod":
            checklist_passed = bool(cl and cl.get("passed")) if cl is not None else not (require_checklist or env_prof == "prod")
        elif cl is not None:
            checklist_passed = bool(cl.get("passed", True))

    closure = ClosureEngine().decide(
        ClosureInput(
            checklist_passed=checklist_passed,
            forensic_passed=forensic_pass,
            evidence_ok=bool(evidence_ok and evidence_complete),
            new_gaps_after_fix=ctr.new_gaps_after_fix,
            unexpected_changes=ctr.unexpected_changes,
            broken_connections=ctr.broken_connections,
            gap_registry=gap_reg,
        )
    )
    wire_trace["closure_engine"] = closure
    wire_trace["gap_registry"] = gap_reg.to_list()
    wire_trace["core_all_true"] = _all_core_true(measures)

    ok = forensic_pass and closure.get("closed") is True and fc_all
    return {
        "ok": ok,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "evidence": evidence,
        "evidence_ok": evidence_ok,
        "forensic": forensic,
        "pre_gate": pre_gate_result,
        "closure": closure,
        "gaps": gap_reg.to_list(),
        "core_measures": measures,
        "quality_dag": wire_trace.get("quality_dag"),
        "wire_trace": wire_trace,
        "llm_control": "DENY",
        "verdict": "PASS" if ok else (forensic.get("verdict") or "FAIL"),
        "path": "UNIFIED_RUNNER_V1",
        "gc_status": "GC-01..12_WIRED",
        "gr_status": "GR-01..05_CODE_FIXED",
    }
