import tempfile
import unittest
from pathlib import Path

from coda_persistence.link import CheckpointStore, PersistenceWorkflowLink


class CyberStrikePersistenceTests(unittest.TestCase):
    def envelope(self, task_type="research", payload=None):
        return {
            "workflow_id": "wf-cyberstrike-safe",
            "task_id": "task-002",
            "task": {"task_type": task_type, "payload": payload or {"topic": "durable workflow"}},
        }

    def test_safe_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            link = PersistenceWorkflowLink(CheckpointStore(td))
            result = link.run(self.envelope())
            self.assertEqual(result["status"], "HANDOFF_READY")
            self.assertEqual(result["handoff"]["to_link"], "03-LuaN1aoAgent")
            self.assertEqual(result["result"]["c2"], "disabled")
            self.assertEqual(result["result"]["network"], "disabled")

    def test_resume_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            link = PersistenceWorkflowLink(CheckpointStore(td))
            first = link.run(self.envelope(payload={"a": 1}))
            second = link.run(self.envelope(payload={"a": 999}))
            self.assertEqual(first, second)
            self.assertEqual(second["attempts"], 1)

    def test_offensive_task_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            link = PersistenceWorkflowLink(CheckpointStore(td), max_retries=2)
            result = link.run(self.envelope(task_type="lateral_movement"))
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["attempts"], 2)
            self.assertIn("TASK_TYPE_NOT_ALLOWED", result["error"])

    def test_checkpoint_path_contained(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            path = store.save("../../wf", "../../../link", {"ok": True})
            self.assertTrue(Path(path).is_relative_to(Path(td)))


if __name__ == "__main__":
    unittest.main()
