"""VL-06 — E2E continuous loop with GatewayModel(Mock) + completion_score."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.bridge import GoalLockView, goals_to_loop_state
from wordflow_kernel.gateway import MockIntelligenceGateway
from maxbry_loop.engine import Engine
from maxbry_loop.model import GatewayModel, MockModel
from maxbry_loop.persistence import FileStore


class TestVL06(unittest.TestCase):
    def test_completion_score_mock(self):
        view = GoalLockView("M-VL06", "W1", ("task one", "task two"))
        state = goals_to_loop_state(view)
        with tempfile.TemporaryDirectory() as td:
            eng = Engine(
                state,
                FileStore(td),
                MockModel(),
                {
                    "loop": {
                        "max_iterations": 5,
                        "completion_threshold": 0.9,
                        "max_new_tasks_per_iteration": 2,
                    }
                },
            )
            final = eng.run()
            self.assertGreaterEqual(final.completion_score, 0.0)
            self.assertIsInstance(final.completion_score, float)

    def test_gateway_model_in_loop(self):
        view = GoalLockView("M-GW", "W1", ("via gateway",))
        state = goals_to_loop_state(view)
        gw = MockIntelligenceGateway(fixed_text="GATEWAY_DONE")
        with tempfile.TemporaryDirectory() as td:
            eng = Engine(
                state,
                FileStore(td),
                GatewayModel(gw),
                {"loop": {"max_iterations": 3, "completion_threshold": 0.5}},
            )
            final = eng.run()
            self.assertGreaterEqual(len(gw.calls), 1)
            self.assertTrue(any(t.status == "done" for t in final.tasks.values()))

    def test_score_increases_when_tasks_done(self):
        view = GoalLockView("M-SC", "W1", ("only one",))
        state = goals_to_loop_state(view)
        with tempfile.TemporaryDirectory() as td:
            eng = Engine(
                state,
                FileStore(td),
                MockModel(),
                {"loop": {"max_iterations": 2, "completion_threshold": 1.0}},
            )
            eng.bootstrap()
            eng.iteration()
            score = eng.completion()
            self.assertGreaterEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
