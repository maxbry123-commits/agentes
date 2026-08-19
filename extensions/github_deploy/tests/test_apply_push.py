# -*- coding: utf-8 -*-
"""apply_and_push — offline FakePort, 0% LLM, account B."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.github_deploy.apply_push import apply_and_push
from extensions.github_deploy.git_data_port import FakeGitDataAPIPort
from extensions.github_deploy.hf_port import FakeHfPort
from extensions.wordflow.accounts.registry import AccountRecord, AccountRegistry
from extensions.wordflow.engine.github_publisher import MapCredentialStore


def _registry() -> AccountRegistry:
    r = AccountRegistry()
    r.register(
        AccountRecord(
            account_id="github_b",
            provider="github",
            credential_ref="env:GITHUB_B_TOKEN",
            allowed_repositories=(),
            policy={"can_read": True, "can_write": True, "can_deploy": True},
        )
    )
    r.register(
        AccountRecord(
            account_id="hf_b",
            provider="huggingface",
            credential_ref="env:HF_TOKEN",
            allowed_repositories=(),
            policy={"can_read": True, "can_write": True, "can_deploy": True},
        )
    )
    return r


class TestApplyPush(unittest.TestCase):
    def test_github_b_any_repo_dry_run(self):
        port = FakeGitDataAPIPort()
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td) / "evidence.json"
            out = apply_and_push(
                dest={"provider": "github", "owner": "other-user", "repo": "any-lib", "branch": "main"},
                files=[{"path": "pkg/a.py", "content": "print(1)\n"}],
                account_id="github_b",
                token_ref="env:GITHUB_B_TOKEN",
                commit_message="apply a",
                port=port,
                credentials=MapCredentialStore({"env:GITHUB_B_TOKEN": "secret"}),
                registry=_registry(),
                evidence_path=ev,
            )
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "DRY_RUN")
        self.assertFalse(out["published"])
        self.assertTrue(out["git_apply"])
        self.assertEqual(out["account_id"], "github_b")
        self.assertTrue(ev.is_file())
        self.assertEqual(port.calls[0]["owner"], "other-user")

    def test_protected_hold(self):
        out = apply_and_push(
            dest={"owner": "x", "repo": "y"},
            files=[{"path": ".github/workflows/x.yml", "content": "a: 1\n"}],
            account_id="github_b",
            token_ref="env:GITHUB_B_TOKEN",
            credentials=MapCredentialStore({"env:GITHUB_B_TOKEN": "secret"}),
            registry=_registry(),
            port=FakeGitDataAPIPort(),
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "PROTECTED_PATH")

    def test_force_denied(self):
        out = apply_and_push(
            dest={"owner": "x", "repo": "y"},
            files=[{"path": "a.py", "content": "x"}],
            account_id="github_b",
            token_ref="env:GITHUB_B_TOKEN",
            force=True,
            credentials=MapCredentialStore({"env:GITHUB_B_TOKEN": "secret"}),
            registry=_registry(),
            port=FakeGitDataAPIPort(),
        )
        self.assertEqual(out["reason"], "FORCE_PUSH_DENIED")

    def test_raw_token_forbidden(self):
        out = apply_and_push(
            dest={"owner": "x", "repo": "y"},
            files=[{"path": "a.py", "content": "x"}],
            account_id="github_b",
            token_ref="ghp_NOTAREALTOKEN",
            registry=_registry(),
            port=FakeGitDataAPIPort(),
        )
        self.assertFalse(out["ok"])
        self.assertIn(out["reason"], {"RAW_TOKEN_FORBIDDEN", "TOKEN_REF_UNRESOLVED"})

    def test_account_required(self):
        out = apply_and_push(
            dest={"owner": "x", "repo": "y"},
            files=[{"path": "a.py", "content": "x"}],
            account_id=None,
        )
        self.assertEqual(out["reason"], "ACCOUNT_REQUIRED")

    def test_huggingface_dry_run(self):
        out = apply_and_push(
            dest={"provider": "huggingface", "owner": "user", "repo": "model"},
            files=[{"path": "README.md", "content": "# m\n"}],
            account_id="hf_b",
            token_ref="env:HF_TOKEN",
            credentials=MapCredentialStore({"env:HF_TOKEN": "secret"}),
            registry=_registry(),
            port=FakeHfPort(),
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "DRY_RUN")
        self.assertEqual(out.get("provider") or out["evidence"]["provider"], "huggingface")


if __name__ == "__main__":
    unittest.main()
