# -*- coding: utf-8 -*-
"""G7 — ports package exports + policy file present."""
from __future__ import annotations

import unittest
from pathlib import Path

from extensions.wordflow.engine import ports


class TestPortsExports(unittest.TestCase):
    def test_exports(self):
        for name in (
            "PlanningPort",
            "FakeOpenClawPlanner",
            "FakeHermesPlanner",
            "MemoryPort",
            "FakeHermesMemory",
        ):
            self.assertTrue(hasattr(ports, name), msg=name)

    def test_policy_file(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "policies" / "engine_attach.yaml"
        self.assertTrue(path.is_file(), msg=str(path))
        text = path.read_text(encoding="utf-8")
        self.assertIn("allow_real_engines: false", text)
        self.assertIn("openclaw_on_ping: false", text)


if __name__ == "__main__":
    unittest.main()
