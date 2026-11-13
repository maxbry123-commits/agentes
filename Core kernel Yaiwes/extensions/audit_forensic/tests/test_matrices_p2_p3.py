# -*- coding: utf-8 -*-
"""A-AUD-05 tests — contradiction + gaps matrices."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.matrix_contradiction import (  # noqa: E402
    contradiction_summary,
    run_contradiction,
)
from audit_forensic.engine.matrix_coverage import run_coverage  # noqa: E402
from audit_forensic.engine.matrix_gaps import gaps_summary, run_gaps  # noqa: E402
from audit_forensic.engine.packet_normalizer import normalize_packet  # noqa: E402
from audit_forensic.engine.repo_truth import FakeRepoTruth  # noqa: E402
from audit_forensic.engine.requirements_loader import load_requirements  # noqa: E402

SHA = "4d9c112c4086ef731a808e20b19b6b2c6b1a643a"
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
            "added": ["control-layer/control/fingerprint.py"],
            "modified": [],
            "deleted": [],
        },
        "doc_anchors": [{"doc_id": "SALIDA4_FP", "section": "§14.2"}],
        "tests": {
            "claimed_passed": 10,
            "claimed_total": 10,
            "ci_run_id": "31354290850",
        },
        "loc_claim": {"added": 100, "deleted": 10, "net": 90},
    }
    base.update(kw)
    return normalize_packet(base)


def _repo_ok():
    return FakeRepoTruth(
        commits={
            SHA: {
                "sha": SHA,
                "message": "ok",
                "stats": {"additions": 100, "deletions": 10, "total": 110},
            }
        },
        tree={SHA: {"control-layer/control/fingerprint.py"}},
        runs={
            "31354290850": {
                "conclusion": "success",
                "head_sha": SHA,
                "status": "completed",
            }
        },
    )


class TestP2P3(unittest.TestCase):
    def test_contradiction_pass(self):
        rows = run_contradiction(_packet(), _repo_ok())
        s = contradiction_summary(rows)
        self.assertEqual(s["fail_count"], 0)

    def test_contradiction_files_missing(self):
        repo = FakeRepoTruth(
            commits={SHA: {"sha": SHA, "message": "x", "stats": {}}},
            tree={SHA: set()},
            runs={"31354290850": {"conclusion": "success", "head_sha": SHA}},
        )
        rows = run_contradiction(_packet(), repo)
        pairs = {r["pair"]: r for r in rows}
        self.assertEqual(pairs["files_added_vs_tree"]["status"], "FAIL")

    def test_contradiction_ci_fail(self):
        repo = FakeRepoTruth(
            commits={SHA: {"sha": SHA, "message": "x", "stats": {}}},
            tree={SHA: {"control-layer/control/fingerprint.py"}},
            runs={"31354290850": {"conclusion": "failure", "head_sha": SHA}},
        )
        rows = run_contradiction(_packet(), repo)
        pairs = {r["pair"]: r for r in rows}
        self.assertEqual(pairs["tests_vs_ci"]["status"], "FAIL")
        self.assertEqual(pairs["tests_vs_ci"]["reason_code"], "CI_FAILED")

    def test_contradiction_loc_mismatch(self):
        repo = FakeRepoTruth(
            commits={
                SHA: {
                    "sha": SHA,
                    "message": "x",
                    "stats": {"additions": 50, "deletions": 5, "total": 55},
                }
            },
            tree={SHA: {"control-layer/control/fingerprint.py"}},
            runs={"31354290850": {"conclusion": "success", "head_sha": SHA}},
        )
        rows = run_contradiction(_packet(), repo)
        pairs = {r["pair"]: r for r in rows}
        self.assertEqual(pairs["loc_vs_stats"]["status"], "FAIL")

    def test_gaps_none_when_present(self):
        reqs = load_requirements(SEED_REQ, phase="control-layer-fase1")
        repo = FakeRepoTruth(
            tree={
                SHA: {
                    "control-layer/control/fingerprint.py",
                    "control-layer/control/threat.py",
                    "control-layer/sheriff/states.py",
                    "control-layer/contracts/C00_governance.yaml",
                }
            },
            runs={"31354290850": {"conclusion": "success", "head_sha": SHA}},
        )
        pkt = _packet(
            files={
                "added": [
                    "control-layer/control/fingerprint.py",
                    "control-layer/control/threat.py",
                    "control-layer/sheriff/states.py",
                    "control-layer/contracts/C00_governance.yaml",
                ],
                "modified": [],
                "deleted": [],
            }
        )
        cov = run_coverage(reqs, pkt, repo)
        gaps = run_gaps(cov, phase="control-layer-fase1")
        s = gaps_summary(gaps)
        self.assertIsInstance(s["total"], int)

    def test_gaps_critical(self):
        reqs = load_requirements(SEED_REQ, phase="control-layer-fase1")
        repo = FakeRepoTruth(tree={SHA: set()})
        cov = run_coverage(reqs, _packet(), repo)
        gaps = run_gaps(cov, phase="control-layer-fase1")
        s = gaps_summary(gaps)
        self.assertTrue(s["has_critical_gap"])
        self.assertGreater(s["critical_count"], 0)

    def test_gaps_deferred_excluded(self):
        reqs = load_requirements(SEED_REQ, phase="control-layer-fase1")
        repo = FakeRepoTruth(tree={SHA: set()})
        deferred = {
            "REQ-CL-FP-01",
            "REQ-CL-TH-01",
            "REQ-CL-SH-01",
            "REQ-CL-C00",
            "REQ-CL-CI-01",
        }
        cov = run_coverage(reqs, _packet(), repo, deferred_ids=deferred)
        gaps = run_gaps(cov, phase="control-layer-fase1", deferred_ids=deferred)
        self.assertEqual(gaps, [])


if __name__ == "__main__":
    unittest.main()
