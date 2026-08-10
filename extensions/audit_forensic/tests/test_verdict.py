# -*- coding: utf-8 -*-
"""A-AUD-06 tests — verdict_engine."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.verdict_engine import decide_verdict  # noqa: E402


def _ok_summaries():
    return {
        "coverage_summary": {
            "counts": {"PRESENT": 5},
            "total": 5,
            "critical_missing": [],
        },
        "literal_summary": {"counts": {"PASS": 5}, "fails": [], "total": 5},
        "contradiction_summary": {
            "total": 3,
            "fails": [],
            "fail_count": 0,
            "has_critical_fail": False,
        },
        "gaps_summary": {
            "total": 0,
            "critical_count": 0,
            "critical_ids": [],
            "has_critical_gap": False,
        },
        "packet_flags": {},
        "packet_ok": True,
    }


class TestVerdict(unittest.TestCase):
    def test_confirmado(self):
        v = decide_verdict(**_ok_summaries())
        self.assertEqual(v["veredicto"], "CONFIRMADO")
        self.assertEqual(v["reason_codes"], [])
        self.assertEqual(v["capa1"]["veredicto"], "CONFIRMADO")

    def test_refutado_critical_gap(self):
        s = _ok_summaries()
        s["gaps_summary"] = {
            "total": 1,
            "critical_count": 1,
            "critical_ids": ["REQ-CL-FP-01"],
            "has_critical_gap": True,
        }
        s["coverage_summary"]["critical_missing"] = ["REQ-CL-FP-01"]
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "REFUTADO")
        self.assertIn("PHASE_GAP_CRITICAL", v["reason_codes"])

    def test_refutado_ci_failed(self):
        s = _ok_summaries()
        s["literal_summary"] = {
            "counts": {"FAIL": 1},
            "fails": [{"target": "REQ-CL-CI-01", "reason_code": "CI_FAILED"}],
            "total": 1,
        }
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "REFUTADO")
        self.assertIn("CI_FAILED", v["reason_codes"])

    def test_refutado_packet_invalid(self):
        s = _ok_summaries()
        s["packet_ok"] = False
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "REFUTADO")
        self.assertIn("INVALID_PACKET_SCHEMA", v["reason_codes"])

    def test_parcial_no_verificado(self):
        s = _ok_summaries()
        s["coverage_summary"] = {
            "counts": {"PRESENT": 3, "NO_VERIFICADO": 2},
            "total": 5,
            "critical_missing": [],
        }
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "PARCIAL")

    def test_parcial_non_critical_gap(self):
        s = _ok_summaries()
        s["gaps_summary"] = {
            "total": 1,
            "critical_count": 0,
            "critical_ids": [],
            "has_critical_gap": False,
        }
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "PARCIAL")

    def test_contradiction_fail_refuta(self):
        s = _ok_summaries()
        s["contradiction_summary"] = {
            "total": 1,
            "fails": [{"pair": "tests_vs_ci", "reason_code": "CI_MISSING"}],
            "fail_count": 1,
            "has_critical_fail": True,
        }
        v = decide_verdict(**s)
        self.assertEqual(v["veredicto"], "REFUTADO")
        self.assertIn("CI_MISSING", v["reason_codes"])

    def test_capa_structure(self):
        v = decide_verdict(**_ok_summaries())
        self.assertIn("capa1", v)
        self.assertIn("capa2", v)
        self.assertIn("capa3", v)
        self.assertIn("completitud_hint", v["capa1"])


if __name__ == "__main__":
    unittest.main()
