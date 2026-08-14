# -*- coding: utf-8 -*-
"""Tests G5 ParallelFacadeRuntime."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engines.fake_engine import StaticFakeEngine
from extensions.wordflow.engine.execution_facade import ExecutionFacade
from extensions.wordflow.engine.loop_bridge import bridge_to_lock
from extensions.wordflow.engine.parallel_facade import ParallelFacadeRuntime
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.runtime_bus import RuntimeBus


class TestParallelFacade(unittest.TestCase):
    def _lock(self):
        return bridge_to_lock(
            "objective: parallel facade g5\nsuccess: no bypass\nconstraint: bus only\n"
        )["lock"]

    def test_bypass_forbidden(self):
        lock = self._lock()
        fac = ExecutionFacade()
        rt = ParallelFacadeRuntime(lock, fac, n_workers=1)
        rt.submit(task_id="bad", payload={"bypass_bus": True, "kind": "engine"})
        out = rt.run_routed()
        self.assertFalse(out["executions"][0]["ok"])

    def test_resource_via_facade(self):
        lock = self._lock()
        cat = ResourceCatalog()
        e = make_entry(name="p", kind="tool", source="local", fetchable=True)
        cat.add(e)
        fac = ExecutionFacade(catalog=cat)
        rt = ParallelFacadeRuntime(lock, fac, n_workers=1)
        rt.submit(
            task_id="r1",
            payload={"kind": "resource", "resource_id": e["resource_id"]},
        )
        out = rt.run_routed()
        self.assertTrue(out["executions"][0]["ok"])

    def test_engine_via_bus(self):
        lock = self._lock()
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text="ok"))
        fac = ExecutionFacade(bus=bus)
        rt = ParallelFacadeRuntime(lock, fac, n_workers=1)
        rt.submit(
            task_id="e1",
            payload={
                "kind": "engine",
                "engine_id": "fake_static",
                "prompt": "ok",
            },
        )
        out = rt.run_routed()
        self.assertTrue(out["executions"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
