# -*- coding: utf-8 -*-
"""A-WF-09 integration — wordflow produces evidence stub → audit consumes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.entrypoint import run_audit_fake  # noqa: E402
from audit_forensic.engine.repo_truth import FakeRepoTruth  # noqa: E402
from wordflow.engine.entrypoint import run_wordflow  # noqa: E402
from wordflow.engine.state_store import StateStore  # noqa: E402

SHA = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"


def _wf_raw():
    return {
        "schema_version": "1.0",
        "block_id": "IB-INT-01",
        "source_type": "chat",
        "raw_text": "Implementar control-layer/control/fingerprint.py ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "doc_refs": [
            {"doc_id": "SALIDA4_FP", "section": "§14.2"},
            {"doc_id": "PIPELINE20", "section": "motor"},
            {"doc_id": "AUDIT_SPEC", "section": "§4"},
        ],
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }


class TestIntegration(unittest.TestCase):
    def test_wordflow_to_audit_packet(self):
        wf = run_wordflow(_wf_raw())
        self.assertTrue(wf["ok"])
        packet = {
            "schema_version": "1.0",
            "task_id": wf["block_id"],
            "claim_status": "PARTIAL",
            "repo": {
                "owner": "maxbry123-commits",
                "name": "agentes",
                "branch": "main",
                "base_commit": "e36eba91b8100003eaedef88550f3ae706f1ef4a",
                "final_commit": SHA,
            },
            "files": {
                "added": ["control-layer/control/fingerprint.py"],
                "modified": [],
                "deleted": [],
            },
            "doc_anchors": _wf_raw()["doc_refs"],
            "tests": {"claimed_passed": 0, "claimed_total": 0},
        }
        fake = FakeRepoTruth(
            commits={SHA: {"sha": SHA, "message": "x", "stats": {}}},
            tree={SHA: {"control-layer/control/fingerprint.py"}},
        )
        audit = run_audit_fake(packet, fake)
        self.assertTrue(audit["ok"])
        self.assertIn(
            audit["verdict"]["veredicto"], ("CONFIRMADO", "PARCIAL", "REFUTADO")
        )

    def test_state_store_checkpoint(self):
        store = StateStore()
        wf = run_wordflow(_wf_raw())
        key = store.checkpoint(
            wf["block_id"], {"status": wf["status"], "hash": wf["block_hash"]}
        )
        loaded = store.load_checkpoint(wf["block_id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["status"], "COMPLETED")
        self.assertTrue(key.startswith("ckpt:"))

    def test_state_store_persist(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            store = StateStore(path)
            store.set("k", 1)
            store.checkpoint("B1", {"x": 2})
            store2 = StateStore(path)
            self.assertEqual(store2.get("k"), 1)
            self.assertEqual(store2.load_checkpoint("B1")["x"], 2)


if __name__ == "__main__":
    unittest.main()
