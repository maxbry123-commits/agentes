from __future__ import annotations

import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

import yaiwes_coda_bus_v8 as bus
from yaiwes_coda_persistence_v8 import SQLiteDurableStore


class TestCodaBusV8(unittest.TestCase):
    def setUp(self):
        self.original_roots = bus.core._component_roots_strict
        self.original_run_link = bus.core._run_link
        self.calls: list[int] = []
        self.lock = threading.Lock()
        self.fail_at: int | None = None

        bus.core._component_roots_strict = lambda: {
            i: Path(f"/fake/YAIWES-{i:02d}") for i in range(1, 25)
        }

        def fake_run_link(ordinal, comp, task_id, task, current_input, state_root, history):
            with self.lock:
                self.calls.append(ordinal)
            if self.fail_at == ordinal:
                raise RuntimeError(f"simulated crash at {ordinal}")
            label = f"YAIWES {ordinal:02d}"
            output = {
                "component": label,
                "workflow_status": "COMPLETED",
                "ordinal": ordinal,
                "objective": task.get("objective"),
            }
            state = {
                "component": label,
                "task_id": task_id,
                "input_hash": bus.v7._digest(current_input),
                "output_hash": bus.v7._digest(output),
                "workflow_status": "COMPLETED",
                "workflow_source": f"{label}/code/workflow.py",
                "workflow_symbol": "run_workflow",
                "engine": "TEST_INTERNAL_WORKFLOW",
                "real_internal_workflow": True,
            }
            return state, output

        bus.core._run_link = fake_run_link

    def tearDown(self):
        bus.core._component_roots_strict = self.original_roots
        bus.core._run_link = self.original_run_link

    def _broker(self):
        broker = bus.v7.ToolBroker()

        def research(payload):
            return {
                "component": payload["component"],
                "query": payload["query"],
                "facts": ["fresh-research"],
            }

        broker.register(
            bus.v7.ToolDescriptor(
                capability="web.research",
                name="test-web-research",
                source="unit-test",
                description="benign research adapter",
                risk="benign",
                executable=True,
            ),
            research,
        )
        return broker

    def test_resume_from_last_committed_component_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "CODA-DURABLE.sqlite"
            durable = SQLiteDurableStore(db_path)
            self.fail_at = 7

            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                bus.run_coda_chain(
                    tmp,
                    "task-resume",
                    {"objective": "review a benign software architecture"},
                    broker=self._broker(),
                    durable=durable,
                )

            row = durable.workflow("task-resume")
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "INTERRUPTED")
            self.assertEqual(row["current_component"], 6)
            self.assertEqual(len(durable.load_completed("task-resume")), 6)

            self.fail_at = None
            report = bus.run_coda_chain(
                tmp,
                "task-resume",
                {"objective": "review a benign software architecture"},
                broker=self._broker(),
                durable=durable,
            )
            self.assertEqual(report["status"], "CLOSED_24_CODA_DURABLE")
            self.assertEqual(report["recovered_components"], 6)
            self.assertEqual(report["resume_from_component"], 7)
            self.assertEqual(len(report["evidence"]), 24)
            self.assertEqual([self.calls.count(i) for i in range(1, 7)], [1] * 6)
            self.assertEqual(self.calls.count(7), 2)
            self.assertEqual(durable.workflow("task-resume")["status"], "COMPLETED")
            self.assertEqual(len(durable.load_completed("task-resume")), 24)

            calls_before = list(self.calls)
            cached = bus.run_coda_chain(
                tmp,
                "task-resume",
                {"objective": "review a benign software architecture"},
                broker=self._broker(),
                durable=durable,
            )
            self.assertEqual(cached["status"], "CLOSED_24_CODA_DURABLE")
            self.assertEqual(self.calls, calls_before)

            events = [x["event_type"] for x in durable.events("task-resume")]
            self.assertIn("COMPONENT_INTERRUPTED", events)
            self.assertIn("WORKFLOW_COMPLETED", events)
            self.assertGreaterEqual(len(durable.tool_memory("task-resume")), 24)

            with sqlite3.connect(db_path) as conn:
                mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(str(mode).lower(), "wal")

    def test_workflow_id_is_an_idempotency_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            durable = SQLiteDurableStore(Path(tmp) / "CODA-DURABLE.sqlite")
            bus.run_coda_chain(
                tmp,
                "same-id",
                {"objective": "task A"},
                broker=self._broker(),
                durable=durable,
            )
            with self.assertRaisesRegex(ValueError, "different task"):
                bus.run_coda_chain(
                    tmp,
                    "same-id",
                    {"objective": "task B"},
                    broker=self._broker(),
                    durable=durable,
                )

    def test_parallel_tasks_use_durable_queue_and_isolated_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            durable = SQLiteDurableStore(Path(tmp) / "CODA-DURABLE.sqlite")
            report = bus.run_parallel_tasks(
                tmp,
                [
                    {"task_id": "branch-a", "objective": "review module A", "priority": 5},
                    {"task_id": "branch-b", "objective": "review module B", "priority": 1},
                ],
                broker=self._broker(),
                max_workers=2,
                durable=durable,
            )
            self.assertEqual(report["branches"], 2)
            self.assertEqual(report["status"], "COMPLETED")
            self.assertTrue(report["durable_queue"])
            self.assertEqual(durable.queue_state("branch-a")["status"], "DONE")
            self.assertEqual(durable.queue_state("branch-b")["status"], "DONE")
            self.assertEqual(durable.workflow("branch-a")["current_component"], 24)
            self.assertEqual(durable.workflow("branch-b")["current_component"], 24)
            self.assertEqual(len(self.calls), 48)

    def test_expired_queue_lease_is_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            durable = SQLiteDurableStore(Path(tmp) / "CODA-DURABLE.sqlite")
            durable.enqueue("recover-me", {"objective": "benign task"}, priority=2)
            first = durable.claim("dead-worker", allowed_task_ids=["recover-me"], lease_seconds=-1)
            self.assertEqual(first["task_id"], "recover-me")
            second = durable.claim("replacement-worker", allowed_task_ids=["recover-me"], lease_seconds=30)
            self.assertEqual(second["task_id"], "recover-me")
            durable.finish_queue("recover-me", True)
            self.assertEqual(durable.queue_state("recover-me")["status"], "DONE")


if __name__ == "__main__":
    unittest.main()
