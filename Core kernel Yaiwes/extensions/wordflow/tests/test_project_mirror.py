# -*- coding: utf-8 -*-
"""Tests C-16 project_mirror — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.project_mirror import ProjectMirror, ProjectMirrorError


class TestProjectMirror(unittest.TestCase):
    def test_isolate(self):
        m = ProjectMirror()
        m.create("p1")
        m.create("p2")
        m.set_doc("p1", "README.md", "one")
        m.set_doc("p2", "README.md", "two")
        self.assertEqual(m.snapshot("p1")["docs"]["README.md"], "one")
        self.assertEqual(m.snapshot("p2")["docs"]["README.md"], "two")

    def test_mirror(self):
        m = ProjectMirror()
        m.create("src", meta={"env": "hf-1"})
        m.set_doc("src", "A.md", "x")
        m.mirror("src", "copy")
        self.assertEqual(m.snapshot("copy")["docs"]["A.md"], "x")
        m.set_doc("copy", "A.md", "y")
        self.assertEqual(m.snapshot("src")["docs"]["A.md"], "x")

    def test_dup_raises(self):
        m = ProjectMirror()
        m.create("p")
        with self.assertRaises(ProjectMirrorError):
            m.create("p")


if __name__ == "__main__":
    unittest.main()
