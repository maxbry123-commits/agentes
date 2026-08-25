# -*- coding: utf-8 -*-
"""C-19 modular runner — orchestrates processes 01→12 (same semantics as legacy)."""
from __future__ import annotations

import os
import time
from typing import Any

from .01_context_gate import run_context_manifest, run_require_context
from .02_pre_gate import run_pre_gate
from .03_quality_bar import run_quality_bar
from .04_goal_lock import run_goal_lock
from .05_cognitive import run_cognitive
from .06_evidence import run_evidence, consult_path_gateway
from .07_quality_dag import run_quality_dag
from .08_measures import run_measures
from .09_forensic import run_forensic
from .10_verdict import checklist_passed_from_pre
from .11_closure import run_closure
from .12_return import build_return


class CodePathError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _stage_ms(t0: float) -> float:
    return round((time.monotonic() - t0) * 1000, 2)


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
    from extensions.wordflow.standards.gap_registry import GapRegistry
    from extensions.wordflow.standards.checklist_factory import checklist_from_dict
    from extensions.wordflow.standards.path_resolve import resolve_path
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

    gap_reg = GapRegistry()
    wire_trace: dict[str, Any] = {
        "context_manifest": "SKIP", "pre_gate": "SKIP", "quality_dag": "SKIP",
        "gap_registry": "INIT", "closure_engine": "PENDING", "fc_enforced": False,
        "auto_measure": "SKIP", "fc_auto": "SKIP", "adapt": "SKIP", "post_adapt": "SKIP",
        "evidence_merge": "SKIP", "quality_bar": "SKIP", "dest_resolved": dest_resolved or "SKIP",
        "profile": env_prof, "stage_ms": stage_ms, "path_gateway": "SKIP",
        "modular": True,
    }

    # 01 context
    t0 = time.monotonic()
    cm = run_context_manifest(
        require_context_manifest=require_context_manifest,
        context_manifest=context_manifest,
        wire_trace=wire_trace,
    )
    stage_ms["context_manifest"] = _stage_ms(t0)
    if cm is not None and not cm.get("_continue"):
        return cm
    if cm and cm.get("_continue"):
        context_verified = True
        handoff_verified = True

    t0 = time.monotonic()
    block = run_require_context(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        wire_trace=wire_trace,
    )
    stage_ms["context"] = _stage_ms(t0)
    if block:
        return block

    # 02 pre_gate
    t0 = time.monotonic()
    pre = run_pre_gate(
        require_pre_gate=require_pre_gate,
        symbol_or_stem=symbol_or_stem,
        dest=dest,
        dest_resolved=dest_resolved,
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        checklist=checklist,
        require_checklist=require_checklist,
        apply_adapt=apply_adapt,
        import_mapping=import_mapping,
        mission_id=mission_id,
        env_prof=env_prof,
        gap_reg=gap_reg,
        wire_trace=wire_trace,
    )
    stage_ms["pre_gate"] = _stage_ms(t0)
    if pre.get("block"):
        return pre["block"]
    pre_gate_result = pre.get("pre_gate_result")
    pre_ok = bool(pre.get("pre_ok"))
    adapted_dest = pre.get("adapted_dest") or ""

    # 03 quality_bar
    t0 = time.monotonic()
    qb = run_quality_bar(raw_input, wire_trace)
    stage_ms["quality_bar"] = _stage_ms(t0)
    if qb:
        return qb

    # 04 goal_lock
    t0 = time.monotonic()
    gl = run_goal_lock(raw_input, wire_trace)
    stage_ms["goal_lock"] = _stage_ms(t0)
    if not gl.get("ok"):
        return gl
    lock = gl["lock"]
    mid = mission_id or gl.get("mission_id_hint") or ""
    policy = PolicySnapshot.freeze(mid or "runner")
    policy_dict = {
        "mission_id": policy.mission_id,
        "contract_version": policy.contract_version,
        "frozen_at": policy.frozen_at,
    }

    # 05 cognitive
    t0 = time.monotonic()
    cog_out = run_cognitive(
        raw_input=raw_input, plan_steps=plan_steps, mission_id=mid, lock=lock, skill=skill,
    )
    stage_ms["cognitive"] = _stage_ms(t0)
    cog = cog_out["cognitive"]
    compiled = cog_out["skill_compile"]

    # 06 evidence
    t0 = time.monotonic()
    ev = run_evidence(
        mission_id=mid, raw_input=raw_input, compiled=compiled,
        consult_gateway=consult_gateway, wire_trace=wire_trace,
    )
    stage_ms["path_gateway"] = _stage_ms(t0)
    evidence = ev["evidence"]
    evidence_ok = ev["evidence_ok"]
    merged = ev["merged"]
    gw_hop = ev["path_gateway"]

    # 07 quality_dag
    t0 = time.monotonic()
    dag_passed = run_quality_dag(
        run_quality_dag_flag=run_quality_dag,
        quality_dag_ok=quality_dag_ok,
        scan_paths=scan_paths,
        adapted_dest=adapted_dest,
        wire_trace=wire_trace,
    )
    stage_ms["quality_dag"] = _stage_ms(t0)

    paths_for_q = list(scan_paths or [])
    if adapted_dest:
        paths_for_q.append(adapted_dest)
    paths_for_q.append("extensions/wordflow/engine/programming/runner.py")

    # 08 measures
    meas = run_measures(
        auto_measure_core=auto_measure_core,
        auto_measure_fc=auto_measure_fc,
        core_measures=core_measures,
        connectivity=connectivity,
        fc_results=fc_results,
        require_fc=require_fc,
        evidence_ok=evidence_ok,
        evidence_complete=evidence_complete,
        pre_ok=pre_ok,
        cog=cog,
        lock=lock,
        paths_for_q=paths_for_q,
        gap_reg=gap_reg,
        mission_id=mid,
        wire_trace=wire_trace,
    )

    # 09 forensic
    t0 = time.monotonic()
    fr = run_forensic(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        core_results=meas["core_results"],
        fc_map=meas["fc_map"],
        require_fc=require_fc,
        fc_results=fc_results,
        conn=meas["conn"],
        counters=counters,
        gap_reg=gap_reg,
        evidence_ok=evidence_ok,
        evidence_complete=evidence_complete,
        final_clean_reaudit_passed=final_clean_reaudit_passed,
        dag_passed=dag_passed,
    )
    stage_ms["forensic"] = _stage_ms(t0)

    # 10 checklist
    checklist_passed = checklist_passed_from_pre(
        pre_gate_result=pre_gate_result,
        require_checklist=require_checklist,
        env_prof=env_prof,
    )

    # 11 closure
    t0 = time.monotonic()
    closure = run_closure(
        checklist_passed=checklist_passed,
        forensic_pass=fr["forensic_pass"],
        evidence_ok=evidence_ok,
        evidence_complete=evidence_complete,
        ctr=fr["ctr"],
        gap_reg=gap_reg,
        wire_trace=wire_trace,
    )
    stage_ms["closure"] = _stage_ms(t0)
    stage_ms["total"] = _stage_ms(t_all)

    # 12 return
    return build_return(
        forensic_pass=fr["forensic_pass"],
        closure=closure,
        fc_all=meas["fc_all"],
        require_fc=require_fc,
        fc_results=fc_results,
        mid=mid,
        lock=lock,
        cog=cog,
        compiled=compiled,
        evidence=evidence,
        merged=merged,
        evidence_ok=evidence_ok,
        forensic=fr["forensic"],
        pre_gate_result=pre_gate_result,
        gap_reg=gap_reg,
        measures=meas["measures"],
        fc_map=meas["fc_map"],
        wire_trace=wire_trace,
        policy_dict=policy_dict,
        gw_hop=gw_hop,
    )
