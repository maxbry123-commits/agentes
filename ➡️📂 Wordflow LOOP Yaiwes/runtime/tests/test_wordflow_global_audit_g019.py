import json
import tempfile
import unittest
from pathlib import Path

from runtime.src.core.wordflow_global_audit import WordflowAuditError, audit_wordflow, required_path_status


class WordflowGlobalAuditTests(unittest.TestCase):
    def _root(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "Wordflow LOOP Yaiwes"
        (root / "runtime" / "src" / "core").mkdir(parents=True)
        (root / "docs").mkdir()
        return temp, root

    def test_detects_broken_required_path_and_is_stable(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "HANDOFF.md").write_text("ok", encoding="utf-8")
        first = audit_wordflow(root, required_paths=["HANDOFF.md", "PIPELINE/missing.md"])
        second = audit_wordflow(root, required_paths=["PIPELINE/missing.md", "HANDOFF.md"])
        self.assertEqual(first["broken_required_paths"], ["PIPELINE/missing.md"])
        self.assertEqual(first["report_sha256"], second["report_sha256"])
        self.assertFalse(first["policy"]["mutation_authorized"])
        self.assertEqual(first["ledger"][0]["kind"], "BROKEN_REQUIRED_PATH")

    def test_detects_exact_duplicates_without_deleting(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "docs" / "a.md").write_text("same", encoding="utf-8")
        (root / "docs" / "b.md").write_text("same", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertEqual(len(report["exact_duplicate_groups"]), 1)
        self.assertEqual(report["exact_duplicate_groups"][0]["count"], 2)
        self.assertTrue(report["policy"]["duplicates_are_candidates_not_auto_delete"])
        self.assertIn("EXACT_DUPLICATE_GROUP", report["ledger_counts"])

    def test_marks_zero_inbound_python_module_as_candidate(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "runtime" / "src" / "core" / "unused.py").write_text("VALUE = 2\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertIn("runtime/src/core/unused.py", report["python_orphan_candidates"])
        self.assertIn("runtime/src/core/unused.py", report["unused_code_candidates"])
        self.assertNotIn("runtime/src/core/kernel.py", report["python_orphan_candidates"])

    def test_imported_module_is_not_orphan_candidate(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("from core import helper\n", encoding="utf-8")
        (root / "runtime" / "src" / "core" / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertNotIn("runtime/src/core/helper.py", report["python_orphan_candidates"])
        self.assertEqual(report["broken_internal_imports"], [])

    def test_relative_import_is_not_orphan_candidate(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("from . import helper\n", encoding="utf-8")
        (root / "runtime" / "src" / "core" / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertNotIn("runtime/src/core/helper.py", report["python_orphan_candidates"])
        self.assertEqual(report["broken_internal_imports"], [])

    def test_capability_index_extracts_public_symbols(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("class Kernel:\n    pass\n\ndef run_task():\n    return True\n", encoding="utf-8")
        report = audit_wordflow(root)
        record = next(item for item in report["python_capabilities"] if item["module"] == "core.kernel")
        self.assertEqual(record["classes"], ["Kernel"])
        self.assertEqual(record["functions"], ["run_task"])
        self.assertEqual(record["parse_status"], "PASS")

    def test_detects_missing_src_prefixed_internal_import(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        uek = root / "runtime" / "src" / "uek"; uek.mkdir(parents=True)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("VALUE = 1\n", encoding="utf-8")
        (uek / "uek_cluster.py").write_text("from src.uek.cache_engine import DeterministicCacheEngine\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertEqual(report["broken_internal_imports"], [{"source": "runtime/src/uek/uek_cluster.py", "import": "uek.cache_engine", "reason": "INTERNAL_IMPORT_BASE_NOT_FOUND"}])
        self.assertIn("BROKEN_INTERNAL_IMPORT", report["ledger_counts"])
        self.assertTrue(report["policy"]["broken_internal_imports_are_fail_closed"])

    def test_does_not_flag_standard_library_import(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        (root / "runtime" / "src" / "core" / "kernel.py").write_text("import json\nfrom typing import Any\n", encoding="utf-8")
        report = audit_wordflow(root)
        self.assertEqual(report["broken_internal_imports"], [])

    def test_rejects_path_escape(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        with self.assertRaises(WordflowAuditError): required_path_status(root, ["../outside.md"])

    def test_report_is_json_serializable(self):
        temp, root = self._root(); self.addCleanup(temp.cleanup)
        json.dumps(audit_wordflow(root), sort_keys=True)


if __name__ == "__main__":
    unittest.main()
