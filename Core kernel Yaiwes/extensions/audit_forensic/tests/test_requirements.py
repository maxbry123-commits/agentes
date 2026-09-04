# -*- coding: utf-8 -*-
"""A-AUD-03b tests — phase_seed + requirements loader."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.requirements_loader import (  # noqa: E402
    REASON,
    RequirementError,
    by_id,
    critical_only,
    load_requirements,
    normalize_requirement,
)

SEED = Path(__file__).resolve().parents[1] / "requirements" / "phase_seed.yaml"


class TestRequirements(unittest.TestCase):
    def test_load_all(self):
        reqs = load_requirements(SEED)
        self.assertGreaterEqual(len(reqs), 6)
        ids = {r["id"] for r in reqs}
        self.assertIn("REQ-CL-FP-01", ids)
        self.assertIn("REQ-AUD-PACKET", ids)

    def test_filter_phase(self):
        cl = load_requirements(SEED, phase="control-layer-fase1")
        self.assertTrue(all(r["phase"] == "control-layer-fase1" for r in cl))
        self.assertGreaterEqual(len(cl), 5)
        aud = load_requirements(SEED, phase="audit-fase1")
        self.assertEqual(len(aud), 1)
        self.assertEqual(aud[0]["id"], "REQ-AUD-PACKET")

    def test_by_id(self):
        m = by_id(load_requirements(SEED))
        self.assertEqual(
            m["REQ-CL-FP-01"]["params"]["path"],
            "control-layer/control/fingerprint.py",
        )

    def test_critical_only(self):
        crit = critical_only(load_requirements(SEED))
        self.assertTrue(all(r["critical"] for r in crit))
        self.assertGreaterEqual(len(crit), 6)

    def test_normalize_bad_type(self):
        with self.assertRaises(RequirementError) as ctx:
            normalize_requirement({"id": "X", "check_type": "magic"})
        self.assertEqual(ctx.exception.reason_code, REASON["INVALID_REQUIREMENT"])

    def test_normalize_missing_id(self):
        with self.assertRaises(RequirementError) as ctx:
            normalize_requirement({"check_type": "path_exists"})
        self.assertEqual(ctx.exception.reason_code, REASON["INVALID_REQUIREMENT"])

    def test_missing_seed(self):
        with self.assertRaises(RequirementError) as ctx:
            load_requirements("/tmp/no_phase_seed_aud03b.yaml")
        self.assertEqual(ctx.exception.reason_code, REASON["SEED_MISSING"])

    def test_check_types_present(self):
        reqs = load_requirements(SEED)
        types = {r["check_type"] for r in reqs}
        self.assertIn("path_exists", types)
        self.assertIn("ci_success", types)


if __name__ == "__main__":
    unittest.main()
