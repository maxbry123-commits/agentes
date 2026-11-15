# -*- coding: utf-8 -*-
"""Tests T46 StateAuthority."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.state_authority import StateAuthority, SystemState


class TestStateAuthority(unittest.TestCase):
    def test_happy_path(self):
        sa = StateAuthority()
        self.assertTrue(sa.transition(SystemState.VALIDAR)["ok"])
        self.assertTrue(sa.transition(SystemState.AUDITAR)["ok"])

    def test_invalid(self):
        sa = StateAuthority(SystemState.DETENIDO)
        r = sa.transition(SystemState.AUDITAR)
        self.assertFalse(r["ok"])

    def test_snapshot(self):
        sa = StateAuthority()
        snap = sa.snapshot()
        self.assertEqual(snap["state"], "CONSTRUIR")
        self.assertIn("VALIDAR", snap["allowed_next"])


if __name__ == "__main__":
    unittest.main()
