# -*- coding: utf-8 -*-
"""A-AUD-04 tests — coverage + literal matrices."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.doc_truth import DocumentTruthStore  # noqa: E402
from audit_forensic.engine.matrix_coverage import (  # noqa: E402
    coverage_summary,
    run_coverage,
)
from audit_forensic.engine.matrix_literal import literal_summary, run_literal  # noqa: E402
from audit_forensic.engine.packet_normalizer import normalize_packet  # noqa: E402
from audit_forensic.engine.repo_truth import FakeRepoTruth  # noqa: E402
from audit_forensic.engine.requirements_loader import load_requirements  # noqa: E402

SHA = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"
SEED_DOC = Path(__file__).resolve().parents[1] / "store" / "document_truth_seed.yaml"
SEED_REQ = Path(__file__).resolve().parents[1] / "requirements" / "phase_seed.yaml"


def _packet(**kw):
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
        ],
        "tests": {
            "claimed_passed": 45,
            "claimed_total": 45,
            "ci_run_id": "31354290850",
        },
    }
    base.update(kw)
    return normalize_packet(base)


def _repo():
    paths = {
        "control-layer/control/fingerprint.py",
        "control-layer/control/threat.py",
        "control-layer/sheriff/states.py",
        "control-layer/contracts/C00_governance.yaml",
        "extensions/audit_forensic/schema_module.json",
    }
    return FakeRepoTruth(
        tree={SHA: paths},
        blobs={SHA: {"extensions/audit_forensic/schema_module.json": "abc123"}},
        runs={
            "31354290850": {
                "conclusion": "success",
                "head_sha": SHA,
                "status": "completed",
                "html_url": "https://example/run",
            }
        },
    )


class TestMatrices(unittest.TestCase):
    def setUp(self):
        self.reqs = load_requirements(SEED_REQ)
        self.docs = DocumentTruthStore.from_seed(SEED_DOC)
        self.repo = _repo()
        self.packet = _packet()

    def test_coverage_present(self):
        rows = run_coverage(self.reqs, self.packet, self.repo)
        summary = coverage_summary(rows)
        self.assertGreater(summary["counts"].get("PRESENT", 0), 0)
        self.assertEqual(summary["critical_missing"], [])

    def test_coverage_missing_path(self):
        repo = FakeRepoTruth(tree={SHA: set()})
        rows = run_coverage(self.reqs, self.packet, repo)
        summary = coverage_summary(rows)
        bad = summary["counts"].get("MISSING", 0) + summary["counts"].get(
            "NO_VERIFICADO", 0
        )
        self.assertGreater(bad, 0)
        self.assertGreater(len(summary["critical_missing"]), 0)

    def test_coverage_deferred(self):
        rows = run_coverage(
            self.reqs, self.packet, self.repo, deferred_ids={"REQ-CL-CI-01"}
        )
        statuses = {r["requirement_id"]: r["status"] for r in rows if r["requirement_id"]}
        self.assertEqual(statuses.get("REQ-CL-CI-01"), "DEFERRED")

    def test_literal_anchors_pass(self):
        rows = run_literal(self.reqs, self.packet, self.repo, self.docs)
        anchor_rows = [r for r in rows if r["check"] == "doc_anchor"]
        self.assertTrue(all(r["status"] == "PASS" for r in anchor_rows))

    def test_literal_path_and_ci(self):
        rows = run_literal(self.reqs, self.packet, self.repo, self.docs)
        summary = literal_summary(rows)
        self.assertEqual(summary["fails"], [])
        self.assertGreater(summary["counts"].get("PASS", 0), 0)

    def test_literal_ci_missing(self):
        pkt = _packet(tests={"claimed_passed": 5, "claimed_total": 5})
        rows = run_literal(self.reqs, pkt, self.repo, self.docs)
        ci_rows = [r for r in rows if r["check"] == "ci_success"]
        self.assertTrue(any(r["status"] == "FAIL" for r in ci_rows))

    def test_literal_bad_anchor(self):
        pkt = _packet(doc_anchors=[{"doc_id": "NOPE"}])
        rows = run_literal(self.reqs, pkt, self.repo, self.docs)
        bad = [r for r in rows if r["check"] == "doc_anchor"]
        self.assertTrue(any(r["status"] == "FAIL" for r in bad))


if __name__ == "__main__":
    unittest.main()
