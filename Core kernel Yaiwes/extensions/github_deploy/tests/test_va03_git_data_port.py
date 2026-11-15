"""VA-03 — FakeGitDataAPIPort + factory."""
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from github_deploy.git_data_port import (
    FakeGitDataAPIPort,
    FileChange,
    build_git_data_port,
)


class TestVA03(unittest.TestCase):
    def test_fake_deploy(self):
        port = FakeGitDataAPIPort()
        res = port.deploy(
            "o",
            "r",
            "main",
            [FileChange("a.py", b"x=1\n")],
            "msg",
            expected_head=None,
        )
        self.assertEqual(res.status, "DRY_RUN")
        self.assertTrue(res.commit_sha)
        self.assertEqual(len(port.calls), 1)

    def test_factory_default_fake(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITHUB_DEPLOY_REAL", None)
            os.environ.pop("GITHUB_TOKEN", None)
            port = build_git_data_port()
            self.assertIsInstance(port, FakeGitDataAPIPort)


if __name__ == "__main__":
    unittest.main()
