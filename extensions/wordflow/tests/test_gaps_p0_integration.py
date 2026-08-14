# -*- coding: utf-8 -*-
"""G8 — P0 gaps integration: bridge_full → facade → parallel no-bypass."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engines.fake_engine import StaticFakeEngine
from extensions.wordflow.engine.execution_facade import ExecutionFacade
from extensions.wordflow.engine.loop_bridge import bridge_full, bridge_to_lock
from extensions.wordflow.engine.parallel_facade import ParallelFacadeRuntime
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.runtime_bus import RuntimeBus


class TestGapsP0Integration(unittest.TestCase):
    def test_bridge_full_chain(self):
        r = bridge_full(
            "objective: g8 p0 chain\nsuccess: full stage\nconstraint: 0% LLM\n",
            task_hint="validate",
        )
        self.assertTrue(r.get("ok") or r.get("lock"))
        self.assertEqual(r["stage"], "full")
        self.assertIn("classification", r)
        self.assertIn("registers", r)

    def test_facade_engine_requires_manifest_path(self):
        lock = bridge_to_lock(
            "objective: g8 engine path\nsuccess: bus\nconstraint: deterministic\n"
        )["lock"]
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text="g8"))
        fac = ExecutionFacade(bus=bus)
        out = fac.route(
            lock,
            kind="engine",
            engine_id="fake_static",
            prompt="g8",
            route_name="ANALYSIS",
        )
        self.assertEqual(out["stage"], "engine_bus")
        self.assertIn("manifest_id", out)

    def test_parallel_bypass_denied_then_resource_ok(self):
        lock = bridge_to_lock(
            "objective: g8 parallel\nsuccess: no bypass\nconstraint: facade\n"
        )["lock"]
        cat = ResourceCatalog()
        e = make_entry(name="g8", kind="skill", source="local", fetchable=True)
        cat.add(e)
        fac = ExecutionFacade(catalog=cat)
        rt = ParallelFacadeRuntime(lock, fac, n_workers=1)

        rt.submit(task_id="bad", payload={"direct_engine": True, "kind": "engine"})
        bad = rt.run_routed()
        self.assertFalse(bad["executions"][0]["ok"])

        rt2 = ParallelFacadeRuntime(lock, fac, n_workers=1)
        rt2.submit(
            task_id="good",
            payload={"kind": "resource", "resource_id": e["resource_id"]},
        )
        good = rt2.run_routed()
        self.assertTrue(good["executions"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
