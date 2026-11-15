"""VK-05 tests — ResourceRegistry + Validator."""
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.models import Resource
from wordflow_kernel.resources import ResourceRegistry, SkillResolver
from wordflow_kernel.validator import Validator


class TestVK05(unittest.TestCase):
    def test_register_resolve(self):
        reg = ResourceRegistry()
        reg.register(
            Resource(
                resource_id="skill.python",
                kind="skill",
                source="hf://x",
                version="1",
                capabilities=("code.analyze",),
            )
        )
        hits = SkillResolver(reg).resolve("code.analyze")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].resource_id, "skill.python")

    def test_duplicate_deny(self):
        reg = ResourceRegistry()
        r = Resource("a", "skill", "s", capabilities=("x",))
        reg.register(r)
        with self.assertRaises(ValueError):
            reg.register(r)

    def test_validator_pass(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "ok.py").write_text("x = 1\n", encoding="utf-8")
            v = Validator().validate_python_tree(td)
            self.assertEqual(v["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
