# -*- coding: utf-8 -*-
"""Tests C-11 docs templates — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.docs_templates.generator import (
    DocsTemplateError,
    generate_project_docs,
    list_templates,
)


class TestDocsTemplates(unittest.TestCase):
    def test_list(self):
        names = list_templates()
        self.assertGreaterEqual(len(names), 9)
        self.assertIn("README.md", names)
        self.assertIn("PIPELINE.md", names)

    def test_generate_all(self):
        r = generate_project_docs(
            project_name="Demo",
            mission_id="m1",
            objectives=["ship C-11"],
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["count"], len(list_templates()))
        self.assertIn("Demo", r["files"]["README.md"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_only_subset(self):
        r = generate_project_docs(project_name="X", only=["README.md", "CHANGELOG.md"])
        self.assertEqual(r["count"], 2)

    def test_unknown(self):
        with self.assertRaises(DocsTemplateError):
            generate_project_docs(project_name="X", only=["NOPE.md"])


if __name__ == "__main__":
    unittest.main()
