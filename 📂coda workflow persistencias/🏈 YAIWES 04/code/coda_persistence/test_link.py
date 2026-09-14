import tempfile
import unittest
from pathlib import Path

from coda_persistence.link import EventCheckpointStore, PersistenceWorkflowLink


class AIPentestPersistenceTests(unittest.TestCase):
    def envelope(self, task_type="research", payload=None):
        return {
            "workflow_id": "wf-ai-pentest-safe",
            "task_id": "task-004",
            "task": {"task_type": task_type, "payload": payload or {"topic": "event persistence"}},
        }

    def test_event_checkpoint_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            result = PersistenceWorkflowLink(EventCheckpointStore(td)).run(self.envelope())
            self.assertEqual(result["status"], "HANDOFF_READY")
            self.assertEqual(result["handoff"]["to_link"], "05-AI-Infra-Guard")
            self.assertEqual([e["seq"] for e in result["events"]], list(range(1, len(result["events"]) + 1)))
            self.assertEqual(result["result"]["scanners"], "disabled")
            self.assertEqual(result["result"]["post_exploit"], "disabled")

    def test_resume_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            link = PersistenceWorkflowLink(EventCheckpointStore(td))
            first = link.run(self.envelope(payload={"v": 1}))
            second = link.run(self.envelope(payload={"v": 2}))
            self.assertEqual(first, second)
            self.assertEqual(second["attempts"], 1)

    def test_forbidden_security_action_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            result = PersistenceWorkflowLink(EventCheckpointStore(td), max_retries=2).run(self.envelope("brute_force"))
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["attempts"], 2)
            self.assertIn("TASK_TYPE_NOT_ALLOWED", result["error"])
            self.assertEqual(result["events"][-1]["type"], "failed_closed")

    def test_checkpoint_path_contained(self):
        with tempfile.TemporaryDirectory() as td:
            store = EventCheckpointStore(td)
            p = store.save("../../wf", "../../link", {"ok": True})
            self.assertTrue(Path(p).is_relative_to(Path(td)))


if __name__ == "__main__":
    unittest.main()
