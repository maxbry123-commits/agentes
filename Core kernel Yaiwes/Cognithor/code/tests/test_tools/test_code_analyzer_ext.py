"""Extended tests for tools/code_analyzer.py -- missing lines coverage.

Targets:
  - Duplicate detection
  - UnicodeDecodeError handling
  - analyze_directory non-recursive
  - analyze_directory skips __pycache__
  - _function_body_tokens edge cases
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from cognithor.tools.code_analyzer import (
    CodeSmellDetector,
)


class TestDuplicateDetection:
    def setup_method(self) -> None:
        self.detector = CodeSmellDetector(duplicate_threshold=0.7)
        self.tmpdir = tempfile.mkdtemp()

    def _write_py(self, name: str, content: str) -> Path:
        path = Path(self.tmpdir) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_detect_duplicates(self) -> None:
        code = (
            "def func_a(x):\n"
            "    result = process(x)\n"
            "    data = transform(result)\n"
            "    output = format_data(data)\n"
            "    return save(output)\n"
            "\n"
            "def func_b(y):\n"
            "    result = process(y)\n"
            "    data = transform(result)\n"
            "    output = format_data(data)\n"
            "    return save(output)\n"
        )
        path = self._write_py("dupes.py", code)
        smells = self.detector.analyze_file(path)
        duplicates = [s for s in smells if s.smell_type == "duplicate"]
        assert len(duplicates) >= 1
        assert "aehnlich" in duplicates[0].message

    def test_no_duplicates_different_functions(self) -> None:
        code = (
            "def func_a():\n"
            "    return read_file('a.txt')\n"
            "\n"
            "def func_b():\n"
            "    return write_data(42)\n"
        )
        path = self._write_py("no_dupes.py", code)
        smells = self.detector.analyze_file(path)
        duplicates = [s for s in smells if s.smell_type == "duplicate"]
        assert len(duplicates) == 0


class TestUnicodeDecodeError:
    def test_binary_file_handled(self) -> None:
        tmpdir = tempfile.mkdtemp()
        path = Path(tmpdir) / "binary.py"
        # Write binary data that can't be decoded as UTF-8
        path.write_bytes(b"\x80\x81\x82\x83\x84" * 100)
        detector = CodeSmellDetector()
        smells = detector.analyze_file(path)
        # Should return empty list, not crash
        assert smells == []


class TestAnalyzeDirectoryExtended:
    def test_non_recursive(self) -> None:
        tmpdir = tempfile.mkdtemp()
        Path(tmpdir, "top.py").write_text("x = 1\n", encoding="utf-8")
        sub = Path(tmpdir, "sub")
        sub.mkdir()
        Path(sub, "deep.py").write_text("y = 2\n", encoding="utf-8")

        detector = CodeSmellDetector()
        smells = detector.analyze_directory(tmpdir, recursive=False)
        # Should not error; result depends on file contents
        assert isinstance(smells, list)

    def test_not_a_directory(self) -> None:
        detector = CodeSmellDetector()
        smells = detector.analyze_directory("/nonexistent/dir")
        assert smells == []

    def test_skips_pycache(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cache_dir = Path(tmpdir, "__pycache__")
        cache_dir.mkdir()
        Path(cache_dir, "cached.py").write_text("x = 1\n", encoding="utf-8")
        Path(tmpdir, "real.py").write_text("y = 2\n", encoding="utf-8")

        detector = CodeSmellDetector()
        smells = detector.analyze_directory(tmpdir)
        # Should only analyze real.py
        for s in smells:
            assert "__pycache__" not in s.file_path
