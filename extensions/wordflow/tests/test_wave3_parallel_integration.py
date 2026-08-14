# -*- coding: utf-8 -*-
"""T24 — WAVE-3 integration: Scheduler+Pool+Sandbox+Lease+Retry+Circuit+SSH stub."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.checkpoint_store import CheckpointStore
from extensions.wordflow.engine.circuit_breaker import CircuitBreaker
from extensions.wordflow.engine.parallel_runtime import ParallelRuntime
from extensions.wordflow.engine.parallel_runtime_guarded import GuardedParallelRuntime
from extensions.wordflow.engine.retry_policy import RetryPolicy
from extensions.wordflow.engine.scheduler import Scheduler
from extensions.wordflow.engine.ssh_orchestrator import SSHError, SSHOrchestrator
from extensions.wordflow.engine.task_queue import WorkerPool


class TestWave3ParallelIntegration(unittest.TestCase):
    def test_scheduler_to_pool_dag(self):
        pool = WorkerPool(n_workers=2)
        pool.queue.enqueue(task_id="w3a", priority=50)
        pool.queue.enqueue(task_id="w3b", priority=50)
        pool.queue.enqueue(task_id="w3c", priority=90, depends_on=["w3a", "w3b"])
        order: list[str] = []

        def handler(task):
            order.append(task["task_id"])
            return True

        snap = pool.run_batch(handler)
        self.assertEqual(snap["scheduler"]["by_status"].get("DONE"), 3)
        self.assertLess(order.index("w3a"), order.index("w3c"))
        self.assertLess(order.index("w3b"), order.index("w3c"))

    def test_parallel_runtime_checkpoint(self):
        rt = ParallelRuntime(n_workers=2)
        store = CheckpointStore()
        rt.submit(task_id="p1")
        rt.submit(task_id="p2", depends_on=["p1"])

        def handler(ctx):
            store.save(
                lock_id="gl_wave3",
                task_id=ctx["task"]["task_id"],
                state={
                    "sandbox_id": ctx["sandbox"]["sandbox_id"],
                    "lease_id": ctx["lease"]["lease_id"],
                },
                label="wave3",
            )
            return True

        result = rt.run(handler)
        self.assertEqual(len(result["executions"]), 2)
        self.assertTrue(all(e["ok"] for e in result["executions"]))
        cps = store.list_for_lock("gl_wave3")
        self.assertEqual(len(cps), 2)
        self.assertTrue(store.verify(cps[0])["ok"])

    def test_guarded_retry_and_ssh_stub(self):
        state = {"n": 0}
        rt = GuardedParallelRuntime(
            n_workers=1,
            retry=RetryPolicy(max_attempts=3, strategy="fixed", base_delay_s=0),
            circuit=CircuitBreaker(failure_threshold=5, recovery_timeout_s=60),
        )
        rt.submit(task_id="g1")

        def handler(ctx):
            state["n"] += 1
            if state["n"] < 2:
                return False
            orch = SSHOrchestrator()
            remote = orch.run_remote("vps-stub", "echo wave3")
            self.assertTrue(remote["ok"])
            return True

        result = rt.run(handler)
        self.assertTrue(result["executions"][0]["ok"])
        self.assertEqual(state["n"], 2)

        with self.assertRaises(SSHError):
            SSHOrchestrator(allow_real=True)

    def test_scheduler_priority_deterministic(self):
        s = Scheduler(max_parallel=1)
        s.add("low", priority=10)
        s.add("high", priority=99)
        s.add("mid", priority=50)
        self.assertEqual(s.claim_next()["task_id"], "high")


if __name__ == "__main__":
    unittest.main()
