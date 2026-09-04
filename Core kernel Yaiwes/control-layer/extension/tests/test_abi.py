"""Tests A13 · ABI."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extension.abi import WordflowExtension


def test_load_health_capabilities():
    ext = WordflowExtension()
    assert ext.health().status == "down"
    assert ext.load({"mount_mode": "extension"}) is True
    h = ext.health()
    assert h.status == "ok"
    assert h.loaded is True
    assert "ping" in ext.capabilities()
    assert "C82" in ext.contracts()


def test_execute_ping():
    ext = WordflowExtension()
    ext.load({})
    out = ext.execute("ping")
    assert out.ok is True
    assert out.data.get("pong") is True


def test_execute_unknown():
    ext = WordflowExtension()
    ext.load({})
    out = ext.execute("nope")
    assert out.ok is False
    assert "unknown_capability" in (out.error or "")


def test_execute_before_load():
    ext = WordflowExtension()
    out = ext.execute("ping")
    assert out.ok is False
    assert out.error == "extension_not_loaded"


if __name__ == "__main__":
    test_load_health_capabilities()
    test_execute_ping()
    test_execute_unknown()
    test_execute_before_load()
    print("A13 tests OK")
