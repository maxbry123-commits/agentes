# -*- coding: utf-8 -*-
"""A-AUD-07 tests — entrypoint orchestrator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.entrypoint import run_audit, run_audit_fake  # noqa: E402
from audit_forensic.engine.repo_truth import FakeRepoTruth  # noqa: E402

SHA = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"


def _raw(**kw):
    base = {
        "schema_version": "1.0",
        "task_id": "A11",
        "claim_status": "COMPLETED",
        "repo": {
            "owner": "maxbry123-commits",
            "name": "agentes",
            "branch": "main",
            "base_commit": "e36eba91b8100003eaedef88550f3ae706f1ef4a",
            "final_commit": SHA,
        },
        "files": {
            "added": [
                "control-layer/control/fingerprint.py",
                "control-layer/control/threat.py",
                "control-layer/sheriff/states.py",
                "control-layer/contracts/C00_governance.yaml",
                "extensions/audit_forensic/schema_module.json",
            ],
            "modified": [],
            "deleted": [],
        },
        "doc_anchors": [
            {"doc_id": "SALIDA4_FP", "section": "§14.2"},
            {"doc_id": "PIPELINE20", "section": "motor"},
            {"doc_id": "AUDIT_SPEC", "section": "§4"},
        ],
        "tests": {
            "claimed_passed": 45,
            "claimed_total": 45,
            "ci_run_id": "31354290850",
        },
    }
    base.update(kw)
    return base


def _fake_full():
    paths = {
        "control-layer/control/fingerprint.py",
        "control-layer/control/threat.py",
        "control-layer/sheriff/states.py",
        "control-layer/contracts/C00_governance.yaml",
        "extensions/audit_forensic/schema_module.json",
    }
    return FakeRepoTruth(
        commits={
            SHA: {
                "sha": SHA,
                "message": "A11",
                "stats": {"additions": 100, "deletions": 10, "total": 110},
            }
        },
        tree={SHA: paths},
        runs={
            "31354290850": {
                "conclusion": "success",
                "head_sha": SHA,
                "status": "completed",
            }
        },
    )


class TestEntrypoint(unittest.TestCase):
    def test_confirmado_happy(self):
        result = run_audit_fake(_raw(), _fake_full())
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"]["veredicto"], "CONFIRMADO")
        self.assertIn("matrices", result)
        self.assertIn("coverage", result["matrices"])

    def test_invalid_packet(self):
        result = run_audit_fake(None, FakeRepoTruth())
        self.assertFalse(result["ok"])
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")
        self.assertEqual(result["error"]["reason_code"], "MISSING_PACKET")

    def test_refutado_missing_paths(self):
        result = run_audit_fake(_raw(), FakeRepoTruth(tree={SHA: set()}))
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")

    def test_phase_filter(self):
        result = run_audit_fake(_raw(), _fake_full(), phase="audit-fase1")
        self.assertTrue(result["ok"])
        gaps = result["matrices"]["gaps"]
        self.assertIsInstance(gaps, list)

    def test_packet_hash_present(self):
        result = run_audit_fake(_raw(), _fake_full())
        self.assertIsNotNone(result["packet"]["packet_hash"])


if __name__ == "__main__":
    unittest.main()
