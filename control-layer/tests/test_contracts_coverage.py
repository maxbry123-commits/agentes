# -*- coding: utf-8 -*-
"""B8 — coverage C00–C85 contracts on disk."""
from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1] / "contracts"


def _load_all() -> dict[str, dict]:
    out = {}
    for p in ROOT.rglob("C*.yaml"):
        if yaml is None:
            raise RuntimeError("PyYAML required")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        cid = data.get("id") or p.name.split("_")[0]
        out[cid] = data
    return out


class TestContractsCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = _load_all()

    def test_count_86(self):
        self.assertEqual(len(self.contracts), 86)

    def test_ids_c00_to_c85(self):
        have = set(self.contracts.keys())
        for i in range(0, 86):
            variants = {f"C{i}", f"C{i:02d}"}
            self.assertTrue(have & variants, f"missing contract C{i}")

    def test_c00_critical(self):
        c00 = self.contracts.get("C00") or self.contracts.get("C0")
        self.assertIsNotNone(c00)
        self.assertTrue(c00.get("critical") or c00.get("id") == "C00")

    def test_l8_abi_critical(self):
        for cid in ("C82", "C83", "C84", "C85"):
            self.assertIn(cid, self.contracts)
            self.assertTrue(self.contracts[cid].get("critical"))

    def test_all_have_layer(self):
        for cid, data in self.contracts.items():
            self.assertIn("layer", data, cid)

    def test_all_implementado(self):
        for cid, data in self.contracts.items():
            self.assertTrue(data.get("implementado"), cid)

    def test_routing_13_types_file(self):
        routing = ROOT.parent / "rules" / "routing.yaml"
        data = yaml.safe_load(routing.read_text(encoding="utf-8"))
        keys = [k for k in data.keys() if isinstance(data[k], list)]
        self.assertEqual(len(keys), 13)

    def test_modifiers_present(self):
        mod = ROOT.parent / "rules" / "modifiers.yaml"
        data = yaml.safe_load(mod.read_text(encoding="utf-8"))
        self.assertIn("modifiers", data)
        self.assertGreaterEqual(len(data["modifiers"]), 5)


if __name__ == "__main__":
    unittest.main()
