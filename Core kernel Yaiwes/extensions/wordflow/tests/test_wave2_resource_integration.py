# -*- coding: utf-8 -*-
"""T13 — WAVE-2 integration: ArtifactPin + Catalog + Gate + Passport + Broker."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.artifact_pin import pin_from_text, verify_content, verify_pin
from extensions.wordflow.engine.capability_passport import (
    authorize,
    default_engine_passport,
    issue_passport,
)
from extensions.wordflow.engine.resource_broker import ResourceBroker
from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry, seed_hf_index_stub
from extensions.wordflow.engine.resource_gate import check_entry


class TestWave2ResourceIntegration(unittest.TestCase):
    def test_pin_linked_catalog_local_load(self):
        content = "skill-body-wave2"
        pin = pin_from_text(content, ref="mem://skill-wave2", labels=["skill"])
        self.assertTrue(verify_pin(pin)["ok"])
        self.assertTrue(verify_content(pin, content.encode())["ok"])

        cat = ResourceCatalog()
        entry = make_entry(
            name="skill-wave2",
            kind="skill",
            source="local",
            ref=pin["ref"],
            pin_id=pin["pin_id"],
            content_sha256=pin["content_sha256"],
            fetchable=True,
            tags=["wave2"],
        )
        cat.add(entry)

        passport = default_engine_passport("fake_static")
        self.assertTrue(authorize(passport, "resource:read")["ok"])

        br = ResourceBroker(cat, passport=passport)
        prep = br.prepare(entry["resource_id"])
        self.assertTrue(prep["ok"])
        self.assertEqual(prep["plan"]["next"], "load")

        loaded = br.load(entry["resource_id"])
        self.assertTrue(loaded["ok"])
        self.assertEqual(loaded["payload"]["pin_id"], pin["pin_id"])
        self.assertEqual(loaded["payload"]["content_sha256"], pin["content_sha256"])

    def test_hf_seed_prepare_ok_fetch_denied(self):
        cat = ResourceCatalog()
        for e in seed_hf_index_stub():
            cat.add(e)
        hf_entries = cat.list(source="hf")
        self.assertGreaterEqual(len(hf_entries), 1)
        e = hf_entries[0]

        self.assertTrue(check_entry(e, action="read")["ok"])
        self.assertTrue(check_entry(e, action="prepare")["ok"])
        self.assertFalse(check_entry(e, action="fetch")["ok"])

        br = ResourceBroker(cat)
        self.assertTrue(br.prepare(e["resource_id"])["ok"])
        self.assertFalse(br.load(e["resource_id"])["ok"])

    def test_passport_denies_read(self):
        cat = ResourceCatalog()
        e = make_entry(name="x", kind="tool", source="local", fetchable=True)
        cat.add(e)
        p = issue_passport(
            subject_id="locked-down",
            subject_kind="engine",
            capabilities=["route:ANALYSIS"],
            denied=["resource:read"],
        )
        br = ResourceBroker(cat, passport=p)
        r = br.prepare(e["resource_id"])
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "passport")


if __name__ == "__main__":
    unittest.main()
