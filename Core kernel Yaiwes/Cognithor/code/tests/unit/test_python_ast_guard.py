"""Tests for jarvis.security.python_ast_guard — AST-based Python security analysis."""

from __future__ import annotations

import pytest

from cognithor.security.python_ast_guard import analyse_python, is_safe_python


class TestSafeCode:
    """Code that must pass without violations."""

    @pytest.mark.parametrize(
        "code",
        [
            "x = 1 + 2",
            "print('hello')",
            "result = [i**2 for i in range(10)]",
            "data = {'key': 'value'}",
            "import json\njson.loads('{}')",
            "import math\nmath.sqrt(4)",
            "from datetime import datetime\ndatetime.now()",
            "from collections import Counter\nCounter([1,2,3])",
            "import re\nre.findall(r'\\d+', 'abc123')",
            "with open('file.txt') as f:\n    content = f.read()",
            "class Foo:\n    def bar(self): return 42",
            "def add(a, b): return a + b",
            "names = sorted(['c', 'a', 'b'])",
            "total = sum([1, 2, 3])",
        ],
    )
    def test_safe_code_passes(self, code: str):
        violations = analyse_python(code)
        assert violations == [], f"Unexpected violations for safe code: {violations}"
        assert is_safe_python(code) is True


class TestDangerousImports:
    """Import of restricted modules must be caught."""

    @pytest.mark.parametrize(
        "code,module",
        [
            ("import os", "os"),
            ("import sys", "sys"),
            ("import subprocess", "subprocess"),
            ("import shutil", "shutil"),
            ("import socket", "socket"),
            ("import ctypes", "ctypes"),
            ("import pickle", "pickle"),
            ("import marshal", "marshal"),
            ("from os import system", "os"),
            ("from os.path import join", "os"),
            ("from subprocess import run", "subprocess"),
            ("from shutil import rmtree", "shutil"),
            ("import os, json", "os"),
            ("from multiprocessing import Process", "multiprocessing"),
        ],
    )
    def test_dangerous_import_detected(self, code: str, module: str):
        violations = analyse_python(code)
        assert len(violations) >= 1
        assert any(module in v.detail for v in violations)
        assert is_safe_python(code) is False


class TestDangerousBuiltins:
    """exec/eval/compile/__import__ must be caught."""

    @pytest.mark.parametrize(
        "code,builtin",
        [
            ("exec('print(1)')", "exec"),
            ("eval('1+1')", "eval"),
            ("compile('pass', '<>', 'exec')", "compile"),
            ("__import__('os')", "__import__"),
            ("x = eval(input())", "eval"),
            ("exec(open('file').read())", "exec"),
        ],
    )
    def test_dangerous_builtin_detected(self, code: str, builtin: str):
        violations = analyse_python(code)
        assert len(violations) >= 1
        assert any(builtin in v.detail for v in violations)
        assert is_safe_python(code) is False


class TestBypassDetection:
    """Bypass attempts that regex would miss but AST catches."""

    def test_getattr_os_bypass(self):
        """getattr(os, "system")("cmd") — the primary regex bypass."""
        code = 'import os\ngetattr(os, "system")("whoami")'
        violations = analyse_python(code)
        assert len(violations) >= 2  # import os + getattr(os, ...)
        rules = {v.rule for v in violations}
        assert "dangerous-getattr" in rules

    def test_getattr_with_chr_bypass(self):
        """getattr(os, chr(115)+chr(121)+...) — string construction bypass."""
        code = "import os\ngetattr(os, chr(115) + chr(121) + chr(115))"
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-getattr" for v in violations)

    def test_dunder_import_bypass(self):
        """__import__("os").system("cmd") — dynamic import."""
        code = '__import__("os").system("cmd")'
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-builtin" for v in violations)

    def test_string_concat_import(self):
        """__import__("o" + "s") — string concat in __import__."""
        code = '__import__("o" + "s")'
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-builtin" for v in violations)

    def test_os_system_call(self):
        """os.system("cmd") — direct dangerous call."""
        code = 'import os\nos.system("whoami")'
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-call" for v in violations)

    def test_subprocess_run(self):
        code = 'import subprocess\nsubprocess.run(["ls"])'
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-call" for v in violations)

    def test_setattr_on_os(self):
        code = "import os\nsetattr(os, 'environ', {})"
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-setattr" for v in violations)

    def test_builtins_dunder_import_attribute(self):
        code = 'import builtins\nbuiltins.__import__("os")'
        violations = analyse_python(code)
        assert any(v.rule == "dangerous-dunder-import" for v in violations)


class TestStrictMode:
    """Strict mode catches class hierarchy escape attempts."""

    def test_subclasses_access_strict(self):
        code = "''.__class__.__subclasses__()"
        violations = analyse_python(code, strict=True)
        assert any(v.rule == "dangerous-dunder-access" for v in violations)

    def test_mro_access_strict(self):
        code = "object.__mro__"
        violations = analyse_python(code, strict=True)
        assert any(v.rule == "dangerous-dunder-access" for v in violations)

    def test_subclasses_not_caught_in_normal_mode(self):
        code = "''.__class__.__subclasses__()"
        violations = analyse_python(code, strict=False)
        assert not any(v.rule == "dangerous-dunder-access" for v in violations)


class TestSyntaxErrors:
    """Unparseable code is treated as unsafe."""

    def test_syntax_error_returns_false(self):
        assert is_safe_python("def (broken syntax") is False

    def test_empty_code_is_safe(self):
        assert is_safe_python("") is True
        assert is_safe_python("# just a comment") is True
