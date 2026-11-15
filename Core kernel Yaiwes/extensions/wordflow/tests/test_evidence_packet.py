# -*- coding: utf-8 -*-
"""Tests C-07 EvidencePacket — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.evidence_packet import (
    EvidencePacketError,
    build_evidence_packet,
    chain_packets,
    verify_evidence_packet,
)


class TestEvidencePacket(unittest.TestCase):
    def test_build_and_verify(self):
        p = build_evidence_packet(
            task_id="C-07",
            claim_status="COMPLETED",
            paths=[{"path": "a.py", "blob_sha": "x"}],
            tests={"passed": 3, "failed": 0},
            doc_anchors=["G-CODE-07"],
            commit_sha="abc",
        )
        v = verify_evidence_packet(p)
        self.assertTrue(v["ok"])
        self.assertEqual(p["llm_control"], "DENY")

    def test_tamper_detected(self):
        p = build_evidence_packet(task_id="C-07", claim_status="PARTIAL")
        p["claim_status"] = "COMPLETED"
        self.assertFalse(verify_evidence_packet(p)["ok"])

    def test_chain(self):
        raw = [
            {"task_id": "A", "claim_status": "COMPLETED"},
            {"task_id": "B", "claim_status": "PARTIAL"},
        ]
        c = chain_packets(raw)
        self.assertEqual(c["count"], 2)
        self.assertEqual(c["packets"][1]["parent_hash"], c["packets"][0]["packet_hash"])

    def test_bad_status(self):
        with self.assertRaises(EvidencePacketError):
            build_evidence_packet(task_id="x", claim_status="DONE")


if __name__ == "__main__":
    unittest.main()
