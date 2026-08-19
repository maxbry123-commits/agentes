# -*- coding: utf-8 -*-
"""Loop must invoke run_code_path. Must not claim C-19 PASS."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestLoopCodePath(unittest.TestCase):
    def test_dispatch_invokes_no_pass(self):
        from maxbry_loop.code_path_bridge import dispatch_run_code_path

        out = dispatch_run_code_path("objective: loop wire\nsuccess: invoke")
        self.assertTrue(out.get("invoked"))
        self.assertFalse(out.get("c19_ok"))
        self.assertNotEqual(out.get("verdict"), "PASS")

    def test_engine_method(self):
        from maxbry_loop.models import Goal, State, Task
        from maxbry_loop.model import MockModel
        from maxbry_loop.engine import Engine

        class _Store:
            def save(self, state):
                return None

            def event(self, ev):
                return None

            def checkpoint(self, state):
                return None

        state = State(schema_version="2.0", goal=Goal(text="g"), tasks={})
        eng = Engine(state, _Store(), MockModel(), {"loop": {}})
        out = eng.dispatch_code_path("objective: engine method\nsuccess: invoked", mission_id="T1")
        self.assertTrue(out.get("invoked"))
        self.assertIs(eng.last_code_path, out)


if __name__ == "__main__":
    unittest.main()
