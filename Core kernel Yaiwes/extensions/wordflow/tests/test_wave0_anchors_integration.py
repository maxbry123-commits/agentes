# -*- coding: utf-8 -*-
"""T0m — Integration: Input → Questions → Goals → Lock → Echo → Registers
→ Classifier → Ping → Focus → Bitacora → ReasoningLedger. 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.bitacora import BitacoraStore
from extensions.wordflow.engine.cognitive_registers import (
    as_prompt_block,
    load_from_lock,
    set_register,
)
from extensions.wordflow.engine.focus_monitor import evaluate_focus, focus_gate
from extensions.wordflow.engine.goal_lock import (
    create_goal_lock,
    validate_against_lock,
    verify_lock_integrity,
)
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.objective_echo import inject_echo
from extensions.wordflow.engine.push_ping import PushPingSupervisor, emit_ping
from extensions.wordflow.engine.reasoning_ledger import ReasoningLedger
from extensions.wordflow.engine.resource_trace import build_resource_trace
from extensions.wordflow.engine.structured_questions import (
    answer,
    build_from_contract,
    resolve_gate,
)
from extensions.wordflow.engine.task_classifier import classify_task, decision_gate


class TestWave0AnchorsIntegration(unittest.TestCase):
    def test_full_happy_path(self):
        raw = (
            "objective: cerrar wave0 anchors integration\n"
            "success: cadena T0a-T0l PASS\n"
            "constraint: 0% LLM\n"
            "forbidden: saltar goal lock\n"
        )
        contract = compile_input_contract(raw)
        self.assertIn(contract["status"], ("COMPLETE", "INCOMPLETE"))

        form = build_from_contract(contract)
        if not form["resolved"]:
            form = answer(form, "Q12_approver", "director")
        self.assertTrue(resolve_gate(form)["ok"])

        goals = compile_goals(form)
        self.assertEqual(goals["status"], "COMPILED")

        lock = create_goal_lock(goals)
        self.assertTrue(verify_lock_integrity(lock)["ok"])

        trace = build_resource_trace(contract, extra_paths=[])
        self.assertEqual(trace["contract_id"], contract["contract_id"])

        echo_pkg = inject_echo(lock, "ejecutar paso integracion")
        self.assertIn("GOAL_LOCK", echo_pkg["prompt"])

        regs = load_from_lock(lock)
        regs = set_register(regs, "R1_step", "integration_test")
        block = as_prompt_block(regs)
        self.assertIn("R0_objective", block)

        classification = classify_task(
            "correr pytest unittest validar schema",
            explicit_route="DETERMINISTIC",
        )
        gate = decision_gate(classification)
        self.assertFalse(gate["call_llm"])

        aligned_out = (
            "cerrar wave0 anchors integration con cadena T0a-T0l PASS "
            "sin saltar goal lock 0% LLM"
        )
        self.assertTrue(validate_against_lock(lock, aligned_out)["ok"])

        ping = emit_ping(
            lock,
            trigger="post_tool",
            current_step="integration_test",
            last_output=aligned_out,
        )
        self.assertEqual(ping["action"], "CONTINUE")

        focus = evaluate_focus(
            lock,
            current_step="integration_test",
            last_output=aligned_out,
        )
        self.assertFalse(focus["below_threshold"] or focus["band"] == "ZERO")
        self.assertTrue(
            focus_gate(
                lock,
                current_step="cerrar wave0",
                last_output=aligned_out,
            )["ok"]
        )

        bit = BitacoraStore()
        bit.append("LOCK_CREATED", lock["lock_id"], {"lock_hash": lock["lock_hash"]})
        bit.append("PING", lock["lock_id"], {"action": ping["action"]})
        bit.append("FOCUS", lock["lock_id"], {"score": focus["score"]})
        self.assertTrue(bit.verify_chain()["ok"])

        ledger = ReasoningLedger()
        frame = ledger.append_frame(
            lock,
            decision="WAVE0_ANCHORS_OK",
            evidence=["integration_happy_path"],
            confidence=1.0,
            checkpoint_id="t0m",
        )
        self.assertEqual(frame["lock_id"], lock["lock_id"])
        self.assertTrue(ledger.verify_chain()["ok"])

    def test_goal_violation_discards(self):
        contract = compile_input_contract(
            "objective: proteger goal lock\n"
            "success: discard on forbidden\n"
            "forbidden: saltar goal lock\n"
        )
        form = build_from_contract(contract)
        form = answer(form, "Q12_approver", "director")
        lock = create_goal_lock(compile_goals(form))
        bad = validate_against_lock(lock, "voy a saltar goal lock ahora")
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["action"], "DISCARD_OUTPUT")

    def test_unresolved_form_blocks_goals(self):
        contract = compile_input_contract(
            "objective: solo objective\nsuccess: falta approver en form\n"
        )
        form = build_from_contract(contract)
        # Q12 still pending
        self.assertFalse(resolve_gate(form)["ok"])
        goals = compile_goals(form)
        self.assertEqual(goals["status"], "BLOCKED_UNRESOLVED_FORM")

    def test_supervisor_interval(self):
        contract = compile_input_contract(
            "objective: ping interval supervisor\n"
            "success: second ping after interval\n"
        )
        form = answer(build_from_contract(contract), "Q12_approver", "auto")
        lock = create_goal_lock(compile_goals(form))
        sup = PushPingSupervisor(lock, interval_s=15)
        e1 = sup.maybe_interval_ping(
            now_mono=0.0,
            current_step="ping interval supervisor",
            last_output="ping interval supervisor ok",
        )
        self.assertIsNotNone(e1)
        e2 = sup.maybe_interval_ping(now_mono=5.0)
        self.assertIsNone(e2)


if __name__ == "__main__":
    unittest.main()
