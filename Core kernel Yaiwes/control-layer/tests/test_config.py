"""Tests A18 · config flags."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config, reset_config


def test_defaults_dual():
    cfg = load_config()
    assert cfg.enable_wordflow is True
    assert cfg.enable_extension is True
    assert cfg.enable_durable is True
    assert cfg.mount_mode_for() == "dual"


def test_override_extension_only():
    cfg = load_config({"enable_wordflow": False, "enable_extension": True})
    assert cfg.mount_mode_for() == "extension"


def test_env_roundtrip():
    os.environ["WORDFLOW"] = "0"
    os.environ["EXTENSION"] = "1"
    try:
        cfg = reset_config()
        assert cfg.enable_wordflow is False
        assert cfg.enable_extension is True
    finally:
        os.environ.pop("WORDFLOW", None)
        os.environ.pop("EXTENSION", None)
        reset_config()


if __name__ == "__main__":
    test_defaults_dual()
    test_override_extension_only()
    test_env_roundtrip()
    print("A18 tests OK")
