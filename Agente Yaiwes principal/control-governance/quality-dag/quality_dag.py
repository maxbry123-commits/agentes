"""QualityDAG — required gates cannot SKIP→PASS; fail-closed."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Set
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
class GateNode:
    name: str
    depends_on: List[str] = field(default_factory=list)
    required: bool = True

@dataclass
class QualityDAG:
    nodes: List[GateNode] = field(default_factory=list)
    handlers: Dict[str, Callable[[], GateResult]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.nodes:
            self.nodes = [
                GateNode("FORMAT"),
                GateNode("LINT", ["FORMAT"]),
                GateNode("TYPE", ["FORMAT"]),
                GateNode("STATIC", ["FORMAT"]),
                GateNode("SECURITY", ["FORMAT"]),
                GateNode("DEPS", ["FORMAT"]),
                GateNode("UNIT", ["LINT", "TYPE"]),
                GateNode("ARCH", ["STATIC", "DEPS"]),
                GateNode("INTEGRATION", ["UNIT"]),
                GateNode("CONTRACT", ["UNIT"]),
                GateNode("BUILD", ["ARCH", "INTEGRATION", "CONTRACT", "SECURITY"]),
                GateNode("AUDIT", ["BUILD"]),
            ]

    def register(self, name: str, handler: Callable[[], GateResult]) -> None:
        self.handlers[name] = handler

    def _ready(self, name: str, done: Set[str], results: Dict[str, GateResult]) -> bool:
        node = next(n for n in self.nodes if n.name == name)
        for dep in node.depends_on:
            if dep not in done:
                return False
            if results.get(dep) and results[dep].status == GateStatus.FAIL:
                return False
        return True

    def run(self, fail_closed: bool = True) -> List[GateResult]:
        pending = {n.name for n in self.nodes}
        done: Set[str] = set()
        results: Dict[str, GateResult] = {}
        ordered: List[GateResult] = []

        while pending:
            progressed = False
            for name in list(pending):
                if not self._ready(name, done, results):
                    continue
                node = next(n for n in self.nodes if n.name == name)
                handler = self.handlers.get(name)
                if handler is None:
                    status = GateStatus.FAIL if node.required else GateStatus.SKIP
                    detail = "required gate missing handler" if node.required else "no handler"
                    r = GateResult(name, status, detail)
                else:
                    r = handler()
                results[name] = r
                ordered.append(r)
                done.add(name)
                pending.discard(name)
                progressed = True
                if fail_closed and r.status == GateStatus.FAIL:
                    return ordered
            if not progressed:
                for name in list(pending):
                    ordered.append(GateResult(name, GateStatus.FAIL, "unmet dependencies or deadlock"))
                    pending.discard(name)
                break
        return ordered

    def passed(self, results: List[GateResult]) -> bool:
        return all(r.status != GateStatus.FAIL for r in results)
