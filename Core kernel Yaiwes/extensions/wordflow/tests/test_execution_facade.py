# -*- coding: utf-8 -*-
"""Tests G4 ExecutionFacade."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engines.fake_engine import StaticFakeEngine
from extensions.wordflow.engine.execution_facade import ExecutionFacade
from extensions.wordflow.engine.loop_bridge import bridge_to_lock
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.runtime_bus import RuntimeBus


class TestExecutionFacade(unittest.TestCase):
    def _lock(self):
        return bridge_to_lock(
            "objective: facade g4\nsuccess: route ok\nconstraint: 0% LLM\n"
        )["lock"]

    def test_resource_prepare(self):
        cat = ResourceCatalog()
        e = make_entry(name="s", kind="skill", source="local", fetchable=True)
        cat.add(e)
        fac = ExecutionFacade(catalog=cat)
        r = fac.route(self._lock(), kind="resource", resource_id=e["resource_id"])
        self.assertTrue(r["ok"])

    def test_engine_via_bus(self):
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text="facade-ok"))
        fac = ExecutionFacade(bus=bus)
        r = fac.route(
            self._lock(),
            kind="engine",
            engine_id="fake_static",
            prompt="facade-ok",
            route_name="ANALYSIS",
        )
        self.assertEqual(r["stage"], "engine_bus")
        self.assertIn("manifest_id", r)

    def test_unknown_kind(self):
        fac = ExecutionFacade()
        r = fac.route(self._lock(), kind="magic")
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()
