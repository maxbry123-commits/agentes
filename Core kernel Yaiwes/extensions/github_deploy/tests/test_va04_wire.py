"""VA-04 — AccountResolver ALLOW → FakeGitDataAPIPort deploy."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow.accounts import AccountRegistry, AccountRecord, AccountResolver, WorkspaceRepo
from github_deploy.git_data_port import FakeGitDataAPIPort, FileChange, build_git_data_port


class TestVA04(unittest.TestCase):
    def test_allow_then_fake_deploy(self):
        reg = AccountRegistry()
        reg.register(
            AccountRecord(
                "github:work",
                "github",
                "secret://github/work",
                allowed_repositories=("maxbry123-commits/agentes",),
                policy={"can_read": True, "can_write": True, "can_deploy": True},
            )
        )
        resolver = AccountResolver(reg)
        decision = resolver.resolve(
            WorkspaceRepo(
                "W1",
                "github",
                "maxbry123-commits",
                "agentes",
                account_id="github:work",
            ),
            need_write=True,
            need_deploy=True,
        )
        self.assertEqual(decision.decision, "ALLOW")
        port = FakeGitDataAPIPort()
        res = port.deploy(
            "maxbry123-commits",
            "agentes",
            "main",
            [FileChange("PIPELINE/note.md", b"# ok\n")],
            "VA-04 test",
        )
        self.assertEqual(res.status, "DRY_RUN")
        self.assertEqual(decision.credential_ref, "secret://github/work")

    def test_deny_skips_deploy(self):
        reg = AccountRegistry()
        reg.register(
            AccountRecord(
                "github:ro",
                "github",
                "secret://ro",
                allowed_repositories=("org/x",),
                policy={"can_read": True, "can_write": False, "can_deploy": False},
            )
        )
        r = AccountResolver(reg).resolve(
            WorkspaceRepo("W", "github", "org", "x", account_id="github:ro"),
            need_write=True,
        )
        self.assertEqual(r.decision, "DENY")

    def test_build_port_fake(self):
        self.assertIsInstance(build_git_data_port(dry_run=True), FakeGitDataAPIPort)


if __name__ == "__main__":
    unittest.main()
