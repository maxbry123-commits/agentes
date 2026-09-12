import json
import tempfile
import unittest
from pathlib import Path

from runtime.src.core.wordflow_global_audit import (
    WordflowAuditError,
    audit_wordflow,
    required_path_status,
)


class WordflowGlobalAuditTests(unittest.TestCase):
    def _root(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "Wordflow LOOP Yaiwes"
        (root / "runtime" / "src" / "core").mkdir(parents=True)
        (root / "docs").mkdir()
        return temp, root

    def test_detects_broken_required_path_and_is_stable(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        (root / "HANDOFF.md").write_text("ok", encoding="utf-8")
        first = audit_wordflow(root, required_paths=["HANDOFF.md", "PIPELINE/missing.md"])
        second = audit_wordflow(root, required_paths=["PIPELINE/missing.md", "HANDOFF.md"])
        self.assertEqual(first["broken_required_paths"], ["PIPELINE/missing.md"])
        self.assertEqual(first["report_sha256"], second["report_sha256"])
        self.assertFalse(first["policy"]["mutation_authorized"])

    def test_detects_exact_duplicates_without_deleting(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        (root / "docs" / "a.md").write_text("same", encoding="utf-8")
        (root / "docs" / "b.md").write_text("same", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertEqual(len(report["exact_duplicate_groups"]), 1)
        self.assertEqual(report["exact_duplicate_groups"][0]["count"], 2)
        self.assertTrue(report["policy"]["duplicates_are_candidates_not_auto_delete"])

    def test_marks_zero_inbound_python_module_as_candidate(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "runtime" / "src" / "core" / "unused.py").write_text("VALUE = 2\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertIn("runtime/src/core/unused.py", report["python_orphan_candidates"])
        self.assertNotIn("runtime/src/core/kernel.py", report["python_orphan_candidates"])

    def test_imported_module_is_not_orphan_candidate(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("from core import helper\n", encoding="utf-8")
        (root / "runtime" / "src" / "core" / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertNotIn("runtime/src/core/helper.py", report["python_orphan_candidates"])

    def test_rejects_path_escape(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        with self.assertRaises(WordflowAuditError):
            required_path_status(root, ["../outside.md"])

    def test_report_is_json_serializable(self):
        temp, root = self._root()
        self.addCleanup(temp.cleanup)
        report = audit_wordflow(root)
        json.dumps(report, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
