import tempfile
import unittest
from pathlib import Path

from coda_persistence.link import CheckpointStore, PersistenceWorkflowLink


class PersistenceLinkTests(unittest.TestCase):
    def envelope(self, task_type="research", payload=None):
        return {
            "workflow_id": "wf-test-001",
            "task_id": "task-test-001",
            "task": {"task_type": task_type, "payload": payload or {"topic": "persistence"}},
        }

    def test_checkpoint_roundtrip_and_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            link = PersistenceWorkflowLink(store=store)
            result = link.run(self.envelope())
            self.assertEqual(result["status"], "HANDOFF_READY")
            self.assertEqual(result["handoff"]["to_link"], "02-CyberStrikeAI")
            restored = store.load("wf-test-001", "01-DeepAudit")
            self.assertEqual(restored["result"]["side_effects"], "none")

    def test_resume_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            link = PersistenceWorkflowLink(store=store)
            first = link.run(self.envelope(payload={"n": 1}))
            second = link.run(self.envelope(payload={"n": 999}))
            self.assertEqual(first, second)
            self.assertEqual(second["attempts"], 1)

    def test_forbidden_task_fails_closed_after_bounded_retries(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            link = PersistenceWorkflowLink(store=store, max_retries=2)
            result = link.run(self.envelope(task_type="exploit"))
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["attempts"], 2)
            self.assertIn("TASK_TYPE_NOT_ALLOWED", result["error"])

    def test_state_path_is_not_controlled_by_raw_ids(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            path = store.save("../../workflow", "../link", {"ok": True})
            self.assertTrue(Path(path).is_relative_to(Path(td)))
            self.assertNotIn("..", path.parts)


if __name__ == "__main__":
    unittest.main()
