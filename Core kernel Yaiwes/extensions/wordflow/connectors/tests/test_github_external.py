# -*- coding: utf-8 -*-
import os
import unittest

from extensions.wordflow.connectors.github_external import (
    ExternalGitHubConfig,
    resolve_credential,
    CredentialResolutionError,
)


class TestResolveCredential(unittest.TestCase):
    def test_rejects_raw_pat(self):
        with self.assertRaises(CredentialResolutionError):
            resolve_credential("ghp_FORBIDDEN_EXAMPLE")

    def test_env_ref(self):
        os.environ["TEST_EXT_GH_TOKEN"] = "dummy-not-a-real-token"
        try:
            self.assertEqual(
                resolve_credential("env:TEST_EXT_GH_TOKEN"),
                "dummy-not-a-real-token",
            )
        finally:
            del os.environ["TEST_EXT_GH_TOKEN"]

    def test_config_frozen(self):
        c = ExternalGitHubConfig(
            owner="abc1tienda-web",
            repo="demo",
            credential_ref="env:TEST_EXT_GH_TOKEN",
        )
        self.assertEqual(c.owner, "abc1tienda-web")


if __name__ == "__main__":
    unittest.main()
