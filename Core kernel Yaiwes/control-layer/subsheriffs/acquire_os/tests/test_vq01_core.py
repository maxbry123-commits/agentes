"""VQ-01 — AcquireEngine offline."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# control-layer on path
CL = Path(__file__).resolve().parents[2]
if str(CL.parent.parent) not in sys.path:
    sys.path.insert(0, str(CL.parent.parent))

from control_layer_path import ensure_path  # type: ignore  # optional

# direct import via package path hack
sys.path.insert(0, str(Path(__file__).resolve().parents[2].parent.parent))

# Import by file path structure: control-layer is not a package name with hyphen
import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASE = Path(__file__).resolve().parents[1]
core = _load("acquire_core", BASE / "core.py")


class TestVQ01(unittest.TestCase):
    def test_happy_path(self):
        recipe = {
            "artifact_id": "demo.pkg",
            "source_type": "package_manager",
            "pin": {"version": "1.0.0"},
            "build": {},
            "install": {"cmd": "echo ok"},
            "verify": {"cmd": "true"},
        }
        with tempfile.TemporaryDirectory() as td:
            # load engine with deps from same dir
            sys.path.insert(0, str(BASE))
            from core import AcquireEngine

            ctx = AcquireEngine().run(recipe, td)
            statuses = {r.name: r.status for r in ctx.results}
            self.assertEqual(statuses.get("01_RECEIVE"), "PASS")
            self.assertNotEqual(statuses.get("24_PROMOTE"), "FAILED")

    def test_missing_artifact_fails(self):
        sys.path.insert(0, str(BASE))
        from core import AcquireEngine

        with tempfile.TemporaryDirectory() as td:
            ctx = AcquireEngine().run({"source_type": "local"}, td)
            self.assertTrue(ctx.has_failed())


if __name__ == "__main__":
    unittest.main()
