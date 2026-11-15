"""VL-03 — 12-stage loop completes with default handlers."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.stages import (
    Goal,
    DeterministicLoopEngine,
    make_default_handlers,
    KernelLoopHook,
)


class TestVL03(unittest.TestCase):
    def test_twelve_stages_complete(self):
        eng = DeterministicLoopEngine(make_default_handlers())
        hook = KernelLoopHook(eng)
        state = hook.activate(
            "M1",
            [Goal("g1", "ship")],
            ["step1", "step2"],
        )
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(len(state.completed), 12)
        self.assertEqual(state.completed[0], "ADMIT")
        self.assertEqual(state.completed[-1], "CLOSE")


if __name__ == "__main__":
    unittest.main()
