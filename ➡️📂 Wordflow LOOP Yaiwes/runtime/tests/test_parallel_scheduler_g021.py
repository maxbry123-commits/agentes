import asyncio
import unittest

from runtime.src.core.parallel_scheduler import (
    SchedulerError,
    TaskEnvelope,
    execute_tasks,
    plan_tasks,
)


class ParallelSchedulerG021Tests(unittest.TestCase):
    def test_priority_fan_out_fan_in_and_concurrency_bound(self):
        async def scenario():
            active = 0
            peak = 0
            events = []

            async def worker(task):
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                events.append(("start", task.task_id))
                await asyncio.sleep(0.01)
                events.append(("end", task.task_id))
                active -= 1
                return task.task_id

            tasks = [
                TaskEnvelope("root", 10, "k-root", payload={"n": 0}),
                TaskEnvelope("left", 9, "k-left", ("root",), {"n": 1}),
                TaskEnvelope("right", 8, "k-right", ("root",), {"n": 2}),
                TaskEnvelope("join", 7, "k-join", ("left", "right"), {"n": 3}),
            ]
            results = await execute_tasks(tasks, worker, max_concurrency=2)
            self.assertLessEqual(peak, 2)
            self.assertEqual([r.task_id for r in results], ["root", "left", "right", "join"])
            self.assertLess(events.index(("end", "root")), events.index(("start", "left")))
            self.assertLess(events.index(("end", "right")), events.index(("start", "join")))

        asyncio.run(scenario())

    def test_identical_idempotency_key_is_deduplicated(self):
        async def scenario():
            calls = []

            async def worker(task):
                calls.append(task.task_id)
                return {"value": task.payload["value"]}

            tasks = [
                TaskEnvelope("a", 5, "same", payload={"value": 1}),
                TaskEnvelope("a-copy", 5, "same", payload={"value": 1}),
            ]
            results = await execute_tasks(tasks, worker)
            self.assertEqual(calls, ["a"])
            self.assertEqual([r.status for r in results], ["COMPLETED", "DEDUPLICATED"])
            self.assertEqual(results[1].canonical_task_id, "a")

        asyncio.run(scenario())

    def test_retry_uses_explicit_idempotency_store(self):
        async def scenario():
            calls = 0
            store = {}

            async def worker(task):
                nonlocal calls
                calls += 1
                return task.payload

            tasks = [TaskEnvelope("once", 1, "once-key", payload={"safe": True})]
            first = await execute_tasks(tasks, worker, completed_by_key=store)
            second = await execute_tasks(tasks, worker, completed_by_key=store)
            self.assertEqual(calls, 1)
            self.assertEqual(first[0].status, "COMPLETED")
            self.assertEqual(second[0].status, "IDEMPOTENT_REPLAY")

        asyncio.run(scenario())

    def test_conflicting_dedup_fails_closed(self):
        with self.assertRaisesRegex(SchedulerError, "IDEMPOTENCY_KEY_CONFLICT"):
            plan_tasks([
                TaskEnvelope("a", 1, "same", payload={"value": 1}),
                TaskEnvelope("b", 1, "same", payload={"value": 2}),
            ])

    def test_duplicate_task_id_fails_even_after_dedup_alias(self):
        with self.assertRaisesRegex(SchedulerError, "DUPLICATE_TASK_ID"):
            plan_tasks([
                TaskEnvelope("a", 1, "first", payload={"value": 1}),
                TaskEnvelope("alias", 1, "first", payload={"value": 1}),
                TaskEnvelope("alias", 1, "second", payload={"value": 2}),
            ])

    def test_backpressure_and_cycles_fail_closed(self):
        tasks = [
            TaskEnvelope("a", 1, "a"),
            TaskEnvelope("b", 1, "b"),
        ]
        with self.assertRaisesRegex(SchedulerError, "BACKPRESSURE_QUEUE_LIMIT"):
            plan_tasks(tasks, max_queue=1)
        with self.assertRaisesRegex(SchedulerError, "CYCLE_DETECTED"):
            plan_tasks([
                TaskEnvelope("a", 1, "a", ("b",)),
                TaskEnvelope("b", 1, "b", ("a",)),
            ])


if __name__ == "__main__":
    unittest.main()
