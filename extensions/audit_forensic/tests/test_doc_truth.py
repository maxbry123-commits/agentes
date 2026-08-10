# -*- coding: utf-8 -*-
"""A-AUD-02 tests — DocumentTruthStore seed + resolve."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from audit_forensic.engine.doc_truth import (  # noqa: E402
    DocumentTruthStore,
    DocTruthError,
    REASON,
)

SEED = Path(__file__).resolve().parents[1] / "store" / "document_truth_seed.yaml"


class TestDocTruth(unittest.TestCase):
    def setUp(self):
        self.store = DocumentTruthStore.from_seed(SEED)

    def test_seed_loads_six(self):
        self.assertGreaterEqual(len(self.store), 6)
        for doc_id in (
            "PIPELINE20",
            "SALIDA4_FP",
            "SALIDA4_RISK",
            "SALIDA4_SHERIFF",
            "C00",
            "AUDIT_SPEC",
        ):
            self.assertTrue(self.store.has(doc_id), doc_id)

    def test_active_ids(self):
        ids = self.store.active_ids()
        self.assertIn("C00", ids)
        self.assertIn("PIPELINE20", ids)

    def test_resolve_ok(self):
        r = self.store.resolve_anchor({"doc_id": "SALIDA4_FP", "section": "§14.2"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["doc_id"], "SALIDA4_FP")

    def test_resolve_missing_doc(self):
        r = self.store.resolve_anchor({"doc_id": "NO_EXISTE"})
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason_code"], REASON["DOC_NOT_IN_STORE"])

    def test_resolve_bad_section(self):
        r = self.store.resolve_anchor({"doc_id": "C00", "section": "§999"})
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason_code"], REASON["SECTION_NOT_FOUND"])

    def test_resolve_without_section(self):
        r = self.store.resolve_anchor({"doc_id": "AUDIT_SPEC"})
        self.assertTrue(r["ok"])

    def test_resolve_anchors_batch(self):
        results = self.store.resolve_anchors(
            [
                {"doc_id": "PIPELINE20", "section": "motor"},
                {"doc_id": "MISSING"},
            ]
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["ok"])
        self.assertFalse(results[1]["ok"])

    def test_superseded(self):
        store = DocumentTruthStore()
        store.register(
            {
                "doc_id": "OLD",
                "path": "x.md",
                "status": "superseded",
                "sections": [],
            }
        )
        r = store.resolve_anchor({"doc_id": "OLD"})
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason_code"], REASON["DOC_SUPERSEDED"])

    def test_register_get(self):
        e = self.store.get("C00")
        self.assertIsNotNone(e)
        self.assertEqual(e["path"], "control-layer/contracts/C00_governance.yaml")

    def test_missing_seed_file(self):
        with self.assertRaises(DocTruthError) as ctx:
            DocumentTruthStore.from_seed("/tmp/no_such_seed_aud02.yaml")
        self.assertEqual(ctx.exception.reason_code, REASON["SEED_MISSING"])


if __name__ == "__main__":
    unittest.main()
