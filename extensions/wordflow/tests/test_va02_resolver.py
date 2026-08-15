"""VA-02 — AccountResolver DENY rules."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow.accounts import (
    AccountRegistry,
    AccountRecord,
    AccountResolver,
    WorkspaceRepo,
)


class TestVA02(unittest.TestCase):
    def setUp(self):
        self.reg = AccountRegistry()
        self.reg.register(
            AccountRecord(
                "github:work",
                "github",
                "secret://github/work",
                allowed_repositories=("org/allowed",),
                policy={"can_read": True, "can_write": True, "can_deploy": False},
            )
        )
        self.res = AccountResolver(self.reg)

    def test_allow_listed_repo(self):
        r = self.res.resolve(
            WorkspaceRepo("W1", "github", "org", "allowed", account_id="github:work"),
            need_write=True,
        )
        self.assertEqual(r.decision, "ALLOW")
        self.assertEqual(r.credential_ref, "secret://github/work")

    def test_deny_repo_not_allowed(self):
        r = self.res.resolve(
            WorkspaceRepo("W1", "github", "org", "other", account_id="github:work"),
            need_write=True,
        )
        self.assertEqual(r.decision, "DENY")
        self.assertEqual(r.reason, "repository_not_allowed")

    def test_deny_deploy_policy(self):
        r = self.res.resolve(
            WorkspaceRepo("W1", "github", "org", "allowed", account_id="github:work"),
            need_deploy=True,
        )
        self.assertEqual(r.decision, "DENY")
        self.assertEqual(r.reason, "policy_can_deploy_false")

    def test_deny_unknown_account(self):
        r = self.res.resolve(
            WorkspaceRepo("W1", "github", "org", "allowed", account_id="github:missing")
        )
        self.assertEqual(r.decision, "DENY")
        self.assertEqual(r.reason, "account_not_registered")


if __name__ == "__main__":
    unittest.main()
