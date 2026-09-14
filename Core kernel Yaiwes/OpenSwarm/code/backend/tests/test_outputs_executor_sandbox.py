"""Sandbox escape in the Output backend-code executor (issue #134).

The gate only ever looked at import statements and calls to a bare builtin
name, while the subprocess preamble handed user code live `sys`, `io` and
`builtins`. `sys.modules['os']` therefore scanned clean, and clean means the
`/api/outputs/execute` auto-run path with no consent prompt. Live before the
fix: arbitrary file read, arbitrary file write, and `os.system`, all with
`AST warnings: []`.

The payloads below are the class, not the one string: bare handles, attribute
chains that land on a module, dunder traversal, `getattr` indirection, and
aliasing. The legit block underneath is the other half of the bar; a gate that
warns about `datetime.time` would just train users to click through.

Run:
    backend/.venv/bin/python -m pytest backend/tests/test_outputs_executor_sandbox.py -v
"""

import asyncio
import os
from typing import Any

import pytest

from backend.apps.outputs import executor
from backend.apps.outputs.code_safety import UnsafeCodeError, get_code_warnings
from backend.apps.outputs.executor import execute_backend_code, exec_env


def p_run(coro: Any) -> Any:
    return asyncio.new_event_loop().run_until_complete(coro)


P_ESCAPES = [
    # The reported exploit, verbatim.
    "result = {'escaped': sys.modules['os'].getcwd(), 'uid': sys.modules['os'].getuid()}",
    # The other two handles the preamble left lying around.
    "result = {'x': str(io.open)}",
    "result = {'b': str(builtins.__dict__)}",
    # Attribute chains that land on a module the allowlist withholds.
    "result = {'c': str(json.codecs)}",
    "import random\nresult = {'cwd': random._os.getcwd()}",
    "import collections\nresult = {'m': str(collections._sys.modules)}",
    "import hashlib\nresult = {'h': str(hashlib._hashlib)}",
    "import base64\nresult = {'s': str(base64.struct)}",
    "from json import codecs\nresult = {'c': str(codecs)}",
    # Aliasing the module first.
    "m = json\nresult = {'c': str(m.codecs)}",
    # Dunder traversal.
    "result = {'n': len(().__class__.__bases__[0].__subclasses__())}",
    "f = lambda: 0\nresult = {'g': str(f.__globals__)}",
    "result = {'i': str(__import__('os'))}",
    # exec/eval/compile survive in the subprocess (the import machinery needs them), so the gate is the only thing standing here.
    "exec('import os')\nresult = {}",
    "result = {'e': eval('__import__(\"os\").getcwd()')}",
    "result = {'f': open('/etc/hosts').read()}",
    # getattr indirection, literal and computed.
    "result = {'c': str(getattr(json, 'codecs'))}",
    "n = 'codecs'\nresult = {'c': str(getattr(json, n))}",
    "result = {'c': str(getattr((), '__class__'))}",
    # Namespace grabs.
    "result = {'g': str(globals())}",
    "result = {'v': str(vars())}",
    "result = {'l': str(locals())}",
]

P_LEGIT = [
    'import math, json\nresult = {"a": math.floor(1.9), "b": json.dumps([1, 2])}',
    # datetime.time is a CLASS, not the `time` module: a name-matching gate would flag it.
    'import datetime\nresult = {"t": datetime.time(12, 0).isoformat()}',
    'import collections\nresult = {"c": dict(collections.Counter("aab"))}',
    'import collections.abc\nresult = {"ok": isinstance({}, collections.abc.Mapping)}',
    'import re\nresult = {"m": re.findall(r"\\d+", "a1b22")}',
    'import csv\nresult = {"rows": [r for r in csv.reader("a,b\\n1,2".splitlines())]}',
    'import statistics\nresult = {"mean": statistics.mean([1, 2, 3])}',
    'import textwrap\nresult = {"w": textwrap.wrap("word " * 20, 10)}',
    'import decimal\nresult = {"d": str(decimal.Decimal("1.10") + decimal.Decimal("2.20"))}',
    'import uuid\nresult = {"u": str(uuid.uuid5(uuid.NAMESPACE_DNS, "x"))}',
    # dataclasses and namedtuple exec their generated methods, so they prove the builtins scrub left the plumbing alone.
    'import dataclasses\n@dataclasses.dataclass\nclass Row:\n    n: int\nresult = dataclasses.asdict(Row(1))',
    'import collections\nPoint = collections.namedtuple("Point", "x y")\nresult = {"s": sum(Point(1, 2))}',
    'import functools, operator\nresult = {"s": functools.reduce(operator.add, [1, 2, 3])}',
    'from json import dumps\nresult = {"j": dumps({"a": 1})}',
    'from math import *\nresult = {"p": floor(pi)}',
    'if __name__ == "__main__":\n    pass\nresult = {"ok": True}',
    'result = {"n": len(input_data), "keys": sorted(input_data)}',
    'result = {"v": getattr(input_data, "get")("missing", 7)}',
]


