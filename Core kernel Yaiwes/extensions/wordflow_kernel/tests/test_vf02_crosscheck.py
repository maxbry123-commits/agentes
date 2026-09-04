"""VF-02 tests — CrossVerifier."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.repo_truth import LocalRepoTruth
from wordflow_kernel.crosscheck import CrossVerifier, Claim


class TestVF02(unittest.TestCase):
    def test_implemented_and_missing(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "mod.py").write_text("class GitDataAPIPort:\n    pass\n", encoding="utf-8")
            v = CrossVerifier(LocalRepoTruth(td))
            report = v.verify(
                [
                    Claim("c1", "has port", marker="GitDataAPIPort"),
                    Claim("c2", "missing", marker="DoesNotExistXYZ"),
                    Claim("c3", "path partial", marker="Nope", path="mod.py"),
                ]
            )
            self.assertEqual(report["counts"]["IMPLEMENTED"], 1)
            self.assertEqual(report["counts"]["MISSING"], 1)
            self.assertEqual(report["counts"]["PARTIAL"], 1)
            self.assertEqual(report["status"], "GAPS_FOUND")


if __name__ == "__main__":
    unittest.main()
