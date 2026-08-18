"""GapRegistry completo — campos de contrato + OPEN→FIXED→VERIFIED→CLOSED."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime, timezone

ALLOWED = {
    "OPEN": {"FIXED"},
    "FIXED": {"VERIFIED", "OPEN"},
    "VERIFIED": {"CLOSED", "OPEN"},
    "CLOSED": set(),
}

@dataclass
class Gap:
    gap_id: str
    task_id: str
    mission_id: str
    rule_id: str
    severity: str
    description: str
    location: str = ""
    root_cause: str = ""
    required_fix: str = ""
    implemented_fix: str = ""
    verification: str = ""
    evidence: str = ""
    status: str = "OPEN"
    created_revision: str = ""
    fixed_revision: str = ""
    verified_revision: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GapRegistry:
    def __init__(self):
        self._gaps: Dict[str, Gap] = {}
        self.new_gaps_after_fix: int = 0

    def add(self, gap: Gap) -> None:
        if gap.status != "OPEN":
            raise ValueError("new gaps must start OPEN")
        self._gaps[gap.gap_id] = gap

    def transition(self, gap_id: str, new_status: str, evidence: str = "", revision: str = "") -> Gap:
        g = self._gaps[gap_id]
        if new_status not in ALLOWED.get(g.status, set()):
            raise ValueError(f"forbidden {g.status} → {new_status}")
        if new_status == "CLOSED" and g.status != "VERIFIED":
            raise ValueError("CLOSED only from VERIFIED")
        prev = g.status
        g.status = new_status
        if evidence:
            g.evidence = evidence
        if new_status == "FIXED" and revision:
            g.fixed_revision = revision
        if new_status == "VERIFIED" and revision:
            g.verified_revision = revision
        return g

    def note_new_gap_after_fix(self, gap: Gap) -> None:
        self.add(gap)
        self.new_gaps_after_fix += 1

    def open_count(self) -> int:
        return sum(1 for g in self._gaps.values() if g.status in ("OPEN", "FIXED"))

    def to_list(self) -> List[Dict[str, Any]]:
        return [asdict(g) for g in self._gaps.values()]
