# -*- coding: utf-8 -*-
"""Tests C-08 Resource Runtime — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.resource_runtime import ResourceRuntime, ResourceRuntimeError


class TestResourceRuntime(unittest.TestCase):
    def test_full_pipeline_local(self):
        rt = ResourceRuntime()
        r = rt.run_pipeline(name="skill-a", kind="skill", source="local")
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], "AVAILABLE")

    def test_load_before_available_denied(self):
        rt = ResourceRuntime()
        d = rt.discover(name="x", kind="tool", source="local")
        rid = d["resource_id"]
        denied = rt.load(rid)
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["reason"], "NOT_AVAILABLE")

    def test_invalid_transition(self):
        rt = ResourceRuntime()
        d = rt.discover(name="y", kind="tool")
        rid = d["resource_id"]
        with self.assertRaises(ResourceRuntimeError):
            rt.mark_available(rid)  # must not skip states

    def test_register_resolve_pin(self):
        rt = ResourceRuntime()
        d = rt.discover(name="z", kind="dataset", source="local", fetchable=True)
        rid = d["resource_id"]
        self.assertTrue(rt.register(rid)["ok"])
        self.assertTrue(rt.resolve(rid)["ok"])
        self.assertTrue(rt.pin(rid, "sha40deadbeef")["ok"])


if __name__ == "__main__":
    unittest.main()
