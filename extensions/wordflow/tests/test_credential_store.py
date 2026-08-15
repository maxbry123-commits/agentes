# -*- coding: utf-8 -*-
"""Tests C-18 credential_store — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.credential_store import (
    CredentialError,
    MapCredentialStore,
    assert_no_inline_secrets,
    resolve_required,
)


class TestCredentialStore(unittest.TestCase):
    def test_map_resolve(self):
        s = MapCredentialStore({"github_token": "secret"})
        self.assertEqual(resolve_required(s, "github_token"), "secret")

    def test_unresolved(self):
        s = MapCredentialStore()
        with self.assertRaises(CredentialError):
            resolve_required(s, "missing")

    def test_inline_forbidden(self):
        with self.assertRaises(CredentialError):
            assert_no_inline_secrets({"token": "ghp_abcdefghijklmnopqrstuvwxyz0123456789"})

    def test_clean_payload(self):
        r = assert_no_inline_secrets({"token_ref": "github_token"})
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()
