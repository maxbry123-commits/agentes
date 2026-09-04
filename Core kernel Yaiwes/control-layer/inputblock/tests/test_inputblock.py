"""Tests A07 · chain integrity + TTL + literal."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inputblock.store import Criticality, InputStore
from inputblock.reader import ChainBrokenError, InputBlockReader


def test_chain_ok():
    s = InputStore()
    s.append("hola", criticality=Criticality.ORDEN)
    s.append("mundo", criticality=Criticality.INFO)
    r = InputBlockReader(s)
    report = r.verify_or_raise()
    assert report.ok
    assert report.length == 2


def test_literal_preserved():
    s = InputStore()
    raw = "  espacios  \n y \\"
    b = s.append(raw)
    assert InputBlockReader(s).read_literal(b.block_id) == raw


def test_tamper_breaks_chain():
    s = InputStore()
    s.append("a")
    s.append("b")
    # tamper
    bid = s._order[0]
    s._blocks[bid].content = "hacked"
    r = InputBlockReader(s)
    report = r.verify_chain()
    assert report.ok is False
    try:
        r.verify_or_raise()
        assert False, "should raise"
    except ChainBrokenError:
        pass


def test_ttl_purge_keeps_critico():
    s = InputStore(default_ttl_sec=1)
    s.append("x", criticality=Criticality.INFO, ttl_sec=0)
    s.append("y", criticality=Criticality.CRITICO, ttl_sec=0)
    time.sleep(0.01)
    removed = s.purge_expired(now=time.time() + 10)
    assert removed == 1
    assert len(s) == 1
    assert list(s)[0].criticality == Criticality.CRITICO


if __name__ == "__main__":
    test_chain_ok()
    test_literal_preserved()
    test_tamper_breaks_chain()
    test_ttl_purge_keeps_critico()
    print("A07 tests OK")
