# -*- coding: utf-8 -*-
"""Process 11 — ClosureEngine."""
from __future__ import annotations

from typing import Any


def run_closure(
    *,
    checklist_passed: bool,
    forensic_pass: bool,
    evidence_ok: bool,
    evidence_complete: bool,
    ctr: Any,
    gap_reg: Any,
    wire_trace: dict[str, Any],
) -> dict[str, Any]:
    from extensions.wordflow.standards.closure_engine import ClosureEngine, ClosureInput

    closure = ClosureEngine().decide(ClosureInput(
        checklist_passed=checklist_passed,
        forensic_passed=forensic_pass,
        evidence_ok=bool(evidence_ok and evidence_complete),
        new_gaps_after_fix=ctr.new_gaps_after_fix,
        unexpected_changes=ctr.unexpected_changes,
        broken_connections=ctr.broken_connections,
        gap_registry=gap_reg,
    ))
    wire_trace["closure_engine"] = closure
    wire_trace["gap_registry"] = gap_reg.to_list()
    return closure
