# -*- coding: utf-8 -*-
"""Tests C-27 Knowledge Runtime — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.knowledge.registry import RegistryError, UnifiedRegistry, make_package
from extensions.knowledge.runtime import KnowledgeRuntime


class TestKnowledgeRuntime(unittest.TestCase):
    def test_register_and_get(self):
        rt = KnowledgeRuntime()
        r = rt.register_skill("sk.demo", inputs=["text"], outputs=["ir"])
        self.assertTrue(r["ok"])
        pkg = rt.registry.get("sk.demo")
        self.assertIsNotNone(pkg)
        self.assertEqual(pkg["kind"], "skill")
        self.assertEqual(pkg["llm_control"], "DENY")

    def test_deps_resolve(self):
        rt = KnowledgeRuntime()
        rt.register_dataset("ds.base")
        rt.register_method("mt.pipe", deps=["ds.base@1.0.0"])
        res = rt.registry.resolve_deps("mt.pipe")
        self.assertTrue(res["ok"])

    def test_missing_deps(self):
        rt = KnowledgeRuntime()
        rt.register_method("mt.x", deps=["missing.pkg"])
        res = rt.registry.resolve_deps("mt.x")
        self.assertFalse(res["ok"])

    def test_promote(self):
        rt = KnowledgeRuntime()
        rt.register_method("mt.ok")
        p = rt.promote_method("mt.ok")
        self.assertTrue(p["ok"])
        self.assertTrue(rt.registry.get("mt.ok")["meta"].get("promoted"))

    def test_invalid_kind(self):
        with self.assertRaises(RegistryError):
            make_package(kind="nope", package_id="x")

    def test_list_by_kind(self):
        reg = UnifiedRegistry()
        reg.register(make_package(kind="adapter", package_id="ad.1"))
        reg.register(make_package(kind="skill", package_id="sk.1"))
        self.assertEqual(len(reg.list(kind="adapter")), 1)


if __name__ == "__main__":
    unittest.main()
