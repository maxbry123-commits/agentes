"""TestEffectivenessRunner + edge smoke (G-W2b)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any
from pathlib import Path

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
    r.add(
        "copy_first_import",
        lambda: __import__("extensions.wordflow.standards.copy_first", fromlist=["ExistingCodeScanner"]) is not None,
    )
    r.add(
        "verdict_import",
        lambda: __import__("extensions.wordflow.standards.verdict_authority", fromlist=["VerdictAuthority"]) is not None,
    )
    r.add(
        "wiring_import",
        lambda: __import__("extensions.wordflow.standards.wiring_graph", fromlist=["WiringGraph"]) is not None,
    )
    r.add(
        "forensic_contract_skip_not_pass",
        lambda: __import__("extensions.wordflow.standards.forensic_contract", fromlist=["ForensicCodeContract"]).ForensicCodeContract().skip_equals_pass is False,
    )
    # G-W2b edges
    r.add(
        "edge_empty_scanner_roots",
        lambda: len(__import__("extensions.wordflow.standards.copy_first", fromlist=["ExistingCodeScanner"]).ExistingCodeScanner([]).find_by_name("___none___")) == 0,
    )
    r.add(
        "edge_catalog_exists",
        lambda: (Path(__file__).resolve().parents[1] / "component_catalog.json").exists(),
    )
    r.add(
        "edge_connect_catalog_exists",
        lambda: (Path(__file__).resolve().parents[1] / "connect_catalog.json").exists(),
        required=False,
    )
    return r
