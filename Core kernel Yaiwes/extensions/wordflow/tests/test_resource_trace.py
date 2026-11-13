# -*- coding: utf-8 -*-
"""Tests T0c ResourceTraceBuilder."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.resource_trace import build_resource_trace, trace_gate


class TestResourceTrace(unittest.TestCase):
    def test_build_with_temp_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "extensions" / "wordflow" / "schemas").mkdir(parents=True)
            f = root / "extensions" / "wordflow" / "schemas" / "input_contract.schema.json"
            f.write_text("{}", encoding="utf-8")
            contract = {
                "contract_id": "ic_test",
                "resources_declared": ["hf://skills/demo"],
                "engines_allowed": ["openclaw"],
            }
            trace = build_resource_trace(
                contract,
                workspace_root=str(root),
                extra_paths=["extensions/wordflow/schemas/input_contract.schema.json"],
            )
            self.assertEqual(trace["schema_version"], "1.0")
            self.assertEqual(trace["contract_id"], "ic_test")
            self.assertGreaterEqual(trace["summary"]["found"], 1)
            self.assertGreaterEqual(trace["summary"]["declared"], 2)
            self.assertEqual(len(trace["trace_hash"]), 64)
            statuses = {i["locator"]: i["status"] for i in trace["items"]}
            self.assertEqual(
                statuses.get("extensions/wordflow/schemas/input_contract.schema.json"),
                "FOUND",
            )

    def test_missing_path(self):
        with tempfile.TemporaryDirectory() as td:
            trace = build_resource_trace(
                {"contract_id": "c1"},
                workspace_root=td,
                extra_paths=["does/not/exist.py"],
            )
            self.assertIn("path:does/not/exist.py", trace["missing_ids"])

    def test_trace_gate_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "extensions" / "wordflow"
            p.mkdir(parents=True)
            trace = build_resource_trace(
                workspace_root=str(root),
                extra_paths=["extensions/wordflow", "missing/x"],
            )
            gate_ok = trace_gate(trace, require_paths=["extensions/wordflow"])
            self.assertTrue(gate_ok["ok"])
            gate_fail = trace_gate(trace, require_paths=["missing/x"])
            self.assertFalse(gate_fail["ok"])
            self.assertIn("missing/x", gate_fail["missing_required"])


if __name__ == "__main__":
    unittest.main()
