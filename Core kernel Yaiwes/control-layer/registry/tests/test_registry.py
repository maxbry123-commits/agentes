"""Tests A16 · registry."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from registry.method_registry import MethodManifest, MethodRegistry


def test_quarantine_until_tests():
    reg = MethodRegistry()
    rec = reg.register(
        MethodManifest(
            id="sec-review",
            name="Security Review",
            version="1.0.0",
            capabilities=["review_security"],
        )
    )
    assert rec.manifest.quarantine is True
    assert rec.manifest.active is False
    assert reg.resolve_capability("review_security") == []
    reg.mark_tests_passed("sec-review")
    assert reg.resolve_capability("review_security")[0].manifest.id == "sec-review"


def test_persist():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "reg.json"
        reg = MethodRegistry(path)
        reg.register({"id": "m1", "name": "M1", "version": "0.1.0", "capabilities": ["c1"], "tests_passed": True, "quarantine": False})
        reg2 = MethodRegistry(path)
        assert reg2.get("m1") is not None


if __name__ == "__main__":
    test_quarantine_until_tests()
    test_persist()
    print("A16 tests OK")
