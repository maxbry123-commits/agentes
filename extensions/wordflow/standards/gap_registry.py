"""GapRegistry — OPEN→FIXED→VERIFIED→CLOSED; never OPEN→CLOSED."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
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
    status: str = "OPEN"
    evidence: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GapRegistry:
    def __init__(self):
        self._gaps: Dict[str, Gap] = {}

    def add(self, gap: Gap) -> None:
        if gap.status != "OPEN":
            raise ValueError("new gaps must start OPEN")
        self._gaps[gap.gap_id] = gap

    def transition(self, gap_id: str, new_status: str, evidence: str = "") -> Gap:
        g = self._gaps[gap_id]
        allowed = ALLOWED.get(g.status, set())
        if new_status not in allowed:
            raise ValueError(f"forbidden {g.status} → {new_status}")
        if new_status == "CLOSED" and g.status != "VERIFIED":
            raise ValueError("CLOSED only from VERIFIED")
        g.status = new_status
        if evidence:
            g.evidence = evidence
        return g

    def open_count(self) -> int:
        return sum(1 for g in self._gaps.values() if g.status in ("OPEN", "FIXED"))

    def blocking_open(self) -> List[Gap]:
        return [g for g in self._gaps.values() if g.status == "OPEN" and g.severity in ("P0", "BLOCK", "P1")]

    def to_list(self) -> List[Dict[str, Any]]:
        return [asdict(g) for g in self._gaps.values()]
