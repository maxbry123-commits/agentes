# -*- coding: utf-8 -*-
"""Tests T12 ResourceBroker."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.capability_passport import issue_passport
from extensions.wordflow.engine.resource_broker import ResourceBroker
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry


class TestResourceBroker(unittest.TestCase):
    def test_prepare_and_load_local(self):
        cat = ResourceCatalog()
        e = make_entry(
            name="loc",
            kind="skill",
            source="local",
            ref="file://loc",
            fetchable=True,
        )
        cat.add(e)
        br = ResourceBroker(cat)
        prep = br.prepare(e["resource_id"])
        self.assertTrue(prep["ok"])
        load = br.load(e["resource_id"])
        self.assertTrue(load["ok"])
        self.assertIn(e["resource_id"], br.list_loaded())

    def test_load_hf_denied(self):
        cat = ResourceCatalog()
        e = make_entry(name="hf-s", kind="skill", source="hf", ref="hf://s")
        cat.add(e)
        br = ResourceBroker(cat)
        prep = br.prepare(e["resource_id"])
        self.assertTrue(prep["ok"])
        load = br.load(e["resource_id"])
        self.assertFalse(load["ok"])
        self.assertEqual(
            load["detail"]["reason"], "REMOTE_FETCH_DENIED_PRE_POST_WORDFLOW"
        )

    def test_passport_blocks(self):
        cat = ResourceCatalog()
        e = make_entry(name="loc", kind="tool", source="local", fetchable=True)
        cat.add(e)
        p = issue_passport(
            subject_id="restricted",
            subject_kind="engine",
            capabilities=[],  # no resource:read
            denied=["resource:read"],
        )
        br = ResourceBroker(cat, passport=p)
        self.assertFalse(br.prepare(e["resource_id"])["ok"])


if __name__ == "__main__":
    unittest.main()
