"""VH-01 — ResourceContract immutable."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.resources.contract import ResourceContract


class TestVH01(unittest.TestCase):
    def test_frozen_pin(self):
        c = ResourceContract(
            resource_id="hf://dataset/example/data",
            provider="huggingface",
            kind="dataset",
            source_uri="https://huggingface.co/datasets/example/data",
            revision="abc123",
            capabilities=("search",),
            acquisition_mode="snapshot",
        )
        self.assertIn("abc123", c.pin_key())
        with self.assertRaises(Exception):
            c.revision = "other"  # type: ignore


if __name__ == "__main__":
    unittest.main()
