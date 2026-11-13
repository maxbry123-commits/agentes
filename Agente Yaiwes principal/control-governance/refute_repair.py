# -*- coding: utf-8 -*-
"""Refute L1-L3 + Repair R1-R6 — A-WF-03. 0% LLM."""
from __future__ import annotations

from typing import Any

REFUTE_CODES = {
    "L1_MISSING_FIELD": "L1",
    "L1_INVALID_SCHEMA": "L1",
    "L1_EMPTY_TEXT": "L1",
    "L2_NO_OBJECTIVE": "L2",
    "L2_NO_SUCCESS_CRITERIA": "L2",
    "L2_CONFLICTING_HINTS": "L2",
    "L3_MVP_FORBIDDEN": "L3",
    "L3_SECRET_IN_INPUT": "L3",
    "L3_PHASE_UNKNOWN": "L3",
    "L3_BUDGET_EXCEEDED": "L3",
}

REPAIR_ACTIONS = {
    "R1_FILL_DEFAULTS": {"cap": 3, "layer": "L1"},
    "R2_ASK_DIRECTOR": {"cap": 2, "layer": "L2"},
    "R3_SPLIT_BLOCK": {"cap": 2, "layer": "L2"},
    "R4_DOWNGRADE_PRIORITY": {"cap": 1, "layer": "L3"},
    "R5_DEFER_PHASE": {"cap": 2, "layer": "L3"},
    "R6_REJECT_BLOCK": {"cap": 1, "layer": "L3"},
}


def refute_block(
    block: dict[str, Any],
    goals_in: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    flags = block.get("flags") or {}
    constraints = block.get("constraints") or {}
    goals_in = goals_in or {}

    if not block.get("block_id"):
        findings.append({"code": "L1_MISSING_FIELD", "layer": "L1", "detail": "block_id"})
    if not (block.get("raw_text") or "").strip():
        findings.append({"code": "L1_EMPTY_TEXT", "layer": "L1", "detail": "raw_text"})
    if block.get("schema_version") != "1.0":
        findings.append({"code": "L1_INVALID_SCHEMA", "layer": "L1", "detail": "schema"})

    resolved = (goals_in or {}).get("resolved") or {}
    obj = (resolved.get("GIN-01") or {}).get("value")
    if not obj or (isinstance(obj, str) and len(obj.strip()) < 5):
        findings.append({"code": "L2_NO_OBJECTIVE", "layer": "L2", "detail": "GIN-01"})
    success = (resolved.get("GIN-10") or {}).get("value")
    if not success and block.get("quality_bar") == "never_MVP":
        findings.append(
            {"code": "L2_NO_SUCCESS_CRITERIA", "layer": "L2", "detail": "never_MVP requires criteria"}
        )
    hints = block.get("goals_hint") or []
    if len(hints) != len(set(hints)):
        findings.append(
            {"code": "L2_CONFLICTING_HINTS", "layer": "L2", "detail": "duplicate hints"}
        )

    if block.get("quality_bar") == "draft" and flags.get("never_mvp"):
        findings.append({"code": "L3_MVP_FORBIDDEN", "layer": "L3", "detail": "conflict"})
    meta = block.get("meta") or {}
    if any("token" in str(k).lower() for k in meta):
        findings.append({"code": "L3_SECRET_IN_INPUT", "layer": "L3", "detail": "meta"})
    phase = (resolved.get("GIN-09") or {}).get("value")
    if block.get("source_type") != "system" and phase is None and not hints:
        findings.append({"code": "L3_PHASE_UNKNOWN", "layer": "L3", "detail": "no phase"})
    loc_limit = constraints.get("loc_limit") or (
        (resolved.get("GIN-11") or {}).get("value") or {}
    ).get("loc_limit")
    if loc_limit is not None and int(loc_limit) > 300:
        findings.append(
            {"code": "L3_BUDGET_EXCEEDED", "layer": "L3", "detail": f"loc={loc_limit}"}
        )

    layers = {f["layer"] for f in findings}
    worst = None
    for L in ("L3", "L2", "L1"):
        if L in layers:
            worst = L
            break

    return {
        "findings": findings,
        "count": len(findings),
        "worst_layer": worst,
        "pass": len(findings) == 0,
        "codes": [f["code"] for f in findings],
    }


def propose_repairs(
    refute: dict[str, Any],
    block: dict[str, Any],
    *,
    applied_counts: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    applied_counts = dict(applied_counts or {})
    proposals: list[dict[str, Any]] = []
    codes = set(refute.get("codes") or [])

    def _can(action: str) -> bool:
        meta = REPAIR_ACTIONS[action]
        return applied_counts.get(action, 0) < meta["cap"]

    if codes & {"L1_MISSING_FIELD", "L1_INVALID_SCHEMA", "L1_EMPTY_TEXT"}:
        if _can("R1_FILL_DEFAULTS"):
            proposals.append(
                {"action": "R1_FILL_DEFAULTS", "reason": "structural fix", "auto": True}
            )
        if _can("R6_REJECT_BLOCK") and "L1_EMPTY_TEXT" in codes:
            proposals.append(
                {"action": "R6_REJECT_BLOCK", "reason": "empty input", "auto": False}
            )

    if codes & {"L2_NO_OBJECTIVE", "L2_NO_SUCCESS_CRITERIA", "L2_CONFLICTING_HINTS"}:
        if _can("R2_ASK_DIRECTOR"):
            proposals.append(
                {"action": "R2_ASK_DIRECTOR", "reason": "need clarification", "auto": False}
            )
        if _can("R3_SPLIT_BLOCK") and "L2_CONFLICTING_HINTS" in codes:
            proposals.append(
                {"action": "R3_SPLIT_BLOCK", "reason": "conflicting goals", "auto": False}
            )

    if codes & {"L3_MVP_FORBIDDEN", "L3_SECRET_IN_INPUT"}:
        if _can("R6_REJECT_BLOCK"):
            proposals.append(
                {"action": "R6_REJECT_BLOCK", "reason": "policy violation", "auto": True}
            )
    if "L3_PHASE_UNKNOWN" in codes and _can("R5_DEFER_PHASE"):
        proposals.append(
            {"action": "R5_DEFER_PHASE", "reason": "phase unclear", "auto": False}
        )
    if "L3_BUDGET_EXCEEDED" in codes and _can("R4_DOWNGRADE_PRIORITY"):
        proposals.append(
            {
                "action": "R4_DOWNGRADE_PRIORITY",
                "reason": "LOC budget exceeded",
                "auto": True,
                "from": block.get("priority"),
                "to": "P3",
            }
        )

    return proposals


def apply_auto_repairs(
    block: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    new_block = dict(block)
    applied: list[str] = []
    for p in proposals:
        if not p.get("auto"):
            continue
        action = p["action"]
        if action == "R1_FILL_DEFAULTS":
            new_block.setdefault("priority", "P1")
            new_block.setdefault("goals_hint", [])
            new_block.setdefault("constraints", {})
            applied.append(action)
        elif action == "R4_DOWNGRADE_PRIORITY":
            new_block["priority"] = p.get("to") or "P3"
            applied.append(action)
        elif action == "R6_REJECT_BLOCK":
            new_block["flags"] = dict(new_block.get("flags") or {})
            new_block["flags"]["rejected"] = True
            applied.append(action)
    return new_block, applied
