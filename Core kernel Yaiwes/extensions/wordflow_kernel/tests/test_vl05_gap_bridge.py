"""VL-05 — gaps → TaskSpec → code_path jobs."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maxbry_loop.models import Task
from maxbry_loop.gaps import detect_gaps, append_gap_tasks
from maxbry_loop.models import Goal, State
from wordflow_kernel.bridge import (
    loop_tasks_to_taskspecs,
    gaps_to_taskspecs,
    taskspecs_to_code_path_jobs,
)


class TestVL05(unittest.TestCase):
    def test_loop_task_conversion(self):
        t = Task(id="T1", title="impl", description="do it", acceptance=["ok"])
        specs = loop_tasks_to_taskspecs([t], "W1")
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].workspace_id, "W1")

    def test_detect_and_compile(self):
        goal = Goal(text="Ship\n- must test\n- required feature")
        state = State(schema_version="2.0", goal=goal, tasks={})
        pairs = detect_gaps(goal, state)
        self.assertTrue(len(pairs) >= 1)
        specs = gaps_to_taskspecs(pairs, "W1")
        self.assertTrue(len(specs) >= 1)
        jobs = taskspecs_to_code_path_jobs(specs)
        self.assertEqual(jobs[0]["pipeline"], "code_path")

    def test_append_gap_tasks_then_bridge(self):
        goal = Goal(text="- must implement api")
        state = State(schema_version="2.0", goal=goal, tasks={})
        pairs = detect_gaps(goal, state)
        added = append_gap_tasks(state, pairs, max_new=5)
        specs = loop_tasks_to_taskspecs(added, "W2")
        self.assertEqual(len(specs), len(added))


if __name__ == "__main__":
    unittest.main()
