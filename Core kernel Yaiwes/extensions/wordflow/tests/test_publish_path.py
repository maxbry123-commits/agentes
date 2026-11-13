# -*- coding: utf-8 -*-
"""Tests T43 publish path."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.publish_path import publish_after_mission


class TestPublishPath(unittest.TestCase):
    def test_publish_ok(self):
        contract = {
            "token_ref": "github_token",
            "repository": "user/repo",
            "branch": "main",
            "files": [{"source": "build/a.py", "destination": "a.py"}],
            "commit_message": "Add a",
        }
        r = publish_after_mission(
            "objective: publish capability\nsuccess: dry_run\nconstraint: 0% LLM\n",
            contract,
            credential_map={"github_token": "secret"},
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["publish"]["mode"], "dry_run")

    def test_sheriff_blocks_publish(self):
        contract = {
            "token_ref": "github_token",
            "repository": "user/repo",
            "branch": "main",
            "files": [{"source": "a", "destination": "a"}],
            "commit_message": "x",
        }
        r = publish_after_mission(
            "objective: blocked publish\nsuccess: no\n",
            contract,
            risk_score=9,
            band="quarantine",
            credential_map={"github_token": "secret"},
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "sheriff")


if __name__ == "__main__":
    unittest.main()
