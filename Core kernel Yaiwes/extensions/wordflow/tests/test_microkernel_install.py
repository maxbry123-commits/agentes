# -*- coding: utf-8 -*-
"""Tests T44 MicrokernelInstallPlanner."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.microkernel_install import MicrokernelInstallPlanner


class TestMicrokernelInstall(unittest.TestCase):
    def test_openclaw_deferred(self):
        p = MicrokernelInstallPlanner()
        r = p.plan_install("openclaw")
        self.assertEqual(r["action"], "DEFERRED")

    def test_unknown(self):
        p = MicrokernelInstallPlanner()
        r = p.plan_install("nope")
        self.assertEqual(r["reason"], "UNKNOWN_AGENT")

    def test_batch(self):
        p = MicrokernelInstallPlanner()
        r = p.plan_batch(["openclaw", "hermes", "aider"])
        self.assertEqual(r["n"], 3)
        self.assertEqual(r["deferred"], 3)


if __name__ == "__main__":
    unittest.main()
