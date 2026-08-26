# -*- coding: utf-8 -*-
"""control_sheriff_bridge — D6. Wordflow → control-layer Sheriff. 0% LLM.

Tries real control-layer compile_plan + gate when importable.
Always supports duck-typed plan with C00 check (fail-closed).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .goal_lock import verify_lock_integrity
from .sheriff_adapter import gate_lock, state_from_band


def _ensure_control_layer_path() -> Path | None:
    """Add repo control-layer/ to sys.path if present relative to this file."""
    # extensions/wordflow/engine → parents[3] = repo root
    root = Path(__file__).resolve().parents[3]
    cl = root / "control-layer"
    if cl.is_dir():
        p = str(cl)
        if p not in sys.path:
            sys.path.insert(0, p)
        return cl
    return None


def try_compile_plan(input_data: str | dict[str, Any]) -> dict[str, Any]:
    """Call control-layer compile_plan if available."""
    _ensure_control_layer_path()
    try:
        from control.compiler import compile_plan  # type: ignore

        plan = compile_plan(input_data)
        d = plan.to_dict() if hasattr(plan, "to_dict") else {}
        return {"ok": True, "via": "control.compiler", "plan": d, "raw": plan}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "via": "unavailable", "error": str(exc)}


def try_control_gate(plan_obj: Any) -> dict[str, Any]:
    _ensure_control_layer_path()
    try:
        from sheriff.gate import gate  # type: ignore

        gr = gate(plan_obj)
        return {
            "ok": True,
            "via": "sheriff.gate",
            "passed": bool(gr.passed),
            "result": gr.to_dict() if hasattr(gr, "to_dict") else {},
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "via": "unavailable", "error": str(exc)}


def gate_c00(
    lock: dict[str, Any],
    *,
    contracts: list[str] | None = None,
    risk_score: int = 0,
    band: str = "",
    require_c00: bool = True,
    prefer_control_layer: bool = True,
    input_for_compile: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified gate: optional control-layer path + always C00 rule."""
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {
            "passed": False,
            "action": "DENY",
            "reason": "LOCK_FAIL",
            "detail": integ,
        }

    contracts = list(contracts or ["C00"])
    if require_c00 and "C00" not in contracts:
        return {
            "passed": False,
            "action": "DENY",
            "reason": "MISSING_C00",
            "contracts": contracts,
        }

    control_meta: dict[str, Any] = {"used": False}
    if prefer_control_layer and input_for_compile is not None:
        compiled = try_compile_plan(input_for_compile)
        if compiled.get("ok") and compiled.get("raw") is not None:
            g = try_control_gate(compiled["raw"])
            control_meta = {"used": True, "compile": compiled.get("via"), "gate": g}
            if g.get("ok"):
                # still enforce C00 on plan contracts if present
                plan_contracts = (compiled.get("plan") or {}).get("contracts") or []
                if require_c00 and "C00" not in plan_contracts:
                    return {
                        "passed": False,
                        "action": "DENY",
                        "reason": "CONTROL_PLAN_NO_C00",
                        "control": control_meta,
                    }
                return {
                    "passed": bool(g.get("passed")),
                    "action": "ALLOW" if g.get("passed") else "DENY",
                    "reason": "CONTROL_LAYER_GATE",
                    "control": control_meta,
                    "lock_id": lock.get("lock_id"),
                }

    # Fallback / primary Wordflow path
    base = gate_lock(lock, risk_score=risk_score, band=band)
    if require_c00 and "C00" not in contracts:
        base = {
            "passed": False,
            "action": "DENY",
            "reason": "MISSING_C00",
            "state": state_from_band(band, risk_score).value,
        }
    base["contracts"] = contracts
    base["control"] = control_meta
    base["source"] = "wordflow.control_sheriff_bridge"
    return base
