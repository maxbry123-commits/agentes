"""Tests W-03 — ABI montable real"""
from __future__ import annotations

import unittest
from abi import ExtensionABI, EvidenceOutput, attach_to_wordflow_extension


class TestABI(unittest.TestCase):
    def test_register_list_unregister(self):
        abi = ExtensionABI()

        def dummy(params):
            return EvidenceOutput(ok=True, capability="dummy", evidence_hash="h", data={})

        abi.register("dummy", dummy)
        self.assertIn("dummy", abi.list_capabilities())
        abi.unregister("dummy")
        self.assertNotIn("dummy", abi.list_capabilities())

    def test_not_mounted_blocks_execute(self):
        abi = ExtensionABI()

        def dummy(params):
            return EvidenceOutput(ok=True, capability="dummy", evidence_hash="h", data={})

        abi.register("dummy", dummy)
        out = abi.execute("dummy")
        self.assertFalse(out.ok)
        self.assertEqual(out.error, "extension_not_mounted")

    def test_attach_and_ping(self):
        abi = ExtensionABI()
        abi = attach_to_wordflow_extension(abi)
        self.assertIn("ping", abi.list_capabilities())
        out = abi.execute("ping", {"k": "v"})
        self.assertTrue(out.ok)
        self.assertEqual(out.capability, "ping")
        self.assertTrue(out.evidence_hash.startswith("sha256:"))
        self.assertIsNone(out.error)

    def test_unknown_capability(self):
        abi = attach_to_wordflow_extension(ExtensionABI())
        out = abi.execute("no_existe")
        self.assertFalse(out.ok)
        self.assertIn("unknown_capability", out.error or "")

    def test_evidence_output_contract(self):
        out = EvidenceOutput(ok=True, capability="x", evidence_hash="sha256:abc", data={"a": 1})
        d = out.to_dict()
        self.assertEqual(d["ok"], True)
        self.assertEqual(d["capability"], "x")
        self.assertIn("evidence_hash", d)


if __name__ == "__main__":
    unittest.main()
