"""Ledger EV-####."""
from __future__ import annotations
import json, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class LedgerEntry:
    mutation_id: str
    plugin_id: str
    source_path: str
    package_path: str
    strategy: str
    timestamp: float
    reversible: bool = True
    rolled_back: bool = False
    meta: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)

class EvolutionLedger:
    def __init__(self, path="evolution/ledger.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0
    def next_id(self):
        self._seq += 1
        return f"EV-{int(time.time())}-{self._seq:04d}"
    def append(self, entry: LedgerEntry):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    def list_entries(self):
        if not self.path.exists(): return []
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
    def mark_rollback(self, mutation_id):
        entries = self.list_entries()
        found = False
        for e in entries:
            if e.get("mutation_id") == mutation_id:
                e["rolled_back"] = True; found = True
        if found:
            with self.path.open("w", encoding="utf-8") as f:
                for e in entries: f.write(json.dumps(e)+"\n")
        return found
