"""ClosureEngine — árbitro final determinista."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .checklist_sheriff import SheriffVerdict
from .gap_registry import GapRegistry

@dataclass
class ClosureInput:
    checklist_passed: bool
    forensic_passed: bool
    evidence_ok: bool
    new_gaps_after_fix: int = 0
    unexpected_changes: int = 0
    broken_connections: int = 0
    gap_registry: Optional[GapRegistry] = None

class ClosureEngine:
    def decide(self, inp: ClosureInput) -> Dict[str, Any]:
        reasons = []
        if not inp.checklist_passed:
            reasons.append("checklist_failed")
        if not inp.forensic_passed:
            reasons.append("forensic_failed")
        if not inp.evidence_ok:
            reasons.append("evidence_failed")
        if inp.new_gaps_after_fix != 0:
            reasons.append("new_gaps_after_fix")
        if inp.unexpected_changes != 0:
            reasons.append("unexpected_changes")
        if inp.broken_connections != 0:
            reasons.append("broken_connections")
        if inp.gap_registry and inp.gap_registry.open_count() > 0:
            reasons.append("gaps_open")
        closed = len(reasons) == 0
        return {"closed": closed, "verdict": "CLOSED" if closed else "OPEN", "reasons": reasons}
