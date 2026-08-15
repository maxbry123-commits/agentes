"""VF-01 — LocalRepoTruth + GitHubRepoTruth factory (no live network required)."""
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.repo_truth import LocalRepoTruth, GitHubRepoTruth, build_repo_truth, RepoFile


class TestVF01(unittest.TestCase):
    def test_local(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "a.py").write_text("x=1\n", encoding="utf-8")
            repo = LocalRepoTruth(td)
            files = repo.list_files()
            self.assertTrue(any(f.path == "a.py" for f in files))
            self.assertTrue(repo.exists("a.py"))
            self.assertIsNotNone(repo.file_sha("a.py"))

    def test_factory_local(self):
        with tempfile.TemporaryDirectory() as td:
            r = build_repo_truth(f"local:{td}")
            self.assertIsInstance(r, LocalRepoTruth)

    def test_factory_github(self):
        r = build_repo_truth("github:maxbry123-commits/agentes@main")
        self.assertIsInstance(r, GitHubRepoTruth)
        self.assertEqual(r.owner, "maxbry123-commits")

    def test_github_list_mocked(self):
        gw = GitHubRepoTruth("o", "r", ref="main", token="")
        tree = {
            "tree": [
                {"type": "blob", "path": "x.py", "sha": "abc", "size": 3},
                {"type": "tree", "path": "d"},
            ]
        }
        with patch.object(gw, "head", return_value="sha0"), patch.object(
            gw, "_get", return_value=tree
        ):
            files = gw.list_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].path, "x.py")


if __name__ == "__main__":
    unittest.main()
