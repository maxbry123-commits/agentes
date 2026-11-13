# -*- coding: utf-8 -*-
"""A-AUD-01 tests — EvidencePacket normalizer. Offline, 0% LLM."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.packet_normalizer import (  # noqa: E402
    PacketError,
    normalize_packet,
    validate_or_reason,
)

VALID_SHA_A = "e36eba91b8100003eaedef88550f3ae706f1ef4a"
VALID_SHA_B = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"


def _base(**overrides):
    pkt = {
        "schema_version": "1.0",
        "task_id": "A-AUD-01",
        "claim_status": "COMPLETED",
        "repo": {
            "owner": "maxbry123-commits",
            "name": "agentes",
            "branch": "main",
            "base_commit": VALID_SHA_A,
            "final_commit": VALID_SHA_B,
        },
        "files": {"added": ["a.py"], "modified": [], "deleted": []},
        "doc_anchors": [{"doc_id": "AUDIT_SPEC", "section": "§4"}],
        "tests": {"claimed_passed": 0, "claimed_total": 0},
    }
    pkt.update(overrides)
    return pkt


class TestPacketNormalizer(unittest.TestCase):
    def test_valid_packet(self):
        out = normalize_packet(_base())
        self.assertEqual(out["schema_version"], "1.0")
        self.assertEqual(out["task_id"], "A-AUD-01")
        self.assertIn("packet_hash", out)
        self.assertEqual(len(out["packet_hash"]), 64)
        self.assertFalse(out["flags"]["ci_missing"])

    def test_missing_packet(self):
        ok, err = validate_or_reason(None)
        self.assertFalse(ok)
        self.assertEqual(err["reason_code"], "MISSING_PACKET")

    def test_missing_task_id(self):
        p = _base()
        del p["task_id"]
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(p)
        self.assertEqual(ctx.exception.reason_code, "MISSING_FIELD")

    def test_bad_claim_status(self):
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(_base(claim_status="DONE"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_PACKET_SCHEMA")

    def test_bad_commit_sha(self):
        p = _base()
        p["repo"]["final_commit"] = "not-a-sha"
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(p)
        self.assertEqual(ctx.exception.reason_code, "INVALID_COMMIT_SHA")

    def test_empty_doc_anchors(self):
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(_base(doc_anchors=[]))
        self.assertEqual(ctx.exception.reason_code, "MISSING_DOC_ANCHOR")

    def test_ci_missing_flag(self):
        p = _base()
        p["tests"] = {"claimed_passed": 5, "claimed_total": 5}
        out = normalize_packet(p)
        self.assertTrue(out["flags"]["ci_missing"])
        self.assertEqual(out["flags"]["reason_ci"], "CI_MISSING")

    def test_ci_present_ok(self):
        p = _base()
        p["tests"] = {
            "claimed_passed": 5,
            "claimed_total": 5,
            "ci_run_id": "31354290850",
        }
        out = normalize_packet(p)
        self.assertFalse(out["flags"]["ci_missing"])

    def test_secret_in_meta_rejected(self):
        p = _base()
        p["meta"] = {"api_key": "sk-secret"}
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(p)
        self.assertEqual(ctx.exception.reason_code, "SECRET_IN_INPUT")

    def test_files_keys_required(self):
        p = _base()
        p["files"] = {"added": []}
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(p)
        self.assertEqual(ctx.exception.reason_code, "MISSING_FIELD")

    def test_schema_version_mismatch(self):
        with self.assertRaises(PacketError) as ctx:
            normalize_packet(_base(schema_version="2.0"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_PACKET_SCHEMA")

    def test_packet_hash_stable(self):
        a = normalize_packet(_base())
        b = normalize_packet(_base())
        self.assertEqual(a["packet_hash"], b["packet_hash"])


if __name__ == "__main__":
    unittest.main()
