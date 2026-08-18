"""G-W13 — medición simple de scope/requirements para post_verify."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Dict, Any

@dataclass
class ScopeMeasure:
    expected_paths: List[str]
    actual_paths: List[str]

    def unexpected(self) -> List[str]:
        exp = set(self.expected_paths)
        return [p for p in self.actual_paths if p not in exp]

    def missing(self) -> List[str]:
        act = set(self.actual_paths)
        return [p for p in self.expected_paths if p not in act]

    def ok(self) -> bool:
        return len(self.unexpected()) == 0


def measure_requirements(declared: List[str], satisfied: List[str]) -> Dict[str, Any]:
    ds, ss = set(declared), set(satisfied)
    return {
        "declared": list(ds),
        "satisfied": list(ss),
        "missing": list(ds - ss),
        "extra": list(ss - ds),
        "ok": ds <= ss,
    }
