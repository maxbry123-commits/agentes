# -*- coding: utf-8 -*-
"""Tests C-10 GitHubDeployer — offline FakePort, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.github_deploy.deployer import FakeGitDataPort, GitHubDeployer, load_deploy_config
from extensions.wordflow.engine.github_publisher import MapCredentialStore


def _contract(**over):
    base = {
        "token_ref": "github_token",
        "repository": "maxbry123-commits/agentes",
        "branch": "main",
        "files": [{"source": "build/a.py", "destination": "extensions/demo/a.py"}],
        "commit_message": "Add demo",
        "expected_head": "0" * 40,
        "content_map": {"build/a.py": "print(1)\n"},
    }
    base.update(over)
    return base


class TestDeployer(unittest.TestCase):
    def test_fake_deploy_ok(self):
        port = FakeGitDataPort(head_sha="0" * 40)
        d = GitHubDeployer(
            credentials=MapCredentialStore({"github_token": "secret"}),
            port=port,
            dry_run=False,
            config=load_deploy_config(),
        )
        r = d.deploy(_contract())
        self.assertTrue(r["ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_protected_path(self):
        d = GitHubDeployer(
            credentials=MapCredentialStore({"github_token": "secret"}),
            port=FakeGitDataPort(),
            dry_run=False,
        )
        r = d.deploy(_contract(files=[{
            "source": "x.yml",
            "destination": ".github/workflows/x.yml",
        }]))
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "PROTECTED_PATH")

    def test_missing_expected_head(self):
        d = GitHubDeployer(
            credentials=MapCredentialStore({"github_token": "secret"}),
            port=FakeGitDataPort(),
            dry_run=False,
        )
        c = _contract()
        del c["expected_head"]
        r = d.deploy(c)
        self.assertEqual(r["reason"], "MISSING_EXPECTED_HEAD")

    def test_head_conflict(self):
        d = GitHubDeployer(
            credentials=MapCredentialStore({"github_token": "secret"}),
            port=FakeGitDataPort(head_sha="1" * 40),
            dry_run=False,
        )
        r = d.deploy(_contract(expected_head="0" * 40))
        self.assertEqual(r["reason"], "HEAD_CONFLICT")

    def test_force_push_denied(self):
        d = GitHubDeployer(
            credentials=MapCredentialStore({"github_token": "secret"}),
            port=FakeGitDataPort(),
            dry_run=False,
        )
        r = d.deploy(_contract(force_push=True))
        self.assertEqual(r["reason"], "FORCE_PUSH_DENIED")


if __name__ == "__main__":
    unittest.main()
