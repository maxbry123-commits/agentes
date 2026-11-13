# -*- coding: utf-8 -*-
"""Verdict engine — A-AUD-06. 3 capas + reason_codes. 0% LLM."""
from __future__ import annotations

from typing import Any

VERDICTS = frozenset({"CONFIRMADO", "PARCIAL", "REFUTADO"})


def _collect_reason_codes(
    coverage_summary: dict[str, Any],
    literal_summary: dict[str, Any],
    contradiction_summary: dict[str, Any],
    gaps_summary: dict[str, Any],
    packet_flags: dict[str, Any] | None = None,
) -> list[str]:
    codes: list[str] = []
    packet_flags = packet_flags or {}

    if packet_flags.get("ci_missing"):
        codes.append("CI_MISSING")

    for rid in coverage_summary.get("critical_missing") or []:
        codes.append("PHASE_GAP_CRITICAL")

    for fail in literal_summary.get("fails") or []:
        rc = fail.get("reason_code")
        if rc:
            codes.append(rc)

    for fail in contradiction_summary.get("fails") or []:
        rc = fail.get("reason_code")
        if rc:
            codes.append(rc)

    if gaps_summary.get("has_critical_gap"):
        codes.append("PHASE_GAP_CRITICAL")

    seen: set[str] = set()
    out: list[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def decide_verdict(
    *,
    coverage_summary: dict[str, Any],
    literal_summary: dict[str, Any],
    contradiction_summary: dict[str, Any],
    gaps_summary: dict[str, Any],
    packet_flags: dict[str, Any] | None = None,
    packet_ok: bool = True,
) -> dict[str, Any]:
    packet_flags = packet_flags or {}
    reasons = _collect_reason_codes(
        coverage_summary,
        literal_summary,
        contradiction_summary,
        gaps_summary,
        packet_flags,
    )

    refutado = False
    parcial = False

    if not packet_ok:
        refutado = True
        if "INVALID_PACKET_SCHEMA" not in reasons:
            reasons.insert(0, "INVALID_PACKET_SCHEMA")

    if coverage_summary.get("critical_missing"):
        refutado = True
    if gaps_summary.get("has_critical_gap"):
        refutado = True
    if contradiction_summary.get("has_critical_fail"):
        refutado = True

    hard_literal = {
        "PATH_NOT_IN_REPO",
        "CI_FAILED",
        "CI_MISSING",
        "BLOB_SHA_MISMATCH",
        "CI_HEAD_MISMATCH",
    }
    for fail in literal_summary.get("fails") or []:
        if fail.get("reason_code") in hard_literal:
            refutado = True

    cov_counts = coverage_summary.get("counts") or {}
    if cov_counts.get("NO_VERIFICADO", 0) > 0:
        parcial = True
    if (gaps_summary.get("total") or 0) > 0 and not gaps_summary.get("has_critical_gap"):
        parcial = True
    lit_counts = literal_summary.get("counts") or {}
    if lit_counts.get("NO_VERIFICADO", 0) > 0:
        parcial = True
    if packet_flags.get("ci_missing"):
        parcial = True

    if refutado:
        verdict = "REFUTADO"
    elif parcial:
        verdict = "PARCIAL"
    else:
        verdict = "CONFIRMADO"

    capa1 = {
        "veredicto": verdict,
        "reason_codes": reasons,
        "completitud_hint": _completitud(
            coverage_summary, gaps_summary, contradiction_summary
        ),
    }
    capa2 = {
        "coverage": coverage_summary,
        "literal_fails": literal_summary.get("fails") or [],
        "contradiction_fails": contradiction_summary.get("fails") or [],
        "gaps": {
            "total": gaps_summary.get("total"),
            "critical_ids": gaps_summary.get("critical_ids") or [],
        },
    }
    capa3 = {
        "counts_coverage": cov_counts,
        "counts_literal": lit_counts,
        "contradiction_total": contradiction_summary.get("total"),
        "packet_flags": packet_flags,
    }
    return {
        "veredicto": verdict,
        "reason_codes": reasons,
        "capa1": capa1,
        "capa2": capa2,
        "capa3": capa3,
    }


def _completitud(
    coverage_summary: dict[str, Any],
    gaps_summary: dict[str, Any],
    contradiction_summary: dict[str, Any],
) -> int:
    total = coverage_summary.get("total") or 0
    if total == 0:
        return 0
    present = (coverage_summary.get("counts") or {}).get("PRESENT", 0)
    base = int(100 * present / total)
    if gaps_summary.get("has_critical_gap"):
        base = min(base, 50)
    if contradiction_summary.get("has_critical_fail"):
        base = min(base, 40)
    return max(0, min(100, base))
