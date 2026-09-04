"""Tests A15 · plugin adapter."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extension.plugin_adapter import PluginAdapter, TurnInput


def test_mount_turn_unmount():
    with tempfile.TemporaryDirectory() as td:
        ad = PluginAdapter(Path(td))
        h = ad.on_mount({"state_dir": td})
        assert h["status"] == "ok"
        out = ad.on_turn(TurnInput(text="hola", op_type="READ_LOCAL"))
        assert out.ok is True
        assert out.chat_output.get("mode") == "extension"
        ad.on_unmount()
        out2 = ad.on_turn({"text": "x"})
        assert out2.ok is False
        assert out2.error == "plugin_not_mounted"


def test_secret_turn_blocked():
    with tempfile.TemporaryDirectory() as td:
        ad = PluginAdapter(Path(td))
        ad.on_mount({"state_dir": td})
        out = ad.on_turn(
            {
                "text": "write key",
                "op_type": "WRITE_LOCAL",
                "payload": {"content": "api_key=sk-secret"},
            }
        )
        assert out.ok is False
        assert out.chat_output.get("status") == "BLOCKED"


if __name__ == "__main__":
    test_mount_turn_unmount()
    test_secret_turn_blocked()
    print("A15 tests OK")
