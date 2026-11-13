"""W07-W08 tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.harness import UniversalHarness
from agents.registry import AgentRegistry
from input.gateway import InputGateway
from input.classifier import InputKind


def test_registry_capability():
    r = AgentRegistry()
    r.register({"id": "opencode", "capabilities": ["code_gen", "repair"], "group": "backend", "priority": 10})
    r.register({"id": "cline", "capabilities": ["code_gen"], "group": "frontend", "priority": 20})
    got = r.resolve("code_gen", group="backend")
    assert got and got[0].id == "opencode"


def test_harness_cancel():
    h = UniversalHarness("x")
    h.prepare({"goal": "t"})
    h.cancel()
    res = h.execute({"a": 1})
    assert res.ok is False


def test_gateway_new_task_none_mission():
    g = InputGateway()
    q = g.receive("nuevo proyecto de pagos", mission_id="m9")
    assert q.kind == InputKind.NEW_TASK
    assert q.mission_id is None


if __name__ == "__main__":
    test_registry_capability()
    test_harness_cancel()
    test_gateway_new_task_none_mission()
    print("W07-W08 OK")
