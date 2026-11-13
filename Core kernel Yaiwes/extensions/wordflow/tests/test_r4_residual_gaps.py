# -*- coding: utf-8 -*-
"""R4 residual gap closures: G-W13b, G-W14b, G-W3b, hops_ok."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extensions.wordflow.standards.mission_edges import edges_from_mission
from extensions.wordflow.standards.scope_measure import scope_from_git_diff
from extensions.wordflow.standards.symbol_index import build_symbol_index, clear_symbol_cache


class TestGW13bGitScope(unittest.TestCase):
    def test_scope_from_git_diff_invokes_git(self):
        with tempfile.TemporaryDirectory() as td:
            out = scope_from_git_diff(td, base="HEAD")
        self.assertEqual(out["source"], "git_diff")
        self.assertIn("actual_paths", out)


class TestGW14bMissionEdges(unittest.TestCase):
    def test_edges_from_mission_injects_business(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "required.py"
            p.write_text("x = 1\n", encoding="utf-8")
            reg = edges_from_mission(
                {
                    "mission_id": "m-biz",
                    "include_defaults": False,
                    "llm_control": "DENY",
                    "required_paths": [str(p)],
                    "edges": [{"name": "accepts_only_locate", "pass": True}],
                }
            )
            result = reg.run()
        self.assertTrue(result["passed"], msg=str(result))
        names = {r["name"] for r in result["results"]}
        self.assertIn("accepts_only_locate", names)
        self.assertIn("mission_llm_control_deny", names)


class TestGW3bDiskCache(unittest.TestCase):
    def test_symbol_index_writes_disk_cache(self):
        clear_symbol_cache()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "src"
            root.mkdir()
            (root / "mod.py").write_text("class Foo:\n    pass\n", encoding="utf-8")
            cache = Path(td) / "cache"
            os.environ["WORDFLOW_SYMBOL_CACHE"] = str(cache)
            try:
                idx = build_symbol_index([root], use_cache=True, use_disk=True)
                self.assertTrue(idx.find("Foo"))
                files = list(cache.glob("symbols_*.json"))
                self.assertTrue(files)
                clear_symbol_cache()
                idx2 = build_symbol_index([root], use_cache=True, use_disk=True)
                self.assertTrue(idx2.find("Foo"))
            finally:
                os.environ.pop("WORDFLOW_SYMBOL_CACHE", None)
                clear_symbol_cache()


class TestHopsOkFailClosed(unittest.TestCase):
    def test_plugin_false_sets_hops_ok_false(self):
        from extensions.wordflow_kernel.reception import convert as rec

        with patch.object(
            rec,
            "attach_plugin",
            return_value={"ok": False, "invoked": True, "error": "FICHA_NOT_ON_DISK"},
        ):
            out = rec.ingest({"raw_text": "objective: hops\nsuccess: plugin fail closed"})
        self.assertFalse(out.get("ok"))
        self.assertFalse(out.get("hops_ok"))


if __name__ == "__main__":
    unittest.main()
