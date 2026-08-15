"""VH-02 — SkillLoader IR."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.resources import SkillLoader


SAMPLE = """# Code Review Skill

Review Python PRs carefully.

## Steps
- Read diff
- Check tests

## Output
- Summary
"""


class TestVH02(unittest.TestCase):
    def test_parse_and_contract(self):
        ir = SkillLoader().load_text(SAMPLE, source_path="SKILL.md")
        self.assertEqual(ir.name, "Code Review Skill")
        self.assertTrue(len(ir.capabilities) >= 1)
        c = SkillLoader().to_contract(ir)
        self.assertEqual(c.kind, "skill")
        self.assertEqual(c.acquisition_mode, "file")

    def test_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "SKILL.md"
            p.write_text(SAMPLE, encoding="utf-8")
            ir = SkillLoader().load_file(p)
            self.assertIn("Review", ir.description)


if __name__ == "__main__":
    unittest.main()
