# -*- coding: utf-8 -*-
"""A-DEP-01 tests — GitHub Publisher."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from github_publisher.engine.publisher import (  # noqa: E402
    FakeGitHubPort,
    PublishError,
    normalize_publish,
    run_publish,
)


def _req(**kw):
    b = {
        "schema_version": "1.0",
        "token_ref": "github_token",
        "repository": "maxbry123-commits/agentes",
        "branch": "main",
        "files": [
            {
                "source": "build/a.py",
                "destination": "extensions/demo/a.py",
                "content": "print('ok')\n",
            }
        ],
        "commit_message": "Add demo capability",
    }
    b.update(kw)
    return b


class TestPublisher(unittest.TestCase):
    def test_normalize(self):
        p = normalize_publish(_req())
        self.assertEqual(p["token_ref"], "github_token")
        self.assertEqual(p["llm_control"], "DENY")

    def test_raw_token_forbidden(self):
        with self.assertRaises(PublishError) as ctx:
            normalize_publish(_req(token="ghp_xxx"))
        self.assertEqual(ctx.exception.reason_code, "RAW_TOKEN_FORBIDDEN")

    def test_token_ref_looks_secret(self):
        with self.assertRaises(PublishError) as ctx:
            normalize_publish(_req(token_ref="ghp_abc123"))
        self.assertEqual(ctx.exception.reason_code, "TOKEN_REF_LOOKS_LIKE_SECRET")

    def test_invalid_repo(self):
        with self.assertRaises(PublishError) as ctx:
            normalize_publish(_req(repository="nonsplash"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_REPOSITORY")

    def test_publish_ok(self):
        port = FakeGitHubPort()
        r = run_publish(
            _req(),
            port=port,
            credential_store={"github_token": "fake-token-value"},
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "SUCCESS")
        self.assertEqual(r["files_count"], 1)
        self.assertNotIn("token", r)
        self.assertEqual(len(port.commits), 1)

    def test_missing_token_ref(self):
        r = run_publish(_req(), port=FakeGitHubPort(), credential_store={})
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "TOKEN_REF_NOT_FOUND")

    def test_secret_in_content(self):
        with self.assertRaises(PublishError) as ctx:
            normalize_publish(
                _req(
                    files=[{
                        "source": "a",
                        "destination": "b",
                        "content": "token = ghp_xxx",
                    }]
                )
            )
        self.assertEqual(ctx.exception.reason_code, "SECRET_IN_CONTENT")


if __name__ == "__main__":
    unittest.main()
