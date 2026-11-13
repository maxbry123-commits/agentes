"""VL-04 — GoalLock bridge to continuous loop + stages."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.bridge import GoalLockView, goals_to_loop_state, goals_to_stage_plan
from maxbry_loop.engine import Engine
from maxbry_loop.model import MockModel
from maxbry_loop.persistence import FileStore
from wordflow_kernel.stages import DeterministicLoopEngine, make_default_handlers


class TestVL04(unittest.TestCase):
    def test_loop_state_from_goals(self):
        view = GoalLockView(
            mission_id="M1",
            workspace_id="W1",
            goals_in=("implement bridge", "add tests"),
        )
        state = goals_to_loop_state(view)
        self.assertEqual(len(state.tasks), 2)
        self.assertIn("implement bridge", state.goal.text)

    def test_run_continuous_from_bridge(self):
        view = GoalLockView("M2", "W1", ("ship",))
        state = goals_to_loop_state(view)
        with tempfile.TemporaryDirectory() as td:
            eng = Engine(
                state,
                FileStore(td),
                MockModel(),
                {"loop": {"max_iterations": 3, "completion_threshold": 0.5}},
            )
            final = eng.run()
            self.assertGreaterEqual(final.iteration, 1)

    def test_stage_plan_and_run(self):
        view = GoalLockView("M3", "W1", ("a", "b"))
        plan = goals_to_stage_plan(view)
        self.assertEqual(len(plan.goals), 2)
        eng = DeterministicLoopEngine(make_default_handlers())
        st = eng.run(plan)
        self.assertEqual(st.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
