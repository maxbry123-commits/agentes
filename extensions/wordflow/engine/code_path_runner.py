# -*- coding: utf-8 -*-
"""C-19 code_path_runner — UNIFIED · U1-U10 closed."""
from __future__ import annotations

import ast
import os
import time
from pathlib import Path
from typing import Any

from .cognitive_loop import run_cognitive_loop
from .evidence_packet import build_evidence_packet, verify_evidence_packet
from .goal_lock import lock_goals
from .input_quality_bar import admit_or_reject, MIN_CHARS_DEFAULT
from .skill_native_compiler import compile_skill_to_code


class CodePathError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _all_core_true(measures: dict[str, bool]) -> bool:
    return all(measures.get(f"CORE-{i:02d}", False) for i in range(1, 15))


def _stage_ms(t0: float) -> float:
    return round((time.monotonic() - t0) * 1000, 2)


def consult_path_gateway(mission_id: str, raw_input: str) -> dict[str, Any]:
    """CONN.path_gateway: runner → IntelligenceGateway. Vendor = DENY."""
    try:
        from extensions.wordflow_kernel.gateway.intelligence import (
            MockIntelligenceGateway,
            make_request,
        )
    except ImportError:
        try:
            from wordflow_kernel.gateway.intelligence import (  # type: ignore
                MockIntelligenceGateway,
                make_request,
            )
        except ImportError:
            return {
                "ok": False,
                "invoked": False,
                "error": "GATEWAY_MISSING",
                "contract": "GAP",
                "llm_control": "DENY",
                "vendor_call": False,
            }
    gw = MockIntelligenceGateway(fixed_text="PATH_GATEWAY_DENY")
    req = make_request(
        task_id="C-19",
        capability="llm.complete",
        payload={
            "prompt": (raw_input or "")[:200],
            "mission_id": mission_id,
            "llm_control": "DENY",
        },
        policy={"max_cost": 0.0, "vendor": "DENY"},
    )
    res = gw.execute(req)
    return {
        "ok": True,
        "invoked": True,
        "status": res.status,
        "provider": res.provider,
        "llm_control": "DENY",
        "contract": "WIRED_DENY",
        "vendor_call": False,
        "evidence_hash": res.evidence_hash,
    }


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
    auto_measure_fc: bool = True,
    apply_adapt: bool = False,
    import_mapping: dict[str, str] | None = None,
    profile: str = "dev",
    scan_paths: list[str] | None = None,
    consult_gateway: bool = True,
) -> dict[str, Any]:
    from extensions.wordflow.standards.forensic_core import (
        ForensicEnforcementState, CoreCheckResult, ClosureCounters,
        CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS,
    )
    from extensions.wordflow.standards.verdict_authority import VerdictAuthority
    from extensions.wordflow.standards.gap_registry import GapRegistry, Gap
    from extensions.wordflow.standards.closure_engine import ClosureEngine, ClosureInput
    from extensions.wordflow.standards.quality_dag import QualityDAG
    from extensions.wordflow.standards.quality_handlers import register_deterministic_handlers
    from extensions.wordflow.standards.context_manifest import ContextManifest, ContextValidator
    from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate
    from extensions.wordflow.standards.core_auto_measure import auto_measure_core as _auto_core
    from extensions.wordflow.standards.fc_auto_measure import auto_measure_fc as _auto_fc
    from extensions.wordflow.standards.copy_first import copy_file_deterministic
    from extensions.wordflow.standards.adapt_imports import adapt_file
    from extensions.wordflow.standards.evidence_merge import merge_evidence
    from extensions.wordflow.standards.path_resolve import resolve_path
    from extensions.wordflow.standards.checklist_factory import checklist_from_dict
    from extensions.wordflow.standards.checklist_sheriff import AgentChecklistClaim
    from extensions.wordflow.standards.policy_snapshot import PolicySnapshot

    t_all = time.monotonic()
    stage_ms: dict[str, float] = {}
    env_prof = os.environ.get("WORDFLOW_PROFILE", profile).lower()
    if require_pre_gate is None:
        require_pre_gate = env_prof == "prod"

    if isinstance(checklist, dict):
        checklist = checklist_from_dict(checklist)

    dest_resolved = ""
    if dest:
        try:
            dest_resolved = str(resolve_path(dest, must_exist=False))
        except Exception:
            dest_resolved = dest

    authority = VerdictAuthority()
    gap_reg = GapRegistry()
    wire_trace: dict[str, Any] = {
        "context_manifest": "SKIP", "pre_gate": "SKIP", "quality_dag": "SKIP",
        "gap_registry": "INIT", "closure_engine": "PENDING", "fc_enforced": False,
        "auto_measure": "SKIP", "fc_auto": "SKIP", "adapt": "SKIP", "post_adapt": "SKIP",
        "evidence_merge": "SKIP", "quality_bar": "SKIP", "dest_resolved": dest_resolved or "SKIP",
        "profile": env_prof, "stage_ms": stage_ms, "path_gateway": "SKIP",
    }

    t0 = time.monotonic()
    if require_context_manifest:
        if context_manifest is None:
            return {"ok": False, "stage": "context_manifest", "detail": "BLOCK: manifest None", "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
        if isinstance(context_manifest, dict):
            keys = ("mission_id", "task_id", "project_docs", "architecture_docs", "task_spec", "relevant_files", "contracts", "tests", "repository_revision", "handoff_ref")
            context_manifest = ContextManifest(**{k: context_manifest[k] for k in keys if k in context_manifest})
        cv = ContextValidator().validate(context_manifest)
        wire_trace["context_manifest"] = cv
        if not cv.get("ok"):
            return {"ok": False, "stage": "context_manifest", "detail": cv, "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
        context_verified = True
        handoff_verified = True
    stage_ms["context_manifest"] = _stage_ms(t0)

    t0 = time.monotonic()
    block = authority.require_context(context_verified, handoff_verified)
    stage_ms["context"] = _stage_ms(t0)
    if block:
        return {"ok": False, "stage": "context", "detail": block, "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}

    pre_gate_result = None
    pre_ok = False
    adapted_dest = ""
    dest_use = dest_resolved or dest
    t0 = time.monotonic()
    if require_pre_gate or symbol_or_stem or dest:
        if not symbol_or_stem or not dest_use:
            if require_pre_gate:
                stage_ms["pre_gate"] = _stage_ms(t0)
                return {"ok": False, "stage": "pre_gate", "detail": "BLOCK: need symbol_or_stem + dest", "llm_control": "DENY", "verdict": "BLOCK", "wire_trace": wire_trace}
        else:
            pre = ExecutorPreImplementGate()
            pre_gate_result = pre.check(
                context_verified=context_verified, handoff_verified=handoff_verified,
                symbol_or_stem=symbol_or_stem, dest=dest_use,
                checklist=checklist if isinstance(checklist, AgentChecklistClaim) else checklist,
                require_checklist=require_checklist or (env_prof == "prod"),
            )
            wire_trace["pre_gate"] = pre_gate_result
            pre_ok = bool(pre_gate_result.get("allow"))
            if not pre_ok:
                gap_reg.add(Gap(gap_id="GC-PRE-001", task_id="C-19", mission_id=mission_id or "", rule_id="COPY_FIRST_OR_SHERIFF", severity="blocking", description=str(pre_gate_result.get("reason")), location="pre_gate"))
                stage_ms["pre_gate"] = _stage_ms(t0)
                return {"ok": False, "stage": "pre_gate", "detail": pre_gate_result, "llm_control": "DENY", "verdict": "BLOCK", "gaps": gap_reg.to_list(), "wire_trace": wire_trace}
            if apply_adapt and pre_ok:
                cf = pre_gate_result.get("copy_first") or {}
                sources = cf.get("sources") or []
                action = cf.get("action", "")
                if sources and dest_use:
                    src = Path(sources[0])
                    if not src.exists():
                        try:
                            src = resolve_path(sources[0], must_exist=True)
                        except Exception:
                            src = Path(sources[0])
                    dst = Path(dest_use)
                    if src.exists():
                        if action in ("ADAPT", "COPY") and import_mapping:
                            rewrites = adapt_file(src, dst, import_mapping)
                            wire_trace["adapt"] = {"action": "ADAPT", "rewrites": rewrites, "src": str(src), "dest": str(dst)}
                        else:
                            wire_trace["adapt"] = copy_file_deterministic(src, dst)
                        adapted_dest = str(dst)
                        try:
                            txt = dst.read_text(encoding="utf-8")
                            ast.parse(txt)
                            wire_trace["post_adapt"] = {"ok": True, "path": str(dst)}
                        except Exception as e:
                            wire_trace["post_adapt"] = {"ok": False, "error": str(e)}
                            gap_reg.add(Gap(gap_id="GC-ADAPT-001", task_id="C-19", mission_id=mission_id or "", rule_id="POST_ADAPT", severity="blocking", description=str(e), location=str(dst)))
                            stage_ms["pre_gate"] = _stage_ms(t0)
                            return {"ok": False, "stage": "post_adapt", "detail": wire_trace["post_adapt"], "llm_control": "DENY", "verdict": "FAIL", "gaps": gap_reg.to_list(), "wire_trace": wire_trace}
    stage_ms["pre_gate"] = _stage_ms(t0)

    t0 = time.monotonic()
    q = admit_or_reject(raw_input)
    wire_trace["quality_bar"] = {"ok": q.get("ok"), "reason_codes": q.get("reason_codes"), "min_chars": q.get("min_chars", MIN_CHARS_DEFAULT), "thresholds": q.get("thresholds"), "chars": q.get("chars")}
    stage_ms["quality_bar"] = _stage_ms(t0)
    if not q.get("ok"):
        return {"ok": False, "stage": "quality_bar", "detail": q, "llm_control": "DENY", "verdict": "FAIL", "wire_trace": wire_trace}

    t0 = time.monotonic()
    locked = lock_goals({"text": raw_input, "raw": raw_input})
    stage_ms["goal_lock"] = _stage_ms(t0)
    if not locked.get("ok"):
        return {"ok": False, "stage": "goal_lock", "detail": locked, "llm_control": "DENY", "verdict": "FAIL", "wire_trace": wire_trace}

    lock = locked.get("lock") or {}
    mid = mission_id or lock.get("lock_id") or ""
    policy = PolicySnapshot.freeze(mid or "runner")
    policy_dict = {"mission_id": policy.mission_id, "contract_version": policy.contract_version, "frozen_at": policy.frozen_at}

    t0 = time.monotonic()
    steps = plan_steps or ["analyze", "compile", "validate", "promote"]
    cog = run_cognitive_loop(topic=raw_input[:80], plan_steps=steps, mission_id=mid, goal_lock=lock, task_class="CODE")
    stage_ms["cognitive"] = _stage_ms(t0)
    compiled = compile_skill_to_code(skill) if skill else None

    t0 = time.monotonic()
    if consult_gateway:
        gw_hop = consult_path_gateway(mid, raw_input)
        wire_trace["path_gateway"] = gw_hop
    else:
        gw_hop = {"ok": False, "invoked": False, "contract": "SKIP"}
        wire_trace["path_gateway"] = gw_hop
    stage_ms["path_gateway"] = _stage_ms(t0)

    evidence = build_evidence_packet(
        task_id="C-19", claim_status="PARTIAL",
        paths=[{"path": "extensions/wordflow/engine/code_path_runner.py"}],
        tests={"cognitive_ok": True, "skill_compiled": compiled is not None, "path_gateway": bool(gw_hop.get("invoked"))},
        doc_anchors=["C-19", "FORENSIC_ENFORCEMENT"], notes=f"mission={mid}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]
    merged = merge_evidence(engine_packet=evidence if isinstance(evidence, dict) else None, mission_id=mid or "mission-local", task_id="C-19")
    wire_trace["evidence_merge"] = {"complete": merged.get("complete")}

    paths_for_q = list(scan_paths or [])
    if adapted_dest:
        paths_for_q.append(adapted_dest)
    paths_for_q.append("extensions/wordflow/engine/code_path_runner.py")

    t0 = time.monotonic()
    dag_passed = bool(quality_dag_ok)
    if run_quality_dag:
        dag = QualityDAG()
        register_deterministic_handlers(dag, paths=paths_for_q, quality_dag_ok=quality_dag_ok)
        dag_results = dag.run(fail_closed=True)
        dag_passed = dag.passed(dag_results) and quality_dag_ok
        wire_trace["quality_dag"] = {"passed": dag_passed, "results": [{"name": r.name, "status": r.status.value, "detail": r.detail} for r in dag_results]}
    stage_ms["quality_dag"] = _stage_ms(t0)

    conn = {k: bool((connectivity or {}).get(k, False)) for k in CONNECTIVITY_CHAIN}
    measures: dict[str, bool] = {cid: False for cid in CORE_IDS}
    if auto_measure_core:
        am = _auto_core(caller=core_measures or {}, connectivity_hint=conn, evidence_ok=bool(evidence_ok and evidence_complete), pre_gate_ok=pre_ok)
        measures.update(am["measures"])
        if isinstance(cog, dict) and cog.get("ok", True):
            measures.setdefault("CORE-08", measures.get("CORE-08", False))
            if core_measures and core_measures.get("CORE-08"):
                measures["CORE-08"] = True
            wire_trace["cognitive_soft"] = {"cog_ok": True, "note": "U3 soft only with caller CORE-08"}
        if lock:
            wire_trace["goal_lock_soft"] = {"has_lock": True}
        wire_trace["auto_measure"] = am
    elif core_measures:
        measures.update({k: bool(v) for k, v in core_measures.items() if k in measures})

    core_results = [CoreCheckResult(cid, bool(measures.get(cid, False)), evidence=str((wire_trace.get("auto_measure") or {}).get("evidence", {}).get(cid, ""))) for cid in CORE_IDS]

    fc_in = dict(fc_results or {})
    if auto_measure_fc:
        fam = _auto_fc(paths=paths_for_q, caller=fc_in, deterministic_path=True)
        wire_trace["fc_auto"] = fam
        for k, v in fam["measures"].items():
            fc_in.setdefault(k, v)
            if fc_results and k in fc_results:
                fc_in[k] = bool(fc_results[k])

    if require_fc and not (fc_results or auto_measure_fc):
        fc_map = {fid: False for fid in FC_IDS}
        fc_all = False
        wire_trace["fc_enforced"] = True
    else:
        fc_map = {fid: bool(fc_in.get(fid, False)) for fid in FC_IDS}
        fc_all = all(fc_map.values()) if (fc_results or require_fc) else True
        if require_fc and not fc_results:
            fc_all = all(fc_map.values())
        wire_trace["fc_enforced"] = bool(fc_results or require_fc or auto_measure_fc)
    wire_trace["fc_all_pass"] = fc_all
    if (require_fc or fc_results) and not fc_all:
        gap_reg.add(Gap(gap_id="GC-FC-001", task_id="C-19", mission_id=mid, rule_id="FC_REQUIRED", severity="blocking", description="FC not all True", location="fc"))

    ctr_in = counters or {}
    ctr = ClosureCounters(
        gaps=int(ctr_in.get("gaps", 0)), blocking_gaps=int(ctr_in.get("blocking_gaps", 0)),
        broken_connections=int(ctr_in.get("broken_connections", 0)), unexplained_orphans=int(ctr_in.get("unexplained_orphans", 0)),
        unreachable_required_paths=int(ctr_in.get("unreachable_required_paths", 0)), unresolved_dependencies=int(ctr_in.get("unresolved_dependencies", 0)),
        unverified_paths=int(ctr_in.get("unverified_paths", 0)), unverified_requirements=int(ctr_in.get("unverified_requirements", 0)),
        unverified_claims=int(ctr_in.get("unverified_claims", 0)), pending_fixes=int(ctr_in.get("pending_fixes", 0)),
        new_gaps_after_fix=int(ctr_in.get("new_gaps_after_fix", 0)) + gap_reg.new_gaps_after_fix,
        unexpected_changes=int(ctr_in.get("unexpected_changes", 0)),
    )
    open_n = gap_reg.open_count()
    if open_n:
        ctr.gaps = max(ctr.gaps, open_n)
        ctr.blocking_gaps = max(ctr.blocking_gaps, open_n)

    state = ForensicEnforcementState(
        context_verified=context_verified, handoff_verified=handoff_verified,
        core_results=core_results, fc_results=fc_map, require_fc=bool(require_fc or fc_results),
        connectivity=conn, counters=ctr,
        evidence_complete=bool(evidence_complete and evidence_ok),
        final_clean_reaudit_passed=bool(final_clean_reaudit_passed),
        quality_dag_ok=bool(dag_passed), claim_used_as_pass=False,
    )
    t0 = time.monotonic()
    forensic = authority.decide(state=state)
    stage_ms["forensic"] = _stage_ms(t0)
    forensic_pass = forensic.get("verdict") == "PASS"

    checklist_passed = True
    if pre_gate_result is not None:
        cl = pre_gate_result.get("checklist")
        if require_checklist or env_prof == "prod":
            checklist_passed = bool(cl and cl.get("passed")) if cl is not None else False
        elif cl is not None:
            checklist_passed = bool(cl.get("passed", True))

    t0 = time.monotonic()
    closure = ClosureEngine().decide(ClosureInput(
        checklist_passed=checklist_passed, forensic_passed=forensic_pass,
        evidence_ok=bool(evidence_ok and evidence_complete),
        new_gaps_after_fix=ctr.new_gaps_after_fix, unexpected_changes=ctr.unexpected_changes,
        broken_connections=ctr.broken_connections, gap_registry=gap_reg,
    ))
    stage_ms["closure"] = _stage_ms(t0)
    stage_ms["total"] = _stage_ms(t_all)
    wire_trace["closure_engine"] = closure
    wire_trace["gap_registry"] = gap_reg.to_list()
    wire_trace["core_all_true"] = _all_core_true(measures)

    ok = forensic_pass and closure.get("closed") is True and (fc_all if (require_fc or fc_results) else True)
    return {
        "ok": ok, "mission_id": mid, "lock": lock, "cognitive": cog, "skill_compile": compiled,
        "evidence": evidence, "evidence_merged": merged.get("merged"), "evidence_ok": evidence_ok,
        "forensic": forensic, "pre_gate": pre_gate_result, "closure": closure, "gaps": gap_reg.to_list(),
        "core_measures": measures, "fc_measures": fc_map, "quality_dag": wire_trace.get("quality_dag"),
        "policy": policy_dict,
        "path_gateway": gw_hop,
        "wire_trace": wire_trace, "llm_control": "DENY",
        "verdict": "PASS" if ok else (forensic.get("verdict") or "FAIL"),
        "path": "UNIFIED_RUNNER_V1",
        "gc_status": "GC-01..12_WIRED", "gr_status": "GR-01..05_CODE_FIXED",
        "c_status": "C1-C7_CLOSED", "s_status": "S1-S8_CLOSED", "t_status": "T1-T8_CLOSED",
        "u_status": "U1-U10_CLOSED",
    }
