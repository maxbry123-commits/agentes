# -*- coding: utf-8 -*-
"""A-AUD-03 tests — RepoTruthPort Fake only (offline)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.repo_truth import FakeRepoTruth, RepoTruthPort  # noqa: E402

SHA_A = "e36eba91b8100003eaedef88550f3ae706f1ef4a"
SHA_B = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"
BLOB = "b9ec1ecfa8589ac3777ff7de8c324867f9a1ff6b"


def _fake() -> FakeRepoTruth:
    return FakeRepoTruth(
        commits={
            SHA_B: {
                "sha": SHA_B,
                "message": "A11 close",
                "stats": {"additions": 100, "deletions": 10, "total": 110},
            }
        },
        tree={
            SHA_B: {
                "control-layer/control/fingerprint.py",
                "control-layer/sheriff/states.py",
                "extensions/audit_forensic/schema_module.json",
            }
        },
        blobs={
            SHA_B: {
                "extensions/audit_forensic/schema_module.json": BLOB,
            }
        },
        runs={
            "31354290850": {
                "conclusion": "success",
                "head_sha": SHA_B,
                "status": "completed",
                "html_url": "https://github.com/example/actions/runs/31354290850",
                "id": 31354290850,
            }
        },
        jobs={
            "31354290850": [
                {"id": 1, "name": "test", "conclusion": "success"},
            ]
        },
    )


class TestFakeRepoTruth(unittest.TestCase):
    def setUp(self):
        self.port = _fake()

    def test_protocol(self):
        self.assertIsInstance(self.port, RepoTruthPort)

    def test_get_commit(self):
        c = self.port.get_commit(SHA_B)
        self.assertIsNotNone(c)
        self.assertEqual(c["sha"], SHA_B)
        self.assertEqual(c["stats"]["additions"], 100)

    def test_get_commit_missing(self):
        self.assertIsNone(self.port.get_commit("0" * 40))

    def test_path_exists(self):
        self.assertTrue(
            self.port.path_exists(SHA_B, "control-layer/control/fingerprint.py")
        )
        self.assertFalse(self.port.path_exists(SHA_B, "no/such/file.py"))

    def test_get_blob_sha(self):
        sha = self.port.get_blob_sha(
            SHA_B, "extensions/audit_forensic/schema_module.json"
        )
        self.assertEqual(sha, BLOB)
        self.assertIsNone(self.port.get_blob_sha(SHA_B, "missing.py"))

    def test_workflow_run(self):
        r = self.port.get_workflow_run("31354290850")
        self.assertIsNotNone(r)
        self.assertEqual(r["conclusion"], "success")
        self.assertEqual(r["head_sha"], SHA_B)

    def test_workflow_run_missing(self):
        self.assertIsNone(self.port.get_workflow_run("0"))

    def test_get_job(self):
        j = self.port.get_job("31354290850")
        self.assertIsNotNone(j)
        self.assertEqual(j["conclusion"], "success")
        j2 = self.port.get_job("31354290850", "test")
        self.assertEqual(j2["name"], "test")

    def test_empty_fake(self):
        empty = FakeRepoTruth()
        self.assertIsNone(empty.get_commit(SHA_A))
        self.assertFalse(empty.path_exists(SHA_A, "x"))
        self.assertIsNone(empty.get_blob_sha(SHA_A, "x"))
        self.assertIsNone(empty.get_workflow_run("1"))
        self.assertIsNone(empty.get_job("1"))


if __name__ == "__main__":
    unittest.main()
