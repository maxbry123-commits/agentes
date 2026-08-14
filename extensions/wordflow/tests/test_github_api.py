# -*- coding: utf-8 -*-
"""Tests D4 GitDataApiExecutor (no network success without token)."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.github_api import GitDataApiExecutor
from extensions.wordflow.engine.github_publisher import GitHubPublisher, MapCredentialStore


class TestGitDataApi(unittest.TestCase):
    def test_no_token(self):
        ex = GitDataApiExecutor()
        r = ex.publish({"repository": "a/b", "files": []}, "")
        self.assertEqual(r["reason"], "NO_TOKEN")

    def test_missing_content(self):
        ex = GitDataApiExecutor()
        # will fail at API or missing content before network if content_map empty
        r = ex.publish(
            {
                "repository": "a/b",
                "branch": "main",
                "files": [{"source": "x", "destination": "x.py"}],
                "commit_message": "t",
                "content_map": {},
            },
            "fake-token",
        )
        # either MISSING_CONTENT or API_ERROR depending on path
        self.assertFalse(r["ok"])

    def test_publisher_with_api_executor_unresolved(self):
        pub = GitHubPublisher(
            credentials=MapCredentialStore({}),
            executor=GitDataApiExecutor(),
        )
        r = pub.publish(
            {
                "token_ref": "github_token",
                "repository": "u/r",
                "branch": "main",
                "files": [{"source": "a", "destination": "a"}],
                "commit_message": "x",
            }
        )
        self.assertEqual(r["reason"], "TOKEN_REF_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
