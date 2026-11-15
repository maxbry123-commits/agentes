"""VL-01 — continuous loop offline with MockModel."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maxbry_loop.models import Goal, State, Task
from maxbry_loop.persistence import FileStore
from maxbry_loop.model import MockModel
from maxbry_loop.engine import Engine


class TestVL01(unittest.TestCase):
    def test_run_to_completion(self):
        with tempfile.TemporaryDirectory() as td:
            goal = Goal(text="Ship feature\n- must test\n- required deploy")
            tasks = {
                "T1": Task(id="T1", title="do work", description="work", priority=90),
            }
            state = State(schema_version="2.0", goal=goal, tasks=tasks)
            store = FileStore(td)
            eng = Engine(
                state,
                store,
                MockModel(),
                {"loop": {"max_iterations": 5, "completion_threshold": 0.5, "max_new_tasks_per_iteration": 3}},
            )
            final = eng.run()
            self.assertGreaterEqual(final.completion_score, 0.0)
            self.assertGreaterEqual(final.iteration, 1)


if __name__ == "__main__":
    unittest.main()
