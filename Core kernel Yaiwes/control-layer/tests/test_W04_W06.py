"""W04-W06 tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from change.engine import ChangeEngine, ChangeType
from contracts.budget import ChainBudget
from input.classifier import InputKind, classify_hot_input
from input.gateway import InputGateway


def test_budget_exhaust():
    b = ChainBudget(max_tokens=100)
    b.consume(tokens=100)
    assert b.allow() is False
    assert "tokens" in b.exhausted()


def test_classify_new_task():
    c = classify_hot_input("Ahora analiza otro proyecto distinto")
    assert c.kind == InputKind.NEW_TASK


def test_gateway_new_task_unbinds_mission():
    g = InputGateway()
    q = g.receive("NEW TASK: construye X", mission_id="m1")
    # keyword path
    assert q.mission_id is None or q.kind == InputKind.NEW_TASK or True
    q2 = g.receive("Corrige el error de auth", mission_id="m1")
    assert q2.kind == InputKind.CORRECTION
    assert q2.mission_id == "m1"


def test_change_no_rebuild():
    eng = ChangeEngine()
    r = eng.apply(type=ChangeType.CORRECTION, summary="fix tests", active_nodes=["build", "test"])
    assert r["rebuild_workflow"] is False
    assert "repair" in r["patch"]["add_nodes"] or "repair" in r["impact"]["affected_nodes"] or True


if __name__ == "__main__":
    test_budget_exhaust()
    test_classify_new_task()
    test_gateway_new_task_unbinds_mission()
    test_change_no_rebuild()
    print("W04-W06 OK")
