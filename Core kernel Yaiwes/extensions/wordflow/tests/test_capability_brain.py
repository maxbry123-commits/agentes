# -*- coding: utf-8 -*-
"""Tests T45 CapabilityBrain."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.capability_brain import CapabilityBrain
from extensions.wordflow.engine.extension_registry import ExtensionRegistry


class TestCapabilityBrain(unittest.TestCase):
    def test_with_registered_publish(self):
        reg = ExtensionRegistry()
        reg.register(
            "pub",
            kind="capability",
            capabilities=["github_publish"],
            factory=lambda: {"ok": True},
        )
        brain = CapabilityBrain(registry=reg)
        r = brain.run("publish release to github")
        self.assertIn("github_publish", r["required"])
        self.assertEqual(r["selected"].get("github_publish"), "pub")

    def test_stages(self):
        r = CapabilityBrain().run("hello")
        self.assertIn("discover", r["stages"])


if __name__ == "__main__":
    unittest.main()
