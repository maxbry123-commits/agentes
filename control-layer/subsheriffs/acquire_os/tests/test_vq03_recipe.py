"""VQ-03 — OpenClaw is recipe, not motor."""
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class TestVQ03(unittest.TestCase):
    def test_recipe_role(self):
        text = (BASE / "recipes/openclaw.example.yaml").read_text(encoding="utf-8")
        self.assertIn("role: engine_port_only", text)
        self.assertIn("continuous_loop_motor", text)
        self.assertIn("artifact_id: openclaw.runtime", text)


if __name__ == "__main__":
    unittest.main()
