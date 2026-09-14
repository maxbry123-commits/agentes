import tempfile
import unittest
from pathlib import Path

from coda_persistence.link import CheckpointStore, PersistenceWorkflowLink


class LuaN1aoPersistenceTests(unittest.TestCase):
    def envelope(self, task_type="research"):
        return {
            "workflow_id": "wf-luaniao-safe",
            "task_id": "task-003",
            "task": {"task_type": task_type, "payload": {"topic": "persistent DAG"}},
        }

    def test_graph_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            result = PersistenceWorkflowLink(CheckpointStore(td)).run(self.envelope())
            self.assertEqual(result["status"], "HANDOFF_READY")
            self.assertEqual(result["handoff"]["to_link"], "04-AI-Pentest")
            self.assertGreaterEqual(result["graph"]["revision"], 2)
            self.assertTrue(all(n["status"] == "DONE" for n in result["graph"]["nodes"]))
            self.assertEqual(result["result"]["connectivity"], "disabled")
            self.assertEqual(result["result"]["sandbox"], "disabled")

    def test_resume_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            link = PersistenceWorkflowLink(CheckpointStore(td))
            first = link.run(self.envelope())
            second = link.run(self.envelope())
            self.assertEqual(first, second)
            self.assertEqual(second["attempts"], 1)

    def test_forbidden_execution_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            result = PersistenceWorkflowLink(CheckpointStore(td), max_retries=2).run(self.envelope("network_scan"))
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["attempts"], 2)
            self.assertIn("TASK_TYPE_NOT_ALLOWED", result["error"])

    def test_checkpoint_path_is_contained(self):
        with tempfile.TemporaryDirectory() as td:
            store = CheckpointStore(td)
            p = store.save("../../wf", "../link", {"safe": True})
            self.assertTrue(Path(p).is_relative_to(Path(td)))


if __name__ == "__main__":
    unittest.main()
