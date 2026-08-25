# -*- coding: utf-8 -*-
"""Process 09 — Forensic enforcement state + decide."""
from __future__ import annotations

from typing import Any


def run_forensic(
    *,
    context_verified: bool,
    handoff_verified: bool,
    core_results: list,
    fc_map: dict[str, bool],
    require_fc: bool,
    fc_results: dict[str, bool] | None,
    conn: dict[str, bool],
    counters: dict[str, int] | None,
    gap_reg: Any,
    evidence_ok: bool,
    evidence_complete: bool,
    final_clean_reaudit_passed: bool,
    dag_passed: bool,
) -> dict[str, Any]:
    from extensions.wordflow.standards.forensic_core import (
        ForensicEnforcementState, ClosureCounters,
    )
    from extensions.wordflow.standards.verdict_authority import VerdictAuthority

    ctr_in = counters or {}
    ctr = ClosureCounters(
        gaps=int(ctr_in.get("gaps", 0)),
        blocking_gaps=int(ctr_in.get("blocking_gaps", 0)),
        broken_connections=int(ctr_in.get("broken_connections", 0)),
        unexplained_orphans=int(ctr_in.get("unexplained_orphans", 0)),
        unreachable_required_paths=int(ctr_in.get("unreachable_required_paths", 0)),
        unresolved_dependencies=int(ctr_in.get("unresolved_dependencies", 0)),
        unverified_paths=int(ctr_in.get("unverified_paths", 0)),
        unverified_requirements=int(ctr_in.get("unverified_requirements", 0)),
        unverified_claims=int(ctr_in.get("unverified_claims", 0)),
        pending_fixes=int(ctr_in.get("pending_fixes", 0)),
        new_gaps_after_fix=int(ctr_in.get("new_gaps_after_fix", 0)) + gap_reg.new_gaps_after_fix,
        unexpected_changes=int(ctr_in.get("unexpected_changes", 0)),
    )
    open_n = gap_reg.open_count()
    if open_n:
        ctr.gaps = max(ctr.gaps, open_n)
        ctr.blocking_gaps = max(ctr.blocking_gaps, open_n)

    state = ForensicEnforcementState(
        context_verified=context_verified,
        handoff_verified=handoff_verified,
        core_results=core_results,
        fc_results=fc_map,
        require_fc=bool(require_fc or fc_results),
        connectivity=conn,
        counters=ctr,
        evidence_complete=bool(evidence_complete and evidence_ok),
        final_clean_reaudit_passed=bool(final_clean_reaudit_passed),
        quality_dag_ok=bool(dag_passed),
        claim_used_as_pass=False,
    )
    authority = VerdictAuthority()
    forensic = authority.decide(state=state)
    return {"forensic": forensic, "ctr": ctr, "forensic_pass": forensic.get("verdict") == "PASS"}
