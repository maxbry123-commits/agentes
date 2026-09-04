from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.standards.gap_registry import Gap
from extensions.wordflow.standards.gap_state_machine import GapStateMachine
from extensions.wordflow.standards.gap_registry import GapRegistry


class TestGapStateMachine(unittest.TestCase):
    def test_persistent_lifecycle_and_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "gaps.json"
            machine = GapStateMachine(GapRegistry(path=str(path)))
            machine.create(Gap("G-1", "T-1", "M-1", "R-1", "blocking", "test gap"))
            machine.advance("G-1", "FIXED", evidence="fix", revision="r1")
            machine.advance("G-1", "VERIFIED", evidence="verified", revision="r2")
            machine.advance("G-1", "CLOSED", evidence="closed", revision="r3")

            recovered = GapStateMachine(GapRegistry(path=str(path))).recover()
            self.assertEqual(recovered[0]["status"], "CLOSED")
            self.assertEqual(recovered[0]["verified_revision"], "r2")

    def test_invalid_jump_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            machine = GapStateMachine(GapRegistry(path=str(Path(td) / "gaps.json")))
            machine.create(Gap("G-2", "T-2", "M-2", "R-2", "blocking", "test gap"))
            with self.assertRaises(ValueError):
                machine.advance("G-2", "CLOSED", evidence="invalid")


if __name__ == "__main__":
    unittest.main()
