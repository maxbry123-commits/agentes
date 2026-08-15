"""VK-02 tests — LocalRepoTruth + ForensicEngine."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.repo_truth import LocalRepoTruth
from wordflow_kernel.forensic import ForensicEngine


class TestVK02(unittest.TestCase):
    def test_list_and_match(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "mod.py").write_text("class GitDataAPIPort:\n    pass\n", encoding="utf-8")
            repo = LocalRepoTruth(td)
            files = repo.list_files()
            self.assertTrue(any(f.path.endswith("mod.py") for f in files))
            eng = ForensicEngine(repo)
            report = eng.audit(
                "local",
                requirements=[
                    {"requirement": "GitDataAPIPort exists", "marker": "GitDataAPIPort"},
                    {"requirement": "MissingThing", "marker": "MissingThingXYZ"},
                ],
            )
            self.assertEqual(report.matches, 1)
            self.assertEqual(report.missing, 1)
            self.assertEqual(report.status, "GAPS_FOUND")

    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as td:
            repo = LocalRepoTruth(td)
            with self.assertRaises(ValueError):
                repo.read_file("../outside")


if __name__ == "__main__":
    unittest.main()
