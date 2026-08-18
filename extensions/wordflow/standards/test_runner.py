"""TestEffectivenessRunner mínimo — post-verify (G-W2)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional

@dataclass
class TestCase:
    name: str
    fn: Callable[[], bool]
    required: bool = True

@dataclass
class TestRunResult:
    passed: bool
    results: List[Dict[str, Any]] = field(default_factory=list)

class TestEffectivenessRunner:
    def __init__(self):
        self.cases: List[TestCase] = []

    def add(self, name: str, fn: Callable[[], bool], required: bool = True) -> None:
        self.cases.append(TestCase(name, fn, required))

    def run(self) -> TestRunResult:
        results = []
        ok = True
        for c in self.cases:
            try:
                passed = bool(c.fn())
            except Exception as exc:  # noqa: BLE001
                passed = False
                results.append({"name": c.name, "passed": False, "error": str(exc), "required": c.required})
                if c.required:
                    ok = False
                continue
            results.append({"name": c.name, "passed": passed, "required": c.required})
            if c.required and not passed:
                ok = False
        return TestRunResult(passed=ok, results=results)


def default_smoke_runner() -> TestEffectivenessRunner:
    r = TestEffectivenessRunner()
    r.add("truth", lambda: True)
    r.add("copy_first_import", lambda: __import__("extensions.wordflow.standards.copy_first", fromlist=["ExistingCodeScanner"]) is not None)
    r.add("verdict_import", lambda: __import__("extensions.wordflow.standards.verdict_authority", fromlist=["VerdictAuthority"]) is not None)
    return r
