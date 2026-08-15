"""VA-01 — AccountRegistry."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow.accounts import AccountRegistry, AccountRecord


class TestVA01(unittest.TestCase):
    def test_register_and_list(self):
        reg = AccountRegistry()
        reg.register(
            AccountRecord(
                account_id="github:work",
                provider="github",
                credential_ref="secret://github/work",
                allowed_repositories=("maxbry123-commits/agentes",),
                policy={"can_read": True, "can_write": True, "can_deploy": True},
            )
        )
        self.assertEqual(reg.list_ids(), ["github:work"])
        self.assertEqual(reg.get("github:work").default_branch, "main")

    def test_raw_token_forbidden(self):
        reg = AccountRegistry()
        with self.assertRaises(ValueError):
            reg.register(
                AccountRecord(
                    account_id="bad",
                    provider="github",
                    credential_ref="ghp_THISISNOTALLOWED",
                )
            )

    def test_find_for_repo(self):
        reg = AccountRegistry()
        reg.register(
            AccountRecord(
                "github:a",
                "github",
                "secret://a",
                allowed_repositories=("org/repo-a",),
            )
        )
        reg.register(
            AccountRecord("github:b", "github", "secret://b", allowed_repositories=())
        )
        hits = reg.find_for_repo("org/repo-a")
        ids = {h.account_id for h in hits}
        self.assertIn("github:a", ids)
        self.assertIn("github:b", ids)


if __name__ == "__main__":
    unittest.main()
