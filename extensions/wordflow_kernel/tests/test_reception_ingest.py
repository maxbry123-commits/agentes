# -*- coding: utf-8 -*-
"""ingest must invoke compiler; not only list next[]."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestReceptionIngest(unittest.TestCase):
    def test_ingest_invokes_compiler(self):
        from wordflow_kernel.reception.convert import ingest

        out = ingest(
            {
                "raw_text": "objective: wire reception\nsuccess: compiler invoked",
                "source_type": "chat",
            }
        )
        self.assertTrue(out.get("invoked", {}).get("input_compiler"))
        self.assertIn("phase", out)
        self.assertFalse(out.get("wrote"))

    def test_locate_phase_kernel(self):
        from wordflow_kernel.reception.convert import locate_phase

        loc = locate_phase("extensión kernel wordflow_kernel")
        self.assertEqual(loc["phase"], "kernel")
        self.assertIn("wordflow_kernel", loc["path"])


if __name__ == "__main__":
    unittest.main()
