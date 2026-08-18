"""QualityDAG — pipeline de gates (deterministic-first)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any, Optional
from enum import Enum

class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"

@dataclass
class GateResult:
    name: str
    status: GateStatus
    detail: str = ""

@dataclass
class QualityDAG:
    """FORMAT→…→AUDIT. FAIL_CLOSED en P0."""
    gates: List[str] = field(default_factory=lambda: [
        "FORMAT", "LINT", "TYPE", "STATIC", "UNIT", "INTEGRATION",
        "CONTRACT", "SECURITY", "DEPS", "ARCH", "BUILD", "AUDIT",
    ])
    handlers: Dict[str, Callable[[], GateResult]] = field(default_factory=dict)

    def register(self, name: str, handler: Callable[[], GateResult]) -> None:
        self.handlers[name] = handler

    def run(self, fail_closed: bool = True) -> List[GateResult]:
        results: List[GateResult] = []
        for name in self.gates:
            handler = self.handlers.get(name)
            if handler is None:
                results.append(GateResult(name, GateStatus.SKIP, "no handler"))
                continue
            r = handler()
            results.append(r)
            if fail_closed and r.status == GateStatus.FAIL:
                break
        return results

    def passed(self, results: List[GateResult]) -> bool:
        return all(r.status != GateStatus.FAIL for r in results)
