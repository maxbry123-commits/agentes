# -*- coding: utf-8 -*-
"""Tests T15 TaskQueue + WorkerPool."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.task_queue import TaskQueue, WorkerPool


class TestTaskQueue(unittest.TestCase):
    def test_enqueue_auto_id(self):
        q = TaskQueue()
        t1 = q.enqueue(priority=10)
        t2 = q.enqueue(priority=90)
        self.assertTrue(t1["task_id"].startswith("tq_"))
        claimed = q.scheduler.claim_next()
        self.assertEqual(claimed["task_id"], t2["task_id"])

    def test_worker_pool_batch(self):
        pool = WorkerPool(n_workers=2)
        pool.queue.enqueue(task_id="a", priority=50)
        pool.queue.enqueue(task_id="b", priority=50)
        pool.queue.enqueue(task_id="c", priority=50, depends_on=["a"])
        order: list[str] = []

        def handler(task):
            order.append(task["task_id"])
            return True

        result = pool.run_batch(handler)
        self.assertEqual(result["scheduler"]["by_status"].get("DONE"), 3)
        self.assertIn("a", order)
        self.assertIn("b", order)
        self.assertIn("c", order)
        self.assertLess(order.index("a"), order.index("c"))

    def test_slots_capacity(self):
        pool = WorkerPool(n_workers=1)
        pool.queue.enqueue(task_id="x")
        pool.queue.enqueue(task_id="y")
        a1 = pool.assign()
        self.assertIsNotNone(a1)
        a2 = pool.assign()
        self.assertIsNone(a2)
        pool.release(a1["task"]["task_id"], success=True)
        a3 = pool.assign()
        self.assertIsNotNone(a3)


if __name__ == "__main__":
    unittest.main()
