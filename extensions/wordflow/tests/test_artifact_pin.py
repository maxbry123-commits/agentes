# -*- coding: utf-8 -*-
"""Tests T8 ArtifactPin."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.artifact_pin import (
    pin_from_bytes,
    pin_from_path,
    pin_from_text,
    verify_content,
    verify_pin,
)


class TestArtifactPin(unittest.TestCase):
    def test_text_pin(self):
        pin = pin_from_text("hello wave2", ref="mem://hello", labels=["t8"])
        self.assertTrue(verify_pin(pin)["ok"])
        self.assertEqual(pin["size_bytes"], len(b"hello wave2"))

    def test_content_mismatch(self):
        pin = pin_from_bytes(b"abc", ref="blob://x")
        self.assertFalse(verify_content(pin, b"xyz")["ok"])
        self.assertTrue(verify_content(pin, b"abc")["ok"])

    def test_tamper_pin_hash(self):
        pin = pin_from_text("x", ref="r")
        pin["ref"] = "other"
        self.assertFalse(verify_pin(pin)["ok"])

    def test_from_path(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_text("file-content", encoding="utf-8")
            pin = pin_from_path(path)
            self.assertEqual(pin["kind"], "file")
            self.assertTrue(verify_content(pin, path.read_bytes())["ok"])


if __name__ == "__main__":
    unittest.main()
