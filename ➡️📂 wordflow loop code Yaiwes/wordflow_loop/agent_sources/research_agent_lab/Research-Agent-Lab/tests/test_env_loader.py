from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from tools.env_loader import load_env_file, mask_secret


class EnvLoaderTest(unittest.TestCase):
    def test_load_env_file_without_exposing_value(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("DEEPSEEK_API_KEY=sk-1234567890abcdef\n", encoding="utf-8")
            old = os.environ.pop("DEEPSEEK_API_KEY", None)
            try:
                loaded = load_env_file(path)
                self.assertIn("DEEPSEEK_API_KEY", loaded)
                self.assertEqual(mask_secret(os.environ["DEEPSEEK_API_KEY"]), "sk-123...cdef")
            finally:
                os.environ.pop("DEEPSEEK_API_KEY", None)
                if old is not None:
                    os.environ["DEEPSEEK_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
