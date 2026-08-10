# -*- coding: utf-8 -*-
"""A-AUD-08 golden tests — A11 control-layer packet + edge cases."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.entrypoint import run_audit_fake  # noqa: E402
from audit_forensic.engine.repo_truth import FakeRepoTruth  # noqa: E402

BASE = "e36eba91b8100003eaedef88550f3ae706f1ef4a"
FINAL = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"
CI_RUN = "31354290850"

CL_PATHS = [
    "control-layer/control/fingerprint.py",
    "control-layer/control/threat.py",
    "control-layer/control/rules.py",
    "control-layer/control/graph.py",
    "control-layer/control/reverse.py",
    "control-layer/control/compiler.py",
    "control-layer/control/normalizer.py",
    "control-layer/sheriff/states.py",
    "control-layer/sheriff/decision.py",
    "control-layer/sheriff/gate.py",
    "control-layer/contracts/C00_governance.yaml",
    "control-layer/ficha.v2.json",
    "control-layer/manifest.yaml",
    "extensions/audit_forensic/schema_module.json",
]


def _a11_packet(**overrides):
    pkt = {
        "schema_version": "1.0",
        "task_id": "A11",
        "block_id": "control-layer-fase1",
        "claim_status": "COMPLETED",
        "repo": {
            "owner": "maxbry123-commits",
            "name": "agentes",
            "branch": "main",
            "base_commit": BASE,
            "final_commit": FINAL,
        },
        "files": {
            "added": list(CL_PATHS),
            "modified": [],
            "deleted": [],
        },
        "doc_anchors": [
            {"doc_id": "SALIDA4_FP", "section": "§14.2"},
            {"doc_id": "SALIDA4_RISK", "section": "§16"},
            {"doc_id": "SALIDA4_SHERIFF", "section": "§20"},
            {"doc_id": "C00", "section": "root"},
            {"doc_id": "PIPELINE20", "section": "motor"},
            {"doc_id": "AUDIT_SPEC", "section": "§4"},
        ],
        "tests": {
            "claimed_passed": 45,
            "claimed_total": 45,
            "ci_run_id": CI_RUN,
            "ci_url": f"https://github.com/maxbry123-commits/agentes/actions/runs/{CI_RUN}",
        },
        "loc_claim": {"added": 650, "deleted": 0, "net": 650},
    }
    pkt.update(overrides)
    return pkt


def _a11_fake():
    return FakeRepoTruth(
        commits={
            FINAL: {
                "sha": FINAL,
                "message": "A11 close control-layer fase1",
                "stats": {"additions": 650, "deletions": 0, "total": 650},
            }
        },
        tree={FINAL: set(CL_PATHS)},
        blobs={
            FINAL: {
                "extensions/audit_forensic/schema_module.json": "b9ec1ecfa8589ac3777ff7de8c324867f9a1ff6b",
            }
        },
        runs={
            CI_RUN: {
                "conclusion": "success",
                "head_sha": FINAL,
                "status": "completed",
                "html_url": f"https://github.com/maxbry123-commits/agentes/actions/runs/{CI_RUN}",
                "id": int(CI_RUN),
            }
        },
        jobs={CI_RUN: [{"id": 1, "name": "test", "conclusion": "success"}]},
    )


class TestGoldenA11(unittest.TestCase):
    def test_a11_confirmado(self):
        result = run_audit_fake(_a11_packet(), _a11_fake())
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"]["veredicto"], "CONFIRMADO")
        self.assertEqual(result["packet"]["task_id"], "A11")
        self.assertEqual(result["verdict"]["reason_codes"], [])

    def test_a11_phase_control_layer(self):
        result = run_audit_fake(
            _a11_packet(), _a11_fake(), phase="control-layer-fase1"
        )
        self.assertEqual(result["verdict"]["veredicto"], "CONFIRMADO")
        self.assertEqual(result["summaries"]["gaps"]["total"], 0)

    def test_edge_missing_ci_refuta(self):
        pkt = _a11_packet()
        pkt["tests"] = {"claimed_passed": 45, "claimed_total": 45}
        result = run_audit_fake(pkt, _a11_fake())
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")
        self.assertIn("CI_MISSING", result["verdict"]["reason_codes"])

    def test_edge_bad_commit_sha(self):
        pkt = _a11_packet()
        pkt["repo"] = dict(pkt["repo"])
        pkt["repo"]["final_commit"] = "notasha"
        result = run_audit_fake(pkt, _a11_fake())
        self.assertFalse(result["ok"])
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")
        self.assertEqual(result["error"]["reason_code"], "INVALID_COMMIT_SHA")

    def test_edge_empty_doc_anchors(self):
        pkt = _a11_packet(doc_anchors=[])
        result = run_audit_fake(pkt, _a11_fake())
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "MISSING_DOC_ANCHOR")

    def test_edge_ci_failed(self):
        fake = _a11_fake()
        fake.runs[CI_RUN] = {
            "conclusion": "failure",
            "head_sha": FINAL,
            "status": "completed",
        }
        result = run_audit_fake(_a11_packet(), fake)
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")
        self.assertIn("CI_FAILED", result["verdict"]["reason_codes"])

    def test_edge_paths_missing_refuta(self):
        result = run_audit_fake(_a11_packet(), FakeRepoTruth(tree={FINAL: set()}))
        self.assertEqual(result["verdict"]["veredicto"], "REFUTADO")
        self.assertTrue(
            result["summaries"]["gaps"]["has_critical_gap"]
            or result["summaries"]["coverage"]["critical_missing"]
        )

    def test_edge_deferred_avoids_gap(self):
        deferred = {
            "REQ-CL-FP-01",
            "REQ-CL-TH-01",
            "REQ-CL-SH-01",
            "REQ-CL-C00",
            "REQ-CL-CI-01",
            "REQ-AUD-PACKET",
        }
        result = run_audit_fake(
            _a11_packet(),
            FakeRepoTruth(tree={FINAL: set()}),
            deferred_ids=deferred,
        )
        self.assertIn(
            result["verdict"]["veredicto"], ("PARCIAL", "REFUTADO", "CONFIRMADO")
        )
        self.assertEqual(result["summaries"]["gaps"]["total"], 0)

    def test_matrices_populated(self):
        result = run_audit_fake(_a11_packet(), _a11_fake())
        for key in ("coverage", "literal", "contradiction", "gaps"):
            self.assertIn(key, result["matrices"])
        self.assertGreater(len(result["matrices"]["coverage"]), 0)
        self.assertGreater(len(result["matrices"]["literal"]), 0)


if __name__ == "__main__":
    unittest.main()
