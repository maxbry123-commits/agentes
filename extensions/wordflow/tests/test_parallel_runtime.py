# -*- coding: utf-8 -*-
"""Tests T22 ParallelRuntime."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.parallel_runtime import ParallelRuntime


class TestParallelRuntime(unittest.TestCase):
    def test_run_dag(self):
        rt = ParallelRuntime(n_workers=2)
        rt.submit(task_id="a", priority=50)
        rt.submit(task_id="b", priority=50)
        rt.submit(task_id="c", priority=50, depends_on=["a", "b"])
        seen: list[str] = []

        def handler(ctx):
            seen.append(ctx["task"]["task_id"])
            self.assertIsNotNone(ctx["sandbox"]["sandbox_id"])
            self.assertTrue(ctx["lease"]["lease_id"])
            return True

        result = rt.run(handler)
        self.assertEqual(len(seen), 3)
        self.assertIn("a", seen)
        self.assertIn("b", seen)
        self.assertIn("c", seen)
        self.assertLess(max(seen.index("a"), seen.index("b")), seen.index("c"))
        self.assertEqual(result["sandboxes"]["by_status"].get("FREE"), 2)

    def test_handler_failure(self):
        rt = ParallelRuntime(n_workers=1)
        rt.submit(task_id="x")
        result = rt.run(lambda ctx: False)
        self.assertFalse(result["executions"][0]["ok"])
        self.assertEqual(
            result["batch"]["scheduler"]["by_status"].get("FAILED"), 1
        )


if __name__ == "__main__":
    unittest.main()
