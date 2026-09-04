# -*- coding: utf-8 -*-
"""Tests C-05 analyze_12 — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.analyze_12 import AnalyzeError, analyze_12, analyze_document
from extensions.wordflow.engine.dual_compiler import compile_output

SAMPLE = """# Mission

## Components

Use `engine/main.py` and `schemas/out.yaml`.

```python
print(1)
```
"""


class TestAnalyze12(unittest.TestCase):
    def test_analyze_document(self):
        r = analyze_document(SAMPLE, doc_id="s1")
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["metrics"]["headings"], 1)
        self.assertIn("engine/main.py", [f["path"] for f in r["architecture_seed"]["files"]])

    def test_seed_validates_as_architecture(self):
        r = analyze_document(SAMPLE, doc_id="s2")
        c = compile_output("architecture_output", r["architecture_seed"])
        self.assertTrue(c["ok"])

    def test_batch(self):
        b = analyze_12([{"id": "a", "text": SAMPLE}, {"id": "b", "text": "# Only\n"}])
        self.assertEqual(b["count"], 2)

    def test_empty_raises(self):
        with self.assertRaises(AnalyzeError):
            analyze_document("   ")


if __name__ == "__main__":
    unittest.main()
