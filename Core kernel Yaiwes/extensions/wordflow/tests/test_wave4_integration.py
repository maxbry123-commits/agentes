# -*- coding: utf-8 -*-
"""T28 WAVE-4 integration tests."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.execution_facade import ExecutionFacade
from extensions.wordflow.engine.wave4_runtime import run_mission_safe


class TestWave4Integration(unittest.TestCase):
    def test_allow_noop(self):
        r = run_mission_safe(
            "objective: wave4 close\nsuccess: evidence\nconstraint: 0% LLM\n",
            risk_score=0,
            kind="noop",
        )
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["evidence"]["node_count"], 3)

    def test_deny_sheriff(self):
        r = run_mission_safe(
            "objective: blocked\nsuccess: deny\nconstraint: none\n",
            risk_score=9,
            band="quarantine",
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "sheriff")

    def test_resource_after_allow(self):
        cat = ResourceCatalog()
        e = make_entry(name="w4", kind="skill", source="local", fetchable=True)
        cat.add(e)
        fac = ExecutionFacade(catalog=cat)
        r = run_mission_safe(
            "objective: resource after sheriff\nsuccess: load\nconstraint: ok\n",
            kind="resource",
            resource_id=e["resource_id"],
            facade=fac,
        )
        self.assertTrue(r["ok"])
        self.assertIsNotNone(r["route"])


if __name__ == "__main__":
    unittest.main()
