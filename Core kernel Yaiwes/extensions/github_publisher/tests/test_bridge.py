# -*- coding: utf-8 -*-
"""A-DEP-02 tests — BUILD → publish bridge."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from github_publisher.engine.bridge import (  # noqa: E402
    build_publish_request,
    publish_from_build,
)
from github_publisher.engine.publisher import FakeGitHubPort  # noqa: E402


class TestBridge(unittest.TestCase):
    def test_build_request(self):
        req = build_publish_request(
            files=[{"source": "build/x.py", "destination": "ext/x.py", "content": "x"}],
            repository="maxbry123-commits/agentes",
            commit_message="add x",
        )
        self.assertEqual(req["token_ref"], "github_token")
        self.assertEqual(len(req["files"]), 1)

    def test_publish_from_build(self):
        port = FakeGitHubPort()
        r = publish_from_build(
            files=[{
                "source": "build/a.py",
                "destination": "extensions/demo/a.py",
                "content": "print(1)\n",
            }],
            repository="maxbry123-commits/agentes",
            commit_message="Add a",
            credential_store={"github_token": "fake"},
            port=port,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["files_count"], 1)
        self.assertEqual(len(port.commits), 1)


if __name__ == "__main__":
    unittest.main()
