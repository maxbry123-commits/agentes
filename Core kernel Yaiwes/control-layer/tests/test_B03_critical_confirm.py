"""B03 · CRITICAL no arranca sin confirm."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.critical_gate import CriticalConfirmRequired, check_critical_confirm
from inputblock.store import Criticality, InputStore


def test_no_critical_ok():
    s = InputStore()
    s.append("info", criticality=Criticality.INFO)
    r = check_critical_confirm(list(s), confirmed=False)
    assert r.ok is True


def test_critical_without_confirm_raises():
    s = InputStore()
    s.append("peligro", criticality=Criticality.CRITICO)
    try:
        check_critical_confirm(list(s), confirmed=False, raise_on_block=True)
        raise AssertionError("expected CriticalConfirmRequired")
    except CriticalConfirmRequired as e:
        assert e.block_ids


def test_critical_without_confirm_soft():
    s = InputStore()
    s.append("peligro", criticality=Criticality.CRITICO)
    r = check_critical_confirm(list(s), confirmed=False, raise_on_block=False)
    assert r.ok is False
    assert r.error == "critical_confirm_required"


def test_critical_with_confirm_ok():
    s = InputStore()
    s.append("peligro", criticality=Criticality.CRITICO)
    r = check_critical_confirm(list(s), confirmed=True)
    assert r.ok is True
    assert r.confirmed is True


if __name__ == "__main__":
    test_no_critical_ok()
    test_critical_without_confirm_raises()
    test_critical_without_confirm_soft()
    test_critical_with_confirm_ok()
    print("B03 OK")
