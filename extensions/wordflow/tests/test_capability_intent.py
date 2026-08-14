# -*- coding: utf-8 -*-
"""Tests T37 CapabilityIntentResolver."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.capability_intent import resolve_intent


class TestCapabilityIntent(unittest.TestCase):
    def test_code(self):
        r = resolve_intent("implement patch for module")
        self.assertIn("code", r["capabilities"])

    def test_publish(self):
        r = resolve_intent("publish release to github")
        self.assertIn("github_publish", r["capabilities"])

    def test_default(self):
        r = resolve_intent("hello")
        self.assertEqual(r["capabilities"], ["general"])


if __name__ == "__main__":
    unittest.main()
