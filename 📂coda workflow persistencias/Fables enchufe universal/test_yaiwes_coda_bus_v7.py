from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

import yaiwes_coda_bus_v7 as bus


class TestCodaBusV7(unittest.TestCase):
    def setUp(self):
        self.original_roots = bus.core._component_roots_strict
        self.original_run_link = bus.core._run_link
        self.calls = []
        self.lock = threading.Lock()

        bus.core._component_roots_strict = lambda: {i: Path(f"/fake/YAIWES-{i:02d}") for i in range(1, 25)}

        def fake_run_link(ordinal, comp, task_id, task, current_input, state_root, history):
            label = f"YAIWES {ordinal:02d}"
            output = {
                "component": label,
                "workflow_status": "COMPLETED",
                "received": current_input["previous_output_hash"],
                "objective": task.get("objective"),
            }
            state = {
                "component": label,
                "task_id": task_id,
                "input_hash": bus._digest(current_input),
                "output_hash": bus._digest(output),
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
        broker = bus.ToolBroker()

        def research(payload):
            with self.lock:
                self.calls.append((payload["component"], payload["query"]))
            return {"facts": [payload["component"], "fresh-research"], "query": payload["query"]}

        broker.register(
            bus.ToolDescriptor(
                capability="web.research",
                name="test-web-research",
                source="unit-test",
                description="benign web research adapter",
                risk="benign",
                executable=True,
            ),
            research,
        )
        return broker

    def test_research_runs_before_every_internal_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = bus.run_coda_chain(
                tmp,
                "task-one",
                {"objective": "analyze a software architecture"},
                broker=self._broker(),
            )
            self.assertEqual(report["components"], 24)
            self.assertEqual(report["research_cycles"], 24)
            self.assertEqual(report["real_internal_workflows_executed"], 24)
            self.assertEqual(report["completed_internal_workflows"], 24)
            self.assertEqual(len(self.calls), 24)
            self.assertTrue(report["universal_plug_after_component_24"])
            self.assertTrue(all(x["research_status"] == "EXECUTED" for x in report["evidence"]))
            self.assertTrue((Path(tmp) / "UNIVERSAL_PLUG" / "task-one.json").is_file())
            knowledge_files = list((Path(tmp) / "CODA-KNOWLEDGE").glob("YAIWES-*/*.json"))
            self.assertEqual(len(knowledge_files), 24)

    def test_parallel_tasks_are_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = bus.run_parallel_tasks(
                tmp,
                [
                    {"task_id": "branch-a", "objective": "review module A"},
                    {"task_id": "branch-b", "objective": "review module B"},
                ],
                broker=self._broker(),
                max_workers=2,
            )
            self.assertEqual(report["branches"], 2)
            self.assertEqual(report["status"], "COMPLETED")
            self.assertEqual(len(self.calls), 48)
            self.assertTrue((Path(tmp) / "BRANCHES" / "branch-a" / "REPORTS" / "branch-a.json").is_file())
            self.assertTrue((Path(tmp) / "BRANCHES" / "branch-b" / "REPORTS" / "branch-b.json").is_file())

    def test_unverified_discovery_is_not_executable(self):
        broker = bus.ToolBroker()
        descriptor = bus.ToolDescriptor(
            capability="plugin.discovered",
            name="metadata-only",
            source="registry",
            risk="unverified-metadata",
            executable=False,
        )
        with self.assertRaises(ValueError):
            broker.register(descriptor, lambda payload: payload)


if __name__ == "__main__":
    unittest.main()
