from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaiwes_coda_hybrid_v9 as v9


def _verified_report(task_id: str) -> dict:
    evidence = [
        {
            "research_status": "EXECUTED",
            "internal_state": {"workflow_status": "COMPLETED"},
        }
        for _ in range(24)
    ]
    return {
        "task_id": task_id,
        "status": "COMPLETED",
        "report": {
            "status": "CLOSED_24_CODA",
            "components": 24,
            "completed_internal_workflows": 24,
            "real_internal_workflows_executed": 24,
            "research_cycles": 24,
            "universal_plug_after_component_24": True,
            "evidence": evidence,
        },
    }


class HybridV9Tests(unittest.TestCase):
    def test_activation_contract_covers_exactly_24_components(self):
        contract = v9.activation_contract()
        self.assertEqual(contract["component_order"], list(range(1, 25)))
        self.assertEqual(set(map(int, contract["component_modes"])), set(range(1, 25)))
        self.assertEqual(
            set(contract["subagent_capable"]) | set(contract["service_stages"]),
            set(range(1, 25)),
        )
        self.assertTrue(contract["deterministic_fan_in"])
        self.assertTrue(contract["durable_queue"])

    def test_equal_quality_tie_break_is_lexical_and_replayable(self):
        a = _verified_report("same--alpha")
        a["candidate_id"] = "alpha"
        b = _verified_report("same--beta")
        b["candidate_id"] = "beta"
        first = v9.deterministic_fan_in([b, a])
        second = v9.deterministic_fan_in([a, b])
        self.assertEqual(first["status"], "RESOLVED_VERIFIED")
        self.assertEqual(first["winner"]["candidate_id"], "alpha")
        self.assertEqual(second["winner"], first["winner"])

    def test_incomplete_candidate_cannot_win_over_verified_candidate(self):
        good = _verified_report("problem--good")
        good["candidate_id"] = "good"
        bad = {
            "candidate_id": "bad",
            "task_id": "problem--bad",
            "status": "COMPLETED",
            "report": {"status": "PARTIAL", "components": 3, "research_cycles": 2},
        }
        result = v9.deterministic_fan_in([bad, good])
        self.assertEqual(result["winner"]["candidate_id"], "good")

    def test_escalation_is_structured_and_deterministic(self):
        blocked = v9.escalation_decision({"status": "BLOCKED", "no_progress": True})
        clean = v9.escalation_decision({"status": "COMPLETED"})
        self.assertTrue(blocked["escalate"])
        self.assertIn("no_progress", blocked["reasons"])
        self.assertEqual(blocked["candidate_components"], list(v9.SUBAGENT_CAPABLE))
        self.assertFalse(clean["escalate"])
        self.assertEqual(clean["candidate_components"], [])

    def test_independent_queue_never_selects_a_winner(self):
        fake = {
            "status": "COMPLETED",
            "durable_queue": True,
            "results": [_verified_report("task-a"), _verified_report("task-b")],
        }
        with patch.object(v9.v8, "run_parallel_tasks", return_value=fake):
            result = v9.run_independent_queue(
                "/tmp/yaiwes-v9-test",
                [{"task_id": "task-a"}, {"task_id": "task-b"}],
            )
        self.assertEqual(result["mode"], "INDEPENDENT_QUEUE")
        self.assertIsNone(result["winner"])
        self.assertTrue(result["durable_queue"])

    def test_hive_fan_out_then_verified_fan_in(self):
        def fake_parallel(state_root, tasks, **kwargs):
            return {
                "status": "COMPLETED",
                "durable_queue": True,
                "results": [_verified_report(task["task_id"]) for task in tasks],
            }

        with tempfile.TemporaryDirectory() as td, patch.object(
            v9.v8, "run_parallel_tasks", side_effect=fake_parallel
        ):
            result = v9.run_hive_candidates(
                Path(td),
                "stuck-problem",
                [
                    {"candidate_id": "beta", "strategy": "safe-b"},
                    {"candidate_id": "alpha", "strategy": "safe-a"},
                ],
                max_workers=2,
            )
            self.assertEqual(result["fan_in"]["status"], "RESOLVED_VERIFIED")
            self.assertEqual(result["fan_in"]["winner"]["candidate_id"], "alpha")
            self.assertTrue((Path(td) / "HIVE-REPORT-V9.json").is_file())


if __name__ == "__main__":
    unittest.main()
