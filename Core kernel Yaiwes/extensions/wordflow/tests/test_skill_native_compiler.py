# -*- coding: utf-8 -*-
"""Tests C-06 skill_native_compiler — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.skill_native_compiler import (
    SkillNativeError,
    compile_and_promote_skill,
    compile_skill_to_code,
)

PIN = "b" * 40


class TestSkillNative(unittest.TestCase):
    def test_compile(self):
        r = compile_skill_to_code({
            "package_id": "sk.demo",
            "inputs": ["text"],
            "outputs": ["ir"],
        })
        self.assertTrue(r["ok"])
        self.assertIn("extensions/skills_native/sk/demo.py", r["content_map"])
        self.assertEqual(r["code_output"]["llm_control"], "DENY")

    def test_promote(self):
        r = compile_and_promote_skill({"skill_id": "sk.x"}, version_pin=PIN)
        self.assertTrue(r["ok"])
        self.assertTrue(r["promote"]["promoted"])

    def test_missing_id(self):
        with self.assertRaises(SkillNativeError):
            compile_skill_to_code({"version": "1"})


if __name__ == "__main__":
    unittest.main()
