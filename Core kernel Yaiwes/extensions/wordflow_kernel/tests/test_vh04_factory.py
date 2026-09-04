"""VH-04 — AdapterFactory PLAN_ONLY."""
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.resources import AdapterFactory, ResourceContract


class TestVH04(unittest.TestCase):
    def test_skill_register(self):
        f = AdapterFactory()
        c = f.from_skill_markdown("# S\n\n## A\n- step\n", source_path="SKILL.md")
        self.assertEqual(c.kind, "skill")
        self.assertIn(c.resource_id, f.registry.list_ids())

    def test_execute_plan_blocked(self):
        f = AdapterFactory()
        c = ResourceContract(
            "hf://dataset/x/y",
            "huggingface",
            "dataset",
            "https://huggingface.co/datasets/x/y",
            revision="1",
        )
        plan = f.plan_dataset(c)
        with patch.dict(os.environ, {"FETCH_ENABLED": "false"}):
            out = f.execute_plan(plan)
        self.assertFalse(out["executed"])
        self.assertEqual(out["status"], "PLAN_ONLY")


if __name__ == "__main__":
    unittest.main()
