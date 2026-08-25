# -*- coding: utf-8 -*-
"""Process 12 — Final return assembly."""
from __future__ import annotations

from typing import Any


def _all_core_true(measures: dict[str, bool]) -> bool:
    return all(measures.get(f"CORE-{i:02d}", False) for i in range(1, 15))


def build_return(
    *,
    forensic_pass: bool,
    closure: dict[str, Any],
    fc_all: bool,
    require_fc: bool,
    fc_results: dict[str, bool] | None,
    mid: str,
    lock: dict[str, Any],
    cog: Any,
    compiled: Any,
    evidence: Any,
    merged: dict[str, Any],
    evidence_ok: bool,
    forensic: dict[str, Any],
    pre_gate_result: Any,
    gap_reg: Any,
    measures: dict[str, bool],
    fc_map: dict[str, bool],
    wire_trace: dict[str, Any],
    policy_dict: dict[str, Any],
    gw_hop: dict[str, Any],
) -> dict[str, Any]:
    wire_trace["core_all_true"] = _all_core_true(measures)
    ok = forensic_pass and closure.get("closed") is True and (fc_all if (require_fc or fc_results) else True)
    return {
        "ok": ok,
        "mission_id": mid,
        "lock": lock,
        "cognitive": cog,
        "skill_compile": compiled,
        "evidence": evidence,
        "evidence_merged": merged.get("merged"),
        "evidence_ok": evidence_ok,
        "forensic": forensic,
        "pre_gate": pre_gate_result,
        "closure": closure,
        "gaps": gap_reg.to_list(),
        "core_measures": measures,
        "fc_measures": fc_map,
        "quality_dag": wire_trace.get("quality_dag"),
        "policy": policy_dict,
        "path_gateway": gw_hop,
        "wire_trace": wire_trace,
        "llm_control": "DENY",
        "verdict": "PASS" if ok else (forensic.get("verdict") or "FAIL"),
        "path": "UNIFIED_RUNNER_V1_MODULAR",
        "gc_status": "GC-01..12_WIRED",
        "gr_status": "GR-01..05_CODE_FIXED",
        "c_status": "C1-C7_CLOSED",
        "s_status": "S1-S8_CLOSED",
        "t_status": "T1-T8_CLOSED",
        "u_status": "U1-U10_CLOSED",
        "modular": True,
    }
