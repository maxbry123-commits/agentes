# -*- coding: utf-8 -*-
"""Tests T0n PlanningProposal."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.planning_proposal import (
    accept_proposed,
    make_proposal,
    merge_proposal_into_form,
)
from extensions.wordflow.engine.structured_questions import build_from_contract, resolve_gate


class TestPlanningProposal(unittest.TestCase):
    def test_make_and_status(self):
        p = make_proposal(
            "ic_1",
            engine_id="fake",
            proposed_answers={"Q01_objective": "x", "Q12_approver": "director"},
            confidence=0.7,
        )
        self.assertEqual(p["status"], "PROPOSAL")
        self.assertEqual(len(p["proposal_hash"]), 64)

    def test_merge_does_not_auto_resolve(self):
        c = compile_input_contract("success: only success\n")
        form = build_from_contract(c)
        self.assertFalse(form["resolved"])
        p = make_proposal(
            c["contract_id"],
            proposed_answers={
                "Q01_objective": "obj desde proposal",
                "Q12_approver": "director",
            },
        )
        merged = merge_proposal_into_form(form, p, auto_accept=False)
        self.assertFalse(merged["resolved"])
        self.assertIn("Q01_objective", merged.get("proposed") or {})
        self.assertFalse(resolve_gate(merged)["ok"])

    def test_accept_proposed_then_resolve(self):
        c = compile_input_contract(
            "objective: ya hay objective\nsuccess: ok\n"
        )
        form = build_from_contract(c)
        p = make_proposal(
            c["contract_id"],
            proposed_answers={"Q12_approver": "director"},
        )
        merged = merge_proposal_into_form(form, p, auto_accept=False)
        form2 = accept_proposed(merged, "Q12_approver")
        self.assertTrue(resolve_gate(form2)["ok"])


if __name__ == "__main__":
    unittest.main()
