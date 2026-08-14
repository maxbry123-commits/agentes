# -*- coding: utf-8 -*-
"""Tests T0o PlanningPort fakes."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.planning_proposal import merge_proposal_into_form
from extensions.wordflow.engine.ports.planning_port import (
    FakeHermesPlanner,
    FakeOpenClawPlanner,
    run_planning_ports,
)
from extensions.wordflow.engine.structured_questions import build_from_contract


class TestPlanningPort(unittest.TestCase):
    def test_fake_openclaw_proposal(self):
        c = compile_input_contract("success: need objective\n")
        form = build_from_contract(c)
        prop = FakeOpenClawPlanner().propose(c, form)
        self.assertEqual(prop["engine_id"], "openclaw")
        self.assertEqual(prop["status"], "PROPOSAL")
        self.assertIn("Q01_objective", prop["proposed_answers"])

    def test_fake_hermes_proposal(self):
        c = compile_input_contract("objective: x\nsuccess: y\n")
        form = build_from_contract(c)
        prop = FakeHermesPlanner().propose(c, form)
        self.assertEqual(prop["engine_id"], "hermes")
        self.assertTrue(prop["proposed_answers"].get("Q03_constraints") or prop["proposed_answers"].get("Q12_approver"))

    def test_run_both_and_merge_still_unresolved(self):
        c = compile_input_contract("success: z\n")
        form = build_from_contract(c)
        props = run_planning_ports(
            [FakeOpenClawPlanner(), FakeHermesPlanner()],
            c,
            form,
        )
        self.assertEqual(len(props), 2)
        merged = form
        for p in props:
            merged = merge_proposal_into_form(merged, p, auto_accept=False)
        self.assertFalse(merged["resolved"])


if __name__ == "__main__":
    unittest.main()
