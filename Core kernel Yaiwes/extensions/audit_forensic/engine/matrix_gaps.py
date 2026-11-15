# -*- coding: utf-8 -*-
"""P3 Gaps matrix — A-AUD-05. Active-phase requirements not met. 0% LLM."""
from __future__ import annotations

from typing import Any


def run_gaps(
    coverage_rows: list[dict[str, Any]],
    *,
    phase: str | None = None,
    deferred_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    deferred_ids = deferred_ids or set()
    gaps: list[dict[str, Any]] = []

    for row in coverage_rows:
        rid = row.get("requirement_id")
        if not rid:
            continue
        if phase and row.get("phase") and row.get("phase") != phase:
            continue
        if rid in deferred_ids or row.get("status") == "DEFERRED":
            continue
        status = row.get("status")
        if status in ("PRESENT",):
            continue
        gaps.append(
            {
                "requirement_id": rid,
                "status": status,
                "critical": bool(row.get("critical")),
                "phase": row.get("phase") or "",
                "path_claim": row.get("path_claim"),
                "path_real": row.get("path_real"),
                "reason_code": (
                    "PHASE_GAP_CRITICAL"
                    if row.get("critical")
                    else "PHASE_GAP"
                ),
            }
        )
    return gaps


def gaps_summary(gaps: list[dict[str, Any]]) -> dict[str, Any]:
    critical = [g for g in gaps if g.get("critical")]
    return {
        "total": len(gaps),
        "critical_count": len(critical),
        "critical_ids": [g["requirement_id"] for g in critical],
        "all_ids": [g["requirement_id"] for g in gaps],
        "has_critical_gap": len(critical) > 0,
    }
