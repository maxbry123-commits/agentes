# -*- coding: utf-8 -*-
"""Tests T34 GitHubPublisher."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.github_publisher import (
    GitHubPublisher,
    MapCredentialStore,
    validate_contract,
)


class TestGitHubPublisher(unittest.TestCase):
    def test_validate_ok(self):
        c = {
            "token_ref": "github_token",
            "repository": "user/repo",
            "branch": "main",
            "files": [{"source": "build/a.py", "destination": "a.py"}],
            "commit_message": "add a",
        }
        self.assertTrue(validate_contract(c)["ok"])

    def test_inline_token_forbidden(self):
        c = {
            "token_ref": "github_token",
            "repository": "user/repo",
            "branch": "main",
            "files": [{"source": "a", "destination": "a"}],
            "commit_message": "ghp_SECRET",
        }
        self.assertEqual(validate_contract(c)["reason"], "INLINE_TOKEN_FORBIDDEN")

    def test_dry_run_publish(self):
        store = MapCredentialStore({"github_token": "secret-not-logged"})
        pub = GitHubPublisher(credentials=store)
        r = pub.publish(
            {
                "token_ref": "github_token",
                "repository": "user/repo",
                "branch": "main",
                "files": [{"source": "build/a.py", "destination": "ext/a.py"}],
                "commit_message": "Add capability",
            }
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "dry_run")

    def test_unresolved_ref(self):
        pub = GitHubPublisher(credentials=MapCredentialStore({}))
        r = pub.publish(
            {
                "token_ref": "missing",
                "repository": "u/r",
                "branch": "main",
                "files": [{"source": "a", "destination": "a"}],
                "commit_message": "x",
            }
        )
        self.assertEqual(r["reason"], "TOKEN_REF_UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
