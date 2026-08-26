# -*- coding: utf-8 -*-
"""Sentinel gate — A-WF-04. Schema + quality_bar. 0% LLM."""
from __future__ import annotations

from typing import Any

from .input_normalizer import InputBlockError, normalize_input_block
from .refute_repair import refute_block


def run_sentinel(
    raw: dict[str, Any] | None,
    *,
    goals_in: dict[str, Any] | None = None,
    strict_never_mvp: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    reasons: list[str] = []

    try:
        block = normalize_input_block(raw)
        checks.append({"name": "schema", "status": "PASS"})
    except InputBlockError as e:
        checks.append(
            {"name": "schema", "status": "FAIL", "reason_code": e.reason_code}
        )
        return {
            "verdict": "FAIL",
            "checks": checks,
            "reason_codes": [e.reason_code],
            "block": None,
            "refute": None,
        }

    qb = block.get("quality_bar")
    checks.append({"name": "quality_bar", "status": "PASS", "value": qb})

    if strict_never_mvp and qb == "never_MVP":
        constraints = block.get("constraints") or {}
        if not constraints.get("success_criteria"):
            checks.append(
                {
                    "name": "never_mvp_criteria",
                    "status": "FAIL",
                    "reason_code": "L2_NO_SUCCESS_CRITERIA",
                }
            )
            reasons.append("L2_NO_SUCCESS_CRITERIA")
        else:
            checks.append({"name": "never_mvp_criteria", "status": "PASS"})

        loc = constraints.get("loc_limit")
        if loc is not None and int(loc) > 300:
            checks.append(
                {
                    "name": "never_mvp_loc",
                    "status": "FAIL",
                    "reason_code": "L3_BUDGET_EXCEEDED",
                }
            )
            reasons.append("L3_BUDGET_EXCEEDED")
        else:
            checks.append({"name": "never_mvp_loc", "status": "PASS"})

    refute = refute_block(block, goals_in)
    if not refute["pass"]:
        hard = refute["worst_layer"] in ("L1", "L3") or qb == "never_MVP"
        if hard:
            for code in refute["codes"]:
                if code not in reasons:
                    reasons.append(code)
            checks.append(
                {
                    "name": "refute",
                    "status": "FAIL",
                    "worst_layer": refute["worst_layer"],
                    "codes": refute["codes"],
                }
            )
        else:
            checks.append(
                {
                    "name": "refute",
                    "status": "PASS",
                    "note": "L2 soft under standard/draft",
                    "codes": refute["codes"],
                }
            )
    else:
        checks.append({"name": "refute", "status": "PASS"})

    if (block.get("flags") or {}).get("rejected"):
        checks.append(
            {"name": "rejected_flag", "status": "FAIL", "reason_code": "R6_REJECT_BLOCK"}
        )
        reasons.append("R6_REJECT_BLOCK")

    verdict = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    return {
        "verdict": verdict,
        "checks": checks,
        "reason_codes": reasons,
        "block": block,
        "refute": refute,
        "block_id": block.get("block_id"),
        "block_hash": block.get("block_hash"),
    }
