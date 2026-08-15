"""VK-01 tests — models + runtime + workflow skeleton."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.models import MissionContract, TaskSpec, stable_hash, uid
from wordflow_kernel.runtime import ParallelRuntime, JobResult
from wordflow_kernel.workflow import WordflowKernel


class TestVK01(unittest.TestCase):
    def test_mission_contract_hash(self):
        m = MissionContract(
            mission_id="M1",
            workspace_id="W1",
            goals_in=("g1",),
            goals_out=("o1",),
            context_hash=stable_hash({"a": 1}),
        )
        self.assertEqual(m.version, 1)
        self.assertTrue(m.context_hash)

    def test_uid_prefix(self):
        self.assertTrue(uid("gap").startswith("gap_"))

    def test_parallel_runtime(self):
        class T:
            def __init__(self, task_id):
                self.task_id = task_id

        rt = ParallelRuntime(workers=2)
        results = rt.run([T("a"), T("b")], lambda t: t.task_id.upper())
        statuses = {r.status for r in results}
        self.assertEqual(statuses, {"COMPLETED"})

    def test_workflow_requires_engines(self):
        k = WordflowKernel()
        with self.assertRaises(RuntimeError):
            k.audit_to_plan("M", "W", "repo", [])


if __name__ == "__main__":
    unittest.main()
