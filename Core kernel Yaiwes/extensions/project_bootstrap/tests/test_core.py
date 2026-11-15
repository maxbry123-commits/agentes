# -*- coding: utf-8 -*-
"""
Tests unitarios A2–A6
A7 — evidencia de paso
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent.parent))
sys.path.insert(0, str(ROOT))

import unittest


class TestKTPEngine(unittest.TestCase):
    def setUp(self):
        from project_bootstrap.ktp.engine import create_engine, KTPContext
        self.engine = create_engine(str(ROOT / "ktp" / "states.yaml"))
        self.KTPContext = KTPContext

    def test_loads_13_states(self):
        self.assertEqual(len(self.engine.states), 13)

    def test_valid_transition(self):
        ctx = self.KTPContext(raw_input="test")
        ctx = self.engine.transition(ctx, "TAREA", output_data={"ok": True})
        self.assertEqual(ctx.current_state, "TAREA")
        self.assertEqual(len(ctx.history), 1)

    def test_invalid_transition_raises(self):
        ctx = self.KTPContext()
        with self.assertRaises(ValueError):
            self.engine.transition(ctx, "PASO")

    def test_resource_brain_flags(self):
        self.assertTrue(self.engine.requires_resource_brain("PLANIFICAR"))
        self.assertFalse(self.engine.requires_resource_brain("OBJETIVO"))

    def test_director_only_on_H(self):
        self.assertTrue(self.engine.requires_director("FALTA"))
        self.assertFalse(self.engine.requires_director("OBJETIVO"))


class TestMicroflows(unittest.TestCase):
    def test_extract_goal(self):
        from project_bootstrap.microflows.runner import extract_goal
        g = extract_goal("Crear un sistema de autenticación")
        self.assertEqual(g.verb, "crear")
        self.assertTrue(g.hash.startswith("sha256:"))
        self.assertIn("Crear", g.objective)

    def test_extract_goal_empty_raises(self):
        from project_bootstrap.microflows.runner import extract_goal
        with self.assertRaises(ValueError):
            extract_goal("")

    def test_decompose_tasks(self):
        from project_bootstrap.microflows.runner import extract_goal, decompose_tasks
        g = extract_goal("Implementar login y tests")
        tasks = decompose_tasks(g)
        self.assertGreaterEqual(len(tasks), 1)
        self.assertEqual(tasks[0].status, "PENDING")
        self.assertEqual(tasks[0].parent_goal_hash, g.hash)

    def test_run_microflujo_registry(self):
        from project_bootstrap.microflows.runner import run_microflujo, MICROFLUJOS
        self.assertIn("extract_goal", MICROFLUJOS)
        g = run_microflujo("extract_goal", raw_input="Validar el pipeline")
        self.assertEqual(g.verb, "validar")


class TestInputHandler(unittest.TestCase):
    def test_objetivo_classification(self):
        from project_bootstrap.input_handler import handle_input, InputKind
        r = handle_input("Necesito crear un login")
        self.assertEqual(r.input_block.kind, InputKind.OBJETIVO)
        self.assertTrue(len(r.derived_tasks) >= 1)

    def test_prioridad_pause(self):
        from project_bootstrap.input_handler import handle_input
        r = handle_input("Urgente: corregir el bug", current_running=True)
        self.assertTrue(r.should_pause)

    def test_literal_hash(self):
        from project_bootstrap.input_handler import make_input_block
        b1 = make_input_block("mismo texto")
        b2 = make_input_block("mismo texto")
        self.assertEqual(b1.hash, b2.hash)


class TestUpdater(unittest.TestCase):
    def test_no_change_ignored(self):
        from project_bootstrap.updater import IncrementalUpdater
        up = IncrementalUpdater()
        up.register("goal_struct", {"o": 1})
        r = up.apply_update("goal_struct", {"o": 1})
        self.assertFalse(r.changed)

    def test_change_impacts_dependents(self):
        from project_bootstrap.updater import IncrementalUpdater
        up = IncrementalUpdater()
        up.register("goal_struct", {"o": 1})
        r = up.apply_update("goal_struct", {"o": 2})
        self.assertTrue(r.changed)
        self.assertIn("task_list", r.impacted)
        self.assertIn("PROJECT_PROFILE", r.impacted)


class TestResourceBrain(unittest.TestCase):
    def test_onboard_available(self):
        from project_bootstrap.resource_brain import ResourceBrain
        rb = ResourceBrain()
        rb.onboard("cap_a")
        self.assertTrue(rb.is_available("cap_a"))

    def test_select_only_available(self):
        from project_bootstrap.resource_brain import ResourceBrain
        rb = ResourceBrain()
        rb.onboard("cap_a")
        rb.discover("cap_b")
        rb.register("cap_b")
        ready = rb.select_ready(["cap_a", "cap_b"])
        self.assertEqual(ready, ["cap_a"])


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestKTPEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestMicroflows))
    suite.addTests(loader.loadTestsFromTestCase(TestInputHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestUpdater))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceBrain))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n=== SUMMARY ===")
    print(f"Ran: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("STATUS: ALL PASSED" if result.wasSuccessful() else "STATUS: FAILED")
    sys.exit(0 if result.wasSuccessful() else 1)
