"""B02 · chain InputBlock rota → alerta / ChainBrokenError."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.reader import ChainBrokenError, InputBlockReader
from inputblock.store import Criticality, InputStore


def test_intact_chain_ok():
    s = InputStore()
    s.append("bloque-1", criticality=Criticality.ORDEN)
    s.append("bloque-2", criticality=Criticality.INFO)
    s.append("bloque-3", criticality=Criticality.CRITICO)
    report = InputBlockReader(s).verify_or_raise()
    assert report.ok is True
    assert report.length == 3


def test_content_tamper_raises():
    s = InputStore()
    s.append("alpha")
    s.append("beta")
    # mutación hostil del contenido sin recalcular hash
    first_id = s._order[0]
    s._blocks[first_id].content = "TAMPERED"
    reader = InputBlockReader(s)
    report = reader.verify_chain()
    assert report.ok is False
    assert any("content_hash_mismatch" in e for e in report.errors)
    try:
        reader.verify_or_raise()
        raise AssertionError("expected ChainBrokenError")
    except ChainBrokenError as ex:
        assert "chain_broken" in str(ex)


def test_prev_hash_break():
    s = InputStore()
    s.append("a")
    s.append("b")
    second_id = s._order[1]
    s._blocks[second_id].prev_hash = "sha256:" + ("f" * 64)
    report = InputBlockReader(s).verify_chain()
    assert report.ok is False
    assert any("prev_hash_mismatch" in e for e in report.errors)


def test_chain_hash_break():
    s = InputStore()
    s.append("a")
    s.append("b")
    second_id = s._order[1]
    s._blocks[second_id].chain_hash = "sha256:" + ("a" * 64)
    report = InputBlockReader(s).verify_chain()
    assert report.ok is False
    assert any("chain_hash_mismatch" in e for e in report.errors)


if __name__ == "__main__":
    test_intact_chain_ok()
    test_content_tamper_raises()
    test_prev_hash_break()
    test_chain_hash_break()
    print("B02 OK")
