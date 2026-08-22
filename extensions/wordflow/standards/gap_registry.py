"""GapRegistry completo — campos de contrato + OPEN→FIXED→VERIFIED→CLOSED.

The registry is persistent by default so a process restart cannot silently erase
open/fixed/verified gaps.  Set WORDFLOW_GAP_REGISTRY_PATH to choose the store.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

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
    def __init__(self, path: str | None = None):
        configured = path or os.environ.get("WORDFLOW_GAP_REGISTRY_PATH")
        self.path = Path(configured) if configured else Path(".wordflow/gap_registry.json")
        self._gaps: Dict[str, Gap] = {}
        self.new_gaps_after_fix: int = 0
        self._load()

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return
        for item in payload.get("gaps", []):
            try:
                gap = Gap(**item)
            except TypeError:
                continue
            self._gaps[gap.gap_id] = gap
        self.new_gaps_after_fix = int(payload.get("new_gaps_after_fix", 0))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "new_gaps_after_fix": self.new_gaps_after_fix,
            "gaps": [asdict(g) for g in self._gaps.values()],
        }
        fd, tmp_name = tempfile.mkstemp(prefix="gap-registry-", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def add(self, gap: Gap) -> None:
        if gap.status != "OPEN":
            raise ValueError("new gaps must start OPEN")
        self._gaps[gap.gap_id] = gap
        self._save()

    def transition(self, gap_id: str, new_status: str, evidence: str = "", revision: str = "") -> Gap:
        g = self._gaps[gap_id]
        if new_status not in ALLOWED.get(g.status, set()):
            raise ValueError(f"forbidden {g.status} → {new_status}")
        if new_status == "CLOSED" and g.status != "VERIFIED":
            raise ValueError("CLOSED only from VERIFIED")
        g.status = new_status
        if evidence:
            g.evidence = evidence
        if new_status == "FIXED" and revision:
            g.fixed_revision = revision
        if new_status == "VERIFIED" and revision:
            g.verified_revision = revision
        self._save()
        return g

    def note_new_gap_after_fix(self, gap: Gap) -> None:
        self.add(gap)
        self.new_gaps_after_fix += 1
        self._save()

    def open_count(self) -> int:
        return sum(1 for g in self._gaps.values() if g.status in ("OPEN", "FIXED"))

    def to_list(self) -> List[Dict[str, Any]]:
        return [asdict(g) for g in self._gaps.values()]
