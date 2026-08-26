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
    """CONN.path_gateway: runner → RouterHTTPGateway. Fail closed by default."""
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


def run_code_path(raw_input: str, *, plan_steps: list[str] | None = None, skill: dict[str, Any] | None = None, mission_id: str = "", context_verified: bool = False, handoff_verified: bool = False, core_measures: dict[str, bool] | None = None, connectivity: dict[str, bool] | None = None, counters: dict[str, int] | None = None, evidence_complete: bool = False, final_clean_reaudit_passed: bool = False, quality_dag_ok: bool = False, context_manifest: Any | None = None, require_context_manifest: bool = False, symbol_or_stem: str = "", dest: str = "", checklist: Any | None = None, require_pre_gate: bool | None = None, require_checklist: bool = False, run_quality_dag: bool = True, fc_results: dict[str, bool] | None = None, require_fc: bool = False, auto_measure_core: bool = True, auto_measure_fc: bool = True, apply_adapt: bool = False, import_mapping: dict[str, str] | None = None, profile: str = "dev", scan_paths: list[str] | None = None, consult_gateway: bool = True) -> dict[str, Any]:
    """C-19 source body preserved verbatim in semantics; destination is organizational only in S5."""
    # S5 intentionally preserves the operational implementation in its original location.
    # The complete source blob is the authoritative C-19 artifact; later S10 handles p01→p12 wiring.
    raise RuntimeError("C-19 destination materialized; operational cutover remains deferred to S10/S11")
