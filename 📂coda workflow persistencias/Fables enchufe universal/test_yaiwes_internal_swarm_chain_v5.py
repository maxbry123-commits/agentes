from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaiwes_internal_swarm_chain_v5 as swarm


class V5SwarmTest(unittest.TestCase):
    def test_canonical_entry_routes_through_v81_and_preserves_contract(self):
        released = [
            {
                "component": f"YAIWES {i:02d}",
                "status": "RELEASED",
                "workflow_status": "COMPLETED",
                "real_internal_workflow": True,
            }
            for i in range(1, 25)
        ]
        fake_report = {
            "components": 24,
            "real_internal_workflows_executed": 24,
            "research_cycles": 24,
            "research_fail_closed": True,
            "durable_backend": "sqlite-wal",
            "recovered_components": 3,
            "status": "CLOSED_24_CODA_DURABLE",
            "universal_plug_after_component_24": True,
            "evidence": [{"internal_state": item} for item in released],
        }
        with tempfile.TemporaryDirectory() as td:
            registry_path = Path(td) / "registry.json"
            registry_path.write_text(json.dumps({"count": 24}), encoding="utf-8")
            with patch.object(swarm.research_gate, "run_coda_chain", return_value=fake_report) as run:
                result = swarm.run_swarm(
                    registry_path,
                    Path(td) / "state",
                    "V5-E2E-001",
                    {"goal": "task-persistence"},
                )
        run.assert_called_once()
        self.assertEqual(result["components_completed"], 24)
        self.assertEqual(result["research_cycles"], 24)
        self.assertTrue(result["research_fail_closed"])
        self.assertTrue(result["handoff_continuity"])
        self.assertEqual(result["durable_backend"], "sqlite-wal")
        self.assertEqual(result["recovered_components"], 3)
        self.assertTrue(result["universal_plug_after_component_24"])
        self.assertTrue(all(x["status"] == "RELEASED" for x in result["evidence"]))

    def test_registry_requires_24_components(self):
        with tempfile.TemporaryDirectory() as td:
            registry_path = Path(td) / "registry.json"
            registry_path.write_text(json.dumps({"count": 23}), encoding="utf-8")
            with self.assertRaises(ValueError):
                swarm.run_swarm(registry_path, Path(td) / "state", "bad-count", {})


if __name__ == "__main__":
    unittest.main()
