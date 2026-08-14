# -*- coding: utf-8 -*-
"""Tests D2 engine_attach."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engine_attach import EngineAttachRegistry, default_attach
from extensions.wordflow.engine.ports.planning_port import FakeHermesPlanner


class TestEngineAttach(unittest.TestCase):
    def test_default_fakes(self):
        reg = default_attach()
        snap = reg.snapshot()
        self.assertFalse(snap["allow_real"])
        self.assertIn("Fake", snap["planning_type"])

    def test_real_blocked(self):
        reg = EngineAttachRegistry()
        r = reg.attach_planning(FakeHermesPlanner(), name="real-oc", is_real=True)
        self.assertEqual(r["reason"], "REAL_ENGINE_DISABLED")

    def test_swap_fake(self):
        reg = EngineAttachRegistry()
        r = reg.attach_planning(FakeHermesPlanner(), name="FakeHermesPlanner")
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()
