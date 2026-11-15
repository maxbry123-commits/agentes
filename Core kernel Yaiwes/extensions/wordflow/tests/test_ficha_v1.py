# -*- coding: utf-8 -*-
"""Tests V1-05 ficha + manifest."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestFichaV1(unittest.TestCase):
    def test_ficha_json(self):
        p = ROOT / "ficha.v2.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["abi_version"], "2.0")
        self.assertEqual(data["llm_control"], "DENY")
        self.assertIn("entrypoint_v1:run_v1", data["ejecucion"]["entry_point"])
        for k in ("abi_version", "extension_type", "kernel_min", "mount_mode", "load_priority"):
            self.assertIn(k, data)

    def test_manifest_exists(self):
        p = ROOT / "manifest.yaml"
        text = p.read_text(encoding="utf-8")
        self.assertIn("abi_version", text)
        self.assertIn("DENY", text)


if __name__ == "__main__":
    unittest.main()
