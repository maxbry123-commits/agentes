# -*- coding: utf-8 -*-
"""Tests T14 Scheduler."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.scheduler import Scheduler, SchedulerError


class TestScheduler(unittest.TestCase):
    def test_priority_order(self):
        s = Scheduler(max_parallel=1)
        s.add("low", priority=10)
        s.add("high", priority=90)
        s.add("mid", priority=50)
        first = s.claim_next()
        self.assertEqual(first["task_id"], "high")

    def test_dag_deps(self):
        s = Scheduler()
        s.add("a", priority=50)
        s.add("b", priority=80, depends_on=["a"])
        ready = s.ready_queue()
        self.assertEqual([t["task_id"] for t in ready], ["a"])
        s.claim_next()
        s.complete("a", success=True)
        ready2 = s.ready_queue()
        self.assertEqual(ready2[0]["task_id"], "b")

    def test_run_until_idle(self):
        s = Scheduler()
        s.add("t1")
        s.add("t2", depends_on=["t1"])
        order: list[str] = []

        def handler(task):
            order.append(task["task_id"])
            return True

        snap = s.run_until_idle(handler)
        self.assertEqual(order, ["t1", "t2"])
        self.assertEqual(snap["by_status"].get("DONE"), 2)

    def test_max_parallel_claim(self):
        s = Scheduler(max_parallel=2)
        s.add("a", priority=50)
        s.add("b", priority=50)
        s.add("c", priority=50)
        self.assertIsNotNone(s.claim_next())
        self.assertIsNotNone(s.claim_next())
        self.assertIsNone(s.claim_next())  # at capacity

    def test_duplicate(self):
        s = Scheduler()
        s.add("x")
        with self.assertRaises(SchedulerError):
            s.add("x")


if __name__ == "__main__":
    unittest.main()
