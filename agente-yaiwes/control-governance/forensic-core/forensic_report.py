"""Genera formato de salida FORENSIC CODE AUDIT obligatorio."""
from __future__ import annotations
from typing import Dict, Any
from .forensic_contract import ForensicCodeContract

def render_forensic_report(contract: ForensicCodeContract, verdict: str) -> str:
    c = contract
    p = c.passes
    core = c.core
    cl = c.closure

    def mark(ok: bool) -> str:
        return "✓" if ok else "✗"

    lines = [
        "FORENSIC CODE AUDIT v1.3",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"PASS 1 — STRUCTURE            [{mark(p.structure)}]",
        f"PASS 2 — CONNECTIVITY         [{mark(p.connectivity)}]",
        f"PASS 3 — BEHAVIOR             [{mark(p.behavior)}]",
        f"PASS 4 — FORENSIC CLOSURE     [{mark(p.forensic_closure)}]",
        "",
        f"ARCHITECTURE ↔ DOCS           [{mark(core.architecture)}]",
        f"CONNECTIVITY                  [{mark(core.connectivity)}]",
        f"REQ → CODE → TEST → EVIDENCE  [{mark(core.requirements and core.tests and core.evidence)}]",
        f"DEPENDENCIES / CONTRACTS      [{mark(core.dependencies and core.contracts)}]",
        f"BEHAVIOR / ERROR PATHS        [{mark(core.behavior and core.error_paths)}]",
        f"IMPACT / REGRESSION           [{mark(core.regression_impact)}]",
        f"EVIDENCE                      [{mark(core.evidence and c.evidence_complete)}]",
        "",
        f"GAPS: {cl.gaps}  BLOCKING: {cl.blocking_gaps}  BROKEN: {cl.broken_connections}",
        f"ORPHANS: {cl.unexplained_orphans}  UNREACHABLE: {cl.unreachable_required_paths}",
        f"UNRESOLVED_DEPS: {cl.unresolved_dependencies}  UNVERIFIED: {cl.unverified_claims}",
        f"PENDING: {cl.pending_fixes}  NEW_GAPS_AFTER_FIX: {cl.new_gaps_after_fix}",
        f"UNEXPECTED: {cl.unexpected_changes}",
        "",
        f"RESULT: {verdict}",
        "VerdictAuthority only. LLM claim is not PASS.",
    ]
    return "\n".join(lines)
