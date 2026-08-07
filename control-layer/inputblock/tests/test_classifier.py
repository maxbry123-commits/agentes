"""Tests A08 · classifier."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.classifier import InputKind, classify


def test_prefix_correction():
    r = classify("CORRECTION: el paso 3 estaba mal")
    assert r.kind == InputKind.CORRECTION
    assert r.same_mission is True


def test_prefix_new_task():
    r = classify("NEW_TASK: construir API de pagos")
    assert r.kind == InputKind.NEW_TASK
    assert r.same_mission is False


def test_prefix_update():
    r = classify("UPDATE: añadir test de integración")
    assert r.kind == InputKind.UPDATE
    assert r.same_mission is True


def test_explicit_meta():
    r = classify("texto libre", meta={"kind": "CORRECTION"})
    assert r.kind == InputKind.CORRECTION
    assert r.confidence == 1.0


def test_default_with_mission():
    r = classify("sigue con el plan", meta={"active_mission_id": "m1"})
    assert r.kind == InputKind.UPDATE
    assert r.same_mission is True


def test_default_no_mission():
    r = classify("hacer algo nuevo")
    assert r.kind == InputKind.NEW_TASK


if __name__ == "__main__":
    test_prefix_correction()
    test_prefix_new_task()
    test_prefix_update()
    test_explicit_meta()
    test_default_with_mission()
    test_default_no_mission()
    print("A08 tests OK")
