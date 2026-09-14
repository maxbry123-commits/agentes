from __future__ import annotations

import unittest
from unittest.mock import patch

import yaiwes_coda_research_gate_v81 as gate


class TestResearchGateV81(unittest.TestCase):
    def _broker(self):
        broker = gate.bus_v8.v7.ToolBroker()
        broker.register(
            gate.bus_v8.v7.ToolDescriptor(
                capability="web.research",
                name="fake-research",
                source="unit-test",
                description="benign research adapter",
                risk="benign",
                executable=True,
            ),
            lambda payload: {"query": payload.get("query")},
        )
        return broker

    def _report(self):
        return {
            "schema": "yaiwes.coda.bus/v8",
            "components": 24,
            "research_cycles": 24,
            "real_internal_workflows_executed": 24,
            "completed_internal_workflows": 24,
            "universal_plug_after_component_24": True,
            "durable_backend": "sqlite-wal",
            "status": "CLOSED_24_CODA_DURABLE",
            "evidence": [
                {
                    "component": f"YAIWES {i:02d}",
                    "research_status": "EXECUTED",
                    "internal_state": {
                        "status": "RELEASED",
                        "workflow_status": "COMPLETED",
                        "real_internal_workflow": True,
                    },
                }
                for i in range(1, 25)
            ],
        }

    def test_chain_delegates_to_durable_v8_and_requires_research(self):
        fake = self._report()
        with patch.object(gate, "build_research_broker", return_value=self._broker()), patch.object(
            gate.bus_v8, "run_coda_chain", return_value=fake
        ) as run:
            report = gate.run_coda_chain("/tmp/state", "task-v81", {"objective": "benign task"})
        run.assert_called_once()
        self.assertTrue(report["research_fail_closed"])
        self.assertEqual(report["research_gate_schema"], gate.SCHEMA)
        self.assertEqual(report["durable_backend"], "sqlite-wal")

    def test_chain_rejects_missing_research_cycle(self):
        fake = self._report()
        fake["evidence"][7]["research_status"] = "ADAPTER_UNAVAILABLE"
        with patch.object(gate, "build_research_broker", return_value=self._broker()), patch.object(
            gate.bus_v8, "run_coda_chain", return_value=fake
        ):
            with self.assertRaisesRegex(RuntimeError, "research cycle did not execute"):
                gate.run_coda_chain("/tmp/state", "task-v81", {})

    def test_parallel_validates_every_branch(self):
        branch_a = self._report()
        branch_b = self._report()
        parallel = {
            "branches": 2,
            "status": "COMPLETED",
            "durable_queue": True,
            "results": [
                {"task_id": "a", "status": "COMPLETED", "report": branch_a},
                {"task_id": "b", "status": "COMPLETED", "report": branch_b},
            ],
        }
        with patch.object(gate, "build_research_broker", return_value=self._broker()), patch.object(
            gate.bus_v8, "run_parallel_tasks", return_value=parallel
        ) as run:
            report = gate.run_parallel_tasks("/tmp/state", [{"task_id": "a"}, {"task_id": "b"}])
        run.assert_called_once()
        self.assertEqual(report["status"], "COMPLETED")
        self.assertTrue(report["research_fail_closed"])


if __name__ == "__main__":
    unittest.main()
