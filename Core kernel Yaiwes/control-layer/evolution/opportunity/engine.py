"""Opportunity Engine · gaps de capability."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

@dataclass
class Opportunity:
    id: str
    kind: str
    capability_needed: str
    reason: str
    suggested_identity: str = ""
    suggested_source_type: str = "agent"
    priority: int = 50
    meta: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)

DEFAULT_EXPECTED = {"code.generate", "code.analyze", "code.review", "git.diff", "git.commit", "browser.navigate", "browser.capture", "workflow.execute", "test.run"}

class OpportunityEngine:
    def __init__(self):
        self.history = []
        self._seq = 0
    def scan_registry(self, registered_caps: Iterable[str], expected=None, task_hints=None):
        registered = set(registered_caps)
        expected = set(expected or DEFAULT_EXPECTED)
        covered = set()
        for c in registered:
            covered.add(c)
            parts = c.split(".")
            if len(parts) >= 2: covered.add(".".join(parts[-2:])); covered.add(parts[-1])
        opps = []
        for need in sorted(expected):
            if need in covered or any(need in c or c.endswith(need) for c in registered): continue
            self._seq += 1
            opp = Opportunity(f"OPP-{self._seq:04d}", "missing_capability", need, f"registry_missing:{need}", need.replace(".", "_"), "agent" if need.startswith("code") else "software", 80 if need.startswith("code") else 60)
            opps.append(opp); self.history.append(opp)
        for hint in task_hints or []:
            low = hint.lower()
            if any(k in low for k in ("browser", "web", "navigate")) and not any("browser" in c for c in registered):
                self._seq += 1
                opp = Opportunity(f"OPP-{self._seq:04d}", "research_hint", "browser.navigate", f"task_hint:{hint[:80]}", "browser_runtime", "software", 70)
                opps.append(opp); self.history.append(opp)
        return opps
