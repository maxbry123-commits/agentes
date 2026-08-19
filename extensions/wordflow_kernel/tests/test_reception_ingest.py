# -*- coding: utf-8 -*-
"""ingest must invoke compiler; plugin FAIL-closed; locate-only default."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(out.get("phase", {}).get("contract"), "LOCATE_ONLY")

    def test_locate_phase_kernel(self):
        from wordflow_kernel.reception.convert import locate_phase

        loc = locate_phase("extensión kernel wordflow_kernel")
        self.assertEqual(loc["phase"], "kernel")
        self.assertIn("wordflow_kernel", loc["path"])

    def test_ingest_fail_closed_if_plugin_not_ok(self):
        from wordflow_kernel.reception import convert as rec

        with patch.object(rec, "attach_plugin", return_value={"ok": False, "invoked": True, "error": "FICHA_NOT_ON_DISK"}):
            out = rec.ingest({"raw_text": "objective: fail closed\nsuccess: plugin blocks"})
        self.assertTrue(out.get("invoked", {}).get("input_compiler"))
        self.assertFalse(out.get("ok"))
        self.assertFalse(out.get("plugin", {}).get("ok"))

    def test_apply_writes_phase_plan_not_git(self):
        from wordflow_kernel.reception.convert import ingest

        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "phase_plan.json"
            out = ingest(
                {"raw_text": "objective: plan\nsuccess: wrote plan"},
                apply=True,
                plan_path=str(dest),
            )
            self.assertTrue(dest.is_file())
            self.assertTrue(out.get("wrote"))
            self.assertFalse(out.get("phase_plan", {}).get("git_apply"))


if __name__ == "__main__":
    unittest.main()
