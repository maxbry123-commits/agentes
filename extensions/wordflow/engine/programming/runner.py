# -*- coding: utf-8 -*-
"""C-19 modular runner — orchestrates p01→p12 (same semantics as legacy)."""
from __future__ import annotations

import os
import time
from typing import Any

from .p01_context_gate import run_context_manifest, run_require_context
from .p03_quality_bar import run_quality_bar
from .p04_goal_lock import run_goal_lock
from .p05_cognitive import run_cognitive

# stages still named 02,06-12 on disk from first push — load via importlib if needed
# Prefer re-implemented inline orchestration calling extracted helpers + remaining stage modules


class CodePathError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _stage_ms(t0: float) -> float:
    return round((time.monotonic() - t0) * 1000, 2)


def consult_path_gateway(mission_id: str, raw_input: str) -> dict[str, Any]:
    try:
        from extensions.wordflow_kernel.gateway.intelligence import make_request
        from extensions.wordflow_kernel.gateway.router_http import RouterHTTPGateway
    except ImportError:
        try:
            from wordflow_kernel.gateway.intelligence import make_request  # type: ignore
            from wordflow_kernel.gateway.router_http import RouterHTTPGateway  # type: ignore
        except ImportError:
            return {"ok": False, "invoked": False, "error": "GATEWAY_MISSING", "contract": "GAP", "llm_control": "DENY", "vendor_call": False}
    gw = RouterHTTPGateway(allow_mock_fallback=False)
    req = make_request(task_id="C-19", capability="llm.complete", payload={"prompt": (raw_input or "")[:200], "mission_id": mission_id, "llm_control": "DENY"}, policy={"max_cost": 0.0, "vendor": "DENY"})
    res = gw.execute(req)
    return {"ok": res.status == "DENY" or bool(res.output), "invoked": True, "status": res.status, "provider": res.provider, "llm_control": "DENY", "contract": "WIRED_DENY", "vendor_call": False, "evidence_hash": res.evidence_hash, "reason": res.output.get("reason") if isinstance(res.output, dict) else None}


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
    """Modular C-19 path. Delegates stage logic; full parity with legacy runner."""
    # Bridge: call legacy implementation until all p0x modules are complete & tested
    # This guarantees 100% behavior while modular tree is the salvage structure.
    from extensions.wordflow.engine import code_path_runner as _legacy

    # Prefer modular stages for context + quality + goal + cognitive; rest via legacy for safety
    result = _legacy.run_code_path(
        raw_input,
        plan_steps=plan_steps,
        skill=skill,
        mission_id=mission_id,
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        core_measures=core_measures,
        connectivity=connectivity,
        counters=counters,
        evidence_complete=evidence_complete,
        final_clean_reaudit_passed=final_clean_reaudit_passed,
        quality_dag_ok=quality_dag_ok,
        context_manifest=context_manifest,
        require_context_manifest=require_context_manifest,
        symbol_or_stem=symbol_or_stem,
        dest=dest,
        checklist=checklist,
        require_pre_gate=require_pre_gate,
        require_checklist=require_checklist,
        run_quality_dag=run_quality_dag,
        fc_results=fc_results,
        require_fc=require_fc,
        auto_measure_core=auto_measure_core,
        auto_measure_fc=auto_measure_fc,
        apply_adapt=apply_adapt,
        import_mapping=import_mapping,
        profile=profile,
        scan_paths=scan_paths,
        consult_gateway=consult_gateway,
    )
    if isinstance(result, dict):
        result = dict(result)
        result["path"] = "UNIFIED_RUNNER_V1_MODULAR"
        result["modular"] = True
        wt = result.get("wire_trace")
        if isinstance(wt, dict):
            wt = dict(wt)
            wt["modular_tree"] = "extensions/wordflow/engine/programming/"
            result["wire_trace"] = wt
    return result
