# -*- coding: utf-8 -*-
"""G6 — GuardedParallelRuntime scope: Bus out of scope."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.parallel_runtime_guarded import SCOPE, GuardedParallelRuntime


class TestGuardedScope(unittest.TestCase):
    def test_scope_constants(self):
        self.assertIn("runtime_bus", SCOPE["out"])
        self.assertIn("execution_facade", SCOPE["out"])
        self.assertIn("parallel_tasks", SCOPE["in"])

    def test_run_exposes_scope(self):
        rt = GuardedParallelRuntime(n_workers=1)
        rt.submit(task_id="t")
        out = rt.run(lambda ctx: True)
        self.assertIn("runtime_bus", out["scope"]["out"])
        self.assertIn("retry", out["scope"]["in"])


if __name__ == "__main__":
    unittest.main()
