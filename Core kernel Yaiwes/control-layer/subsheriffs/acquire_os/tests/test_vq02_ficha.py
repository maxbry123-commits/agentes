"""VQ-02 — ficha llm_control DENY + config OFF."""
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class TestVQ02(unittest.TestCase):
    def test_ficha(self):
        data = json.loads((BASE / "ficha.v2.json").read_text(encoding="utf-8"))
        self.assertEqual(data["llm_control"], "DENY")
        self.assertFalse(data["config"]["ACQUIRE_OS_ENABLED"])
        self.assertFalse(data["security"]["token_in_journal"])

    def test_config_yaml_off(self):
        text = (BASE / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("ACQUIRE_OS_ENABLED: false", text)


if __name__ == "__main__":
    unittest.main()
