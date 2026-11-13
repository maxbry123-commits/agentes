"""VK-03 tests — GapTaskCompiler."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.repo_truth import LocalRepoTruth
from wordflow_kernel.forensic import ForensicEngine
from wordflow_kernel.gap_tasks import GapTaskCompiler
from wordflow_kernel.workflow import WordflowKernel


class TestVK03(unittest.TestCase):
    def test_compile_from_audit(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "a.py").write_text("x = 1\n", encoding="utf-8")
            repo = LocalRepoTruth(td)
            eng = ForensicEngine(repo)
            report = eng.audit(
                "local",
                requirements=[{"requirement": "NeedFoo", "marker": "NeedFoo"}],
            )
            tasks = GapTaskCompiler().compile(report, "WS1")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].workspace_id, "WS1")
            self.assertTrue(tasks[0].task_id.startswith("task_"))

    def test_workflow_audit_to_plan(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "b.py").write_text("class Present:\n    pass\n", encoding="utf-8")
            repo = LocalRepoTruth(td)
            k = WordflowKernel(
                audit_engine=ForensicEngine(repo),
                compiler=GapTaskCompiler(),
            )
            report, tasks = k.audit_to_plan(
                "M1",
                "W1",
                "local",
                [
                    {"requirement": "Present", "marker": "Present"},
                    {"requirement": "Absent", "marker": "AbsentXYZ"},
                ],
            )
            self.assertEqual(report.matches, 1)
            self.assertEqual(len(tasks), 1)


if __name__ == "__main__":
    unittest.main()
