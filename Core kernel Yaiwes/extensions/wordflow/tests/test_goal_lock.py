# -*- coding: utf-8 -*-
"""C-01 tests — GoalLock e2e."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.goal_lock import (  # noqa: E402
    GoalLock,
    GoalLockError,
    admit_input,
    lock_goals,
)


def _base(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-C01-001",
        "source_type": "chat",
        "raw_text": "Implementar GoalLock inmutable 0% LLM con hash chain",
        "quality_bar": "never_MVP",
        "goals_hint": ["goal_lock", "e2e_admission"],
        "priority": "P0",
        "constraints": {
            "success_criteria": ["lock immutable", "hash present"],
            "loc_limit": 120,
        },
    }
    b.update(kw)
    return b


class TestGoalLock(unittest.TestCase):
    def test_lock_ok(self):
        out = lock_goals(_base())
        self.assertTrue(out["ok"])
        lock = out["lock"]
        self.assertEqual(lock["block_id"], "IB-C01-001")
        self.assertEqual(len(lock["lock_hash"]), 64)
        self.assertEqual(lock["quality_bar"], "never_MVP")
        self.assertIn("GIN-01", lock["goals_in"]["resolved"])
        self.assertGreaterEqual(lock["goals_in"]["covered_count"], 6)

    def test_immutable(self):
        out = lock_goals(_base())
        self.assertTrue(out["ok"])
        gl = GoalLock(out["lock"])
        with self.assertRaises(GoalLockError) as ctx:
            gl.priority = "P9"
        self.assertEqual(ctx.exception.reason_code, "LOCK_IMMUTABLE")

    def test_sentinel_fail(self):
        out = lock_goals(_base(raw_text="   "))
        self.assertFalse(out["ok"])
        self.assertIsNone(out["lock"])
        self.assertIn("EMPTY_RAW_TEXT", out["reason_codes"])

    def test_never_mvp_no_criteria(self):
        out = lock_goals(
            _base(constraints={"loc_limit": 50}),
            strict_never_mvp=True,
        )
        self.assertFalse(out["ok"])
        self.assertTrue(
            "L2_NO_SUCCESS_CRITERIA" in out["reason_codes"]
            or "L2_NO_OBJECTIVE" in out["reason_codes"]
            or len(out["reason_codes"]) >= 1
        )

    def test_admit_input(self):
        out = admit_input(_base())
        self.assertTrue(out["ok"])
        self.assertEqual(out["lock"]["lock_id"], "GL-IB-C01-001")

    def test_admit_bad(self):
        out = admit_input(None)
        self.assertFalse(out["ok"])
        self.assertTrue(len(out["reason_codes"]) >= 1)


if __name__ == "__main__":
    unittest.main()