# --- the gate must see every escape -----------------------------------------

@pytest.mark.parametrize("code", P_ESCAPES)
def test_escape_is_warned(code: str) -> None:
    assert get_code_warnings(code), f"no warning for: {code!r}"


@pytest.mark.parametrize("code", P_ESCAPES)
def test_escape_is_refused_before_it_runs(code: str) -> None:
    with pytest.raises(UnsafeCodeError):
        p_run(execute_backend_code(code, {}))


# --- and must stay quiet about ordinary data shaping -------------------------

@pytest.mark.parametrize("code", P_LEGIT)
def test_legit_code_is_clean(code: str) -> None:
    assert get_code_warnings(code) == []


@pytest.mark.parametrize("code", P_LEGIT)
def test_legit_code_still_runs(code: str) -> None:
    out = p_run(execute_backend_code(code, {"a": 1}))
    assert isinstance(out.result, dict) and out.result


def test_syntax_error_is_reported_not_raised() -> None:
    assert get_code_warnings("result = {")[0].startswith("Syntax error")


def test_print_output_is_still_captured() -> None:
    out = p_run(execute_backend_code('print("hi")\nresult = {"ok": 1}', {}))
    assert out.stdout.strip() == "hi"
    assert out.result == {"ok": 1}


# --- second wall: the subprocess itself, with the gate bypassed ---------------

@pytest.fixture
def gate_bypassed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend a future payload beats the static gate, and check the subprocess
    still has nothing to grab. Defense in depth is only real if it holds alone."""
    monkeypatch.setattr(executor, "validate_code_safety", lambda code: None)


@pytest.mark.parametrize("handle", ["sys", "io", "builtins"])
def test_module_handles_are_gone_from_the_subprocess(gate_bypassed: None, handle: str) -> None:
    with pytest.raises(RuntimeError) as e:
        p_run(execute_backend_code(f"result = {{'x': str({handle})}}", {}))
    assert "NameError" in str(e.value)


def test_open_builtin_is_gone_from_the_subprocess(gate_bypassed: None) -> None:
    with pytest.raises(RuntimeError) as e:
        p_run(execute_backend_code("result = {'x': open('/etc/hosts').read()}", {}))
    assert "NameError" in str(e.value)


def test_no_credentials_or_shell_reachable_when_not_approved(gate_bypassed: None, tmp_path: Any) -> None:
    """The end-to-end version of the report: read HOME, then shell out."""
    marker = tmp_path / "pwned.txt"
    code = (
        "os_mod = sys.modules['os']\n"
        f"result = {{'home': os_mod.environ.get('HOME'), 'rc': os_mod.system('echo x > {marker}')}}"
    )
    with pytest.raises(RuntimeError):
        p_run(execute_backend_code(code, {}))
    assert not marker.exists()


def test_sandboxed_env_carries_no_path_or_home() -> None:
    env = exec_env(approved=False)
    assert "PATH" not in env and "HOME" not in env


def test_approved_env_inherits_but_scrubs_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-not-leak")
    monkeypatch.setenv("OPENSWARM_AUTH_TOKEN", "should-not-leak")
    env = exec_env(approved=True)
    assert env.get("PATH") == os.environ.get("PATH")
    assert "ANTHROPIC_API_KEY" not in env and "OPENSWARM_AUTH_TOKEN" not in env


def test_approved_run_still_gets_its_escape_hatch() -> None:
    """The HITL "Run Anyway" path must keep working, or the fix just breaks the
    feature instead of securing it."""
    out = p_run(execute_backend_code("import os\nresult = {'sep': os.sep}", {}, approved=True))
    assert out.result == {"sep": os.sep}
