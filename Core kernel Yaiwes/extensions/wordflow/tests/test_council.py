# -*- coding: utf-8 -*-
"""A-WF-05 tests — Council of 12."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.council import load_roles, run_council  # noqa: E402
from wordflow.engine.goals_extractor import extract_goals_in  # noqa: E402
from wordflow.engine.input_normalizer import normalize_input_block  # noqa: E402
from wordflow.engine.refute_repair import refute_block  # noqa: E402
from wordflow.engine.sentinel import run_sentinel  # noqa: E402

ROLES = Path(__file__).resolve().parents[1] / "store" / "council_roles.yaml"


def _block(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-C1",
        "source_type": "chat",
        "raw_text": "Implementar fingerprint control-layer ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "doc_refs": [{"doc_id": "SALIDA4_FP"}],
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }
    b.update(kw)
    return normalize_input_block(b)


class TestCouncil(unittest.TestCase):
    def test_roles_12(self):
        cfg = load_roles(ROLES)
        self.assertEqual(len(cfg["roles"]), 12)
        self.assertEqual(cfg["quorum"], 7)

    def test_approve_clean(self):
        block = _block()
        goals = extract_goals_in(block)
        sent = run_sentinel(
            {
                "schema_version": "1.0",
                "block_id": block["block_id"],
                "source_type": "chat",
                "raw_text": block["raw_text"],
                "quality_bar": "never_MVP",
                "goals_hint": block["goals_hint"],
                "priority": "P0",
                "doc_refs": block["doc_refs"],
                "constraints": block["constraints"],
            },
            goals_in=goals,
        )
        ref = refute_block(block, goals)
        c = run_council(block=block, sentinel=sent, refute=ref, roles_path=ROLES)
        self.assertEqual(c["decision"], "APPROVE")
        self.assertEqual(c["veto_count"], 0)
        self.assertGreaterEqual(c["approve_count"], 7)

    def test_veto_on_budget(self):
        block = _block(constraints={"loc_limit": 500, "success_criteria": "ok"})
        goals = extract_goals_in(block)
        ref = refute_block(block, goals)
        sent = {"verdict": "FAIL", "checks": [], "reason_codes": ["L3_BUDGET_EXCEEDED"]}
        c = run_council(block=block, sentinel=sent, refute=ref, roles_path=ROLES)
        self.assertEqual(c["decision"], "REJECT")
        self.assertGreater(c["reject_count"], 0)

    def test_veto_security_rejected(self):
        block = _block()
        block["flags"] = dict(block.get("flags") or {})
        block["flags"]["rejected"] = True
        c = run_council(
            block=block, sentinel={"verdict": "FAIL"}, refute={"pass": False}
        )
        self.assertEqual(c["decision"], "REJECT")
        self.assertGreater(c["veto_count"], 0)

    def test_votes_structure(self):
        block = _block()
        c = run_council(
            block=block, sentinel={"verdict": "PASS"}, refute={"pass": True}
        )
        self.assertEqual(len(c["votes"]), 12)
        for v in c["votes"]:
            self.assertIn(v["vote"], ("APPROVE", "REJECT"))
            self.assertIn("role_id", v)


if __name__ == "__main__":
    unittest.main()
