# -*- coding: utf-8 -*-
"""Process 08 — CORE auto-measure + FC auto-measure."""
from __future__ import annotations

from typing import Any


def run_measures(
    *,
    auto_measure_core: bool,
    auto_measure_fc: bool,
    core_measures: dict[str, bool] | None,
    connectivity: dict[str, bool] | None,
    fc_results: dict[str, bool] | None,
    require_fc: bool,
    evidence_ok: bool,
    evidence_complete: bool,
    pre_ok: bool,
    cog: Any,
    lock: dict[str, Any],
    paths_for_q: list[str],
    gap_reg: Any,
    mission_id: str,
    wire_trace: dict[str, Any],
) -> dict[str, Any]:
    from extensions.wordflow.standards.forensic_core import (
        CoreCheckResult, CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS,
    )
    from extensions.wordflow.standards.core_auto_measure import auto_measure_core as _auto_core
    from extensions.wordflow.standards.fc_auto_measure import auto_measure_fc as _auto_fc
    from extensions.wordflow.standards.gap_registry import Gap

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

    core_results = [
        CoreCheckResult(
            cid,
            bool(measures.get(cid, False)),
            evidence=str((wire_trace.get("auto_measure") or {}).get("evidence", {}).get(cid, "")),
        )
        for cid in CORE_IDS
    ]

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
        gap_reg.add(Gap(
            gap_id="GC-FC-001", task_id="C-19", mission_id=mission_id,
            rule_id="FC_REQUIRED", severity="blocking",
            description="FC not all True", location="fc",
        ))

    return {
        "measures": measures,
        "core_results": core_results,
        "fc_map": fc_map,
        "fc_all": fc_all,
        "conn": conn,
    }
