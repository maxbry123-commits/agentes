"""VH-03 — Dataset plan + Space agents.md parse."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.resources import ResourceContract, DatasetLoader, SpaceAgentsLoader


class TestVH03(unittest.TestCase):
    def test_dataset_plan_only(self):
        c = ResourceContract(
            resource_id="hf://dataset/acme/data",
            provider="huggingface",
            kind="dataset",
            source_uri="https://huggingface.co/datasets/acme/data",
            revision="v1",
            acquisition_mode="auto",
        )
        plan = DatasetLoader().plan(c)
        self.assertEqual(plan.mode, "snapshot")
        desc = DatasetLoader().describe_execution(plan)
        self.assertEqual(desc["status"], "PLAN_ONLY")

    def test_space_parse(self):
        md = """# My Space
api: https://example.com/gradio_api/call
poll: https://example.com/poll
schema: https://example.com/openapi.json
"""
        sc = SpaceAgentsLoader().parse(md, space_id="user/space")
        self.assertTrue(sc.call_url)
        rc = SpaceAgentsLoader().to_resource_contract(sc)
        self.assertEqual(rc.kind, "space")


if __name__ == "__main__":
    unittest.main()
