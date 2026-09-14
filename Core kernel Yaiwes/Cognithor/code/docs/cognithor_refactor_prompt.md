# Cognithor — Comprehensive Refactor Prompt (Reddit Feedback Implementation)

## Project Context

You are working on **Cognithor** — an open-source, local-first Agent Operating System.
- **Scale**: ~200,000+ LOC production code, ~100,000+ LOC test suite
- **Stack**: Python 3.12+, Apache 2.0 license
- **Current version**: v0.57.x → targeting v1.0.0
- **Architecture**: PGE Trinity (Planner → Gatekeeper → Executor), 5-tier cognitive memory,
  16 LLM providers, 17 channels, 123 MCP tools, A2A protocol, knowledge vault, voice,
  browser automation, computer use, Deep Research v2, VS Code extension, SSH backend,
  multi-agent support, Flutter Command Center
- **CI status**: 11,609+ tests at 89% coverage
- **Repo**: github.com/Alex8791-cyber/cognithor

This prompt implements **five critical improvements** identified by an external reviewer
("HoraceAndTheRest") in a public code review. Every task must be applied carefully given
the large codebase — do not break existing tests. Run the full test suite after each
distinct change set before proceeding to the next item.

---

## ITEM 1 — Complete the Rename: `jarvis` → `cognithor` (Single Atomic PR)

### Background
The codebase still contains references to the legacy name `jarvis` (the project's internal
working name before the public rename). This is the single most visible signal to external
contributors that the public-facing brand is a marketing layer pasted over an older
codebase, not a coherent project. It must be fully resolved in one atomic PR.

### Step 1 — Filesystem rename
```bash
git mv src/jarvis src/cognithor
```
If `src/jarvis` does not exist as a top-level directory, search for all paths containing
`jarvis` as a path component:
```bash
find . -not -path './.git/*' -iname '*jarvis*'
```
Rename every file and directory found, preserving the relative structure.

### Step 2 — Import replacement (every Python file)
Run the following across the entire repository:
```bash
grep -rl "from jarvis" . --include="*.py" | xargs sed -i 's/from jarvis/from cognithor/g'
grep -rl "import jarvis" . --include="*.py" | xargs sed -i 's/import jarvis/import cognithor/g'
grep -rl '"jarvis"' . --include="*.py" | xargs sed -i 's/"jarvis"/"cognithor"/g'
grep -rl "'jarvis'" . --include="*.py" | xargs sed -i "s/'jarvis'/'cognithor'/g"
```

### Step 3 — Environment variable prefix
Find every env-var that uses the `JARVIS_` prefix:
```bash
grep -rn "JARVIS_" . --include="*.py" --include="*.env*" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.toml"
```
Replace all `JARVIS_` prefixes with `COGNITHOR_` in:
- All Python source files
- All `.env`, `.env.example`, `.env.template` files
- All shell scripts
- All CI/CD YAML files
- `pyproject.toml`, `setup.cfg`, `setup.py`

### Step 4 — Workspace / config path migration
```bash
grep -rn "\.jarvis" . --include="*.py" --include="*.sh" --include="*.md"
```
Replace every occurrence of `~/.cognithor` (and `$HOME/.jarvis`, `os.path.join(home, ".cognithor")`,
`Path.home() / ".cognithor"`, etc.) with `~/.cognithor`.

Update the default workspace path constant wherever it is defined
(likely in a `config.py`, `constants.py`, or `settings.py`).

Also update the migration/upgrade path: if a user has an existing `~/.cognithor` directory,
the startup code should detect it and emit a deprecation warning:
```python
import warnings
from pathlib import Path

_OLD_WORKSPACE = Path.home() / ".cognithor"
_NEW_WORKSPACE = Path.home() / ".cognithor"

if _OLD_WORKSPACE.exists() and not _NEW_WORKSPACE.exists():
    warnings.warn(
        f"Legacy workspace detected at {_OLD_WORKSPACE}. "
        f"Please migrate to {_NEW_WORKSPACE}. "
        "Automatic migration will be removed in v1.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )
```

### Step 5 — Documentation and non-Python files
```bash
grep -rn "jarvis" . --include="*.md" --include="*.rst" --include="*.txt" \
  --include="*.toml" --include="*.yaml" --include="*.yml" \
  --include="*.json" --include="*.cfg" --include="Dockerfile*" \
  --include="docker-compose*" --include="Makefile" \
  | grep -vi ".git"
```
Replace every case-sensitive and case-insensitive occurrence of `jarvis` / `Jarvis` /
`JARVIS` with the appropriate `cognithor` / `Cognithor` / `COGNITHOR` variant.

### Step 6 — Verification
After all changes:
```bash
# Must return zero results (excluding .git and this prompt file itself)
grep -rn "jarvis" . --include="*.py" --include="*.md" --include="*.toml" \
  --include="*.yaml" --include="*.yml" --include="*.sh" --include="*.json" \
  | grep -v ".git" | grep -vi "cognithor"   # allow "cognithor" mentions

# Run full test suite
pytest tests/ -x -q --tb=short
```

---

## ITEM 2 — README Accuracy Overhaul

### Background
The README currently makes several claims that do not match the actual code behaviour.
External contributors and users will notice the discrepancy immediately. The goal is not
to downgrade Cognithor — it is to ensure every claim is verifiable and reproducible.

### 2a — Sandbox / isolation claims

**Current (wrong) claim**: The README implies a four-tier sandbox that "always blocks"
dangerous operations.

**Correct reality** (verify in source before writing):
Cognithor uses:
- `bubblewrap` (bwrap) on Linux when available in PATH
- `firejail` on Linux as fallback when bwrap is unavailable
- `subprocess` + a configurable timeout as the final fallback on all other platforms
  (macOS, Windows, minimal Linux containers)

**Required README change**: Replace any "always blocks" or "four-tier sandbox" language with
an accurate description of the actual isolation chain. Template:

```markdown
## Sandbox isolation

Cognithor uses the best available isolation mechanism for the current platform:

| Platform | Mechanism | Isolation level |
|---|---|---|
| Linux (bwrap available) | bubblewrap (bwrap) | Strong: namespaces, seccomp |
| Linux (firejail available) | firejail | Medium: profile-based |
| All other platforms | subprocess + timeout | Minimal: process boundary only |

The active sandbox mechanism is logged at startup. To check yours:
```
cognithor doctor --check sandbox
```
No claims are made that execution is "always blocked" — the actual protection
depends on the platform and installed tools.
```

### 2b — Gatekeeper "always blocks" language

Find and audit every use of "always" or "guaranteed" in relation to the Gatekeeper in the
README, ARCHITECTURE.md, and any other docs. Replace each instance with:
- The actual condition under which blocking occurs
- The condition under which it might not block (e.g., if a plugin overrides the hook)
- A reference to the relevant source file and function for traceability

### 2c — Default install / extras

**Required change**: Make it explicit in the README that a default `pip install cognithor`
installs only the core engine (PGE, CLI, Ollama backend). All channels and additional
providers require named extras. Example format:

```markdown
## Installation

```bash
pip install cognithor               # Core engine only: PGE, CLI, Ollama
pip install cognithor[slack]        # + Slack channel
pip install cognithor[discord]      # + Discord channel
pip install cognithor[openai]       # + OpenAI provider
pip install cognithor[all]          # Everything (large install)
```

Verify the extras are correctly declared in `pyproject.toml` / `setup.cfg`. If an
extra is listed in the README but not in `pyproject.toml`, either add it or remove
the README claim.

### 2d — Model name table

The current model-name table lists human-friendly names that may not match what each
vendor's `/models` endpoint actually returns. This silently breaks provider integrations
when names drift.

**Required changes**:
1. Replace the static model-name table with strings **actually returned by each vendor's
   models endpoint** (verify by running `cognithor list-models --provider <name>` or
   inspecting the provider adapter code for the hardcoded model IDs).
2. Add the following CI job to `.github/workflows/model-freshness.yml`:

```yaml
name: Model list freshness check
on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday at 09:00 UTC
  workflow_dispatch:

jobs:
  check-models:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install cognithor[all]
      - name: Verify model list matches README
        run: python scripts/check_model_table.py --readme README.md
```

Create `scripts/check_model_table.py` that:
- Reads the model table from the README (parse the markdown)
- Calls each provider's models endpoint (or reads from the provider adapter's MODEL_LIST constant)
- Compares actual model IDs to documented ones
- Exits non-zero with a diff if they diverge

### 2e — Clone URL

Verify the clone URL in the README is exactly:
```
git clone https://github.com/Alex8791-cyber/cognithor.git
```
Fix any incorrect URL (wrong username, wrong repo name, using SSH where HTTPS is shown,
or vice versa).

---

## ITEM 3 — Replace Silent-Failure Handlers with Loud Warnings + `make health`

### Background
The current codebase uses `except Exception: pass` (or similar silent swallows) around
optional subsystem initialisation. In production this makes it **impossible to distinguish**
"all defences active" from "Layer 1 is completely missing due to an import error".
This is a critical observability gap.

### Step 1 — Introduce `_safe_call` helper

Create or update `cognithor/core/safe_call.py`:

```python
"""
_safe_call — wraps optional subsystem initialisation with structured failure tracking.

Usage:
    result = _safe_call("hashline_guard", hashline_guard.init, config)

Any exception is caught, logged at WARNING level, and counted in
_FAILURE_REGISTRY. The registry is exposed via `get_failure_report()` and
surfaced by `cognithor doctor --health`.
"""
from __future__ import annotations

import logging
import threading
import traceback
from typing import Any, Callable

logger = logging.getLogger(__name__)

_FAILURE_REGISTRY: dict[str, list[str]] = {}
_lock = threading.Lock()


def _safe_call(name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any | None:
    """
    Call fn(*args, **kwargs). On any exception:
      - emit a WARNING log with the full traceback
      - record the failure in _FAILURE_REGISTRY[name]
      - return None

    On success return the function's return value unchanged.
    """
    try:
        return fn(*args, **kwargs)
    except Exception:  # noqa: BLE001
        tb = traceback.format_exc()
        logger.warning(
            "Optional subsystem '%s' failed to initialise:\n%s",
            name,
            tb,
        )
        with _lock:
            _FAILURE_REGISTRY.setdefault(name, []).append(tb)
        return None


def get_failure_report() -> dict[str, list[str]]:
    """Return a snapshot of all recorded failures, keyed by subsystem name."""
    with _lock:
        return dict(_FAILURE_REGISTRY)


def has_failures() -> bool:
    """Return True if any subsystem has a non-zero failure count."""
    with _lock:
        return bool(_FAILURE_REGISTRY)
```

### Step 2 — Audit and replace silent failure patterns

Search the entire codebase for the following patterns and replace each with `_safe_call`:

```bash
# Find all silent exception swallows
grep -rn "except Exception" . --include="*.py" | grep -v "_safe_call" | grep -v "test_"
grep -rn "except Exception.*pass" . --include="*.py"
grep -rn "except.*:\s*$" . --include="*.py" -A 1 | grep -B 1 "^\s*pass$"
grep -rn "except.*:\s*$" . --include="*.py" -A 1 | grep -B 1 "^\s*logger\."
grep -rn "except.*:\s*$" . --include="*.py" -A 1 | grep -B 1 "^\s*log\."
```

For **each match** that wraps an optional subsystem initialisation, plugin load, or
capability bootstrap:

**Before:**
```python
try:
    hashline_guard.init(config)
except Exception:
    pass
```

**After:**
```python
from cognithor.core.safe_call import _safe_call
_safe_call("hashline_guard", hashline_guard.init, config)
```

**Do NOT replace** `except Exception` blocks that:
- Are in test files (keep test isolation)
- Are in top-level `__main__` error handlers (keep user-facing error messages)
- Already re-raise or have non-trivial recovery logic
- Are inside `_safe_call` itself

For each converted location, add a comment:
```python
# _safe_call: failure is logged + counted; check `cognithor doctor --health`
```

### Step 3 — `make health` / `cognithor doctor --health`

**CLI addition** — add a `health` subcommand to the Cognithor CLI:

```python
# cognithor/cli/health.py
import sys
from cognithor.core.safe_call import get_failure_report, has_failures

def cmd_health() -> int:
    """
    Print a health report of all optional subsystems.
    Exit 0 if all subsystems are healthy, 1 if any have failures.
    """
    report = get_failure_report()
    if not report:
        print("✓ All optional subsystems initialised successfully.")
        return 0

    print(f"✗ {len(report)} subsystem(s) failed to initialise:\n")
    for name, tracebacks in report.items():
        print(f"  [{name}]  {len(tracebacks)} failure(s)")
        for i, tb in enumerate(tracebacks, 1):
            print(f"    --- Traceback {i} ---")
            for line in tb.strip().splitlines():
                print(f"    {line}")
        print()

    print(
        "TIP: Run `cognithor doctor --fix` to attempt automatic dependency resolution, "
        "or check the logs above for the root cause."
    )
    return 1


if __name__ == "__main__":
    sys.exit(cmd_health())
```

**Makefile addition:**
```makefile
.PHONY: health
health:  ## Check optional subsystem health
	cognithor doctor --health
```

### Step 4 — Tests

For each converted `_safe_call` site, ensure there is a unit test that verifies:
1. A subsystem that raises during init records a failure in the registry
2. The failure is surfaced by `get_failure_report()`
3. The main execution path continues despite the failure
4. `has_failures()` returns `True`

Template test:
```python
from cognithor.core.safe_call import _safe_call, get_failure_report, _FAILURE_REGISTRY

def test_safe_call_records_failure(monkeypatch):
    _FAILURE_REGISTRY.clear()

    def broken_init():
        raise RuntimeError("simulated init failure")

    result = _safe_call("test_subsystem", broken_init)

    assert result is None
    report = get_failure_report()
    assert "test_subsystem" in report
    assert len(report["test_subsystem"]) == 1
    assert "RuntimeError" in report["test_subsystem"][0]
```

---

## ITEM 4 — Scope Reduction + Real CI (v0.1.0 Milestone)

### Background
The reviewer makes a crucial credibility argument: a focused 8,000-line repo with live CI
is more credible to external contributors than a 200,000-line repo with no running CI.
We do not need to delete code — we need to restructure so the core is verifiable and
optional parts are clearly labelled.

### Step 1 — Identify and tag optional/contrib modules

Create the following directory structure:

```
cognithor/
  core/           ← Keep: PGE Trinity, memory, CLI, Ollama backend
  channels/       ← Optional: each channel becomes a separate extras package
  providers/      ← Optional: each non-Ollama provider becomes a separate extras package
contrib/          ← Community / unmaintained integrations, clearly labelled
```

Add a `contrib/README.md`:
```markdown
# contrib/

This directory contains community-contributed integrations and experimental features.
These modules are **not covered by the core test suite** and carry no maintenance
guarantees. Use at your own risk.

To propose a contrib module for promotion to core, open an issue with benchmark results
and a test coverage report.
```

For each module moved to `contrib/`, add a file-level docstring:
```python
"""
CONTRIB MODULE — Unmaintained. Not covered by core CI.
Use at your own risk. See contrib/README.md.
"""
```

### Step 2 — Real GitHub Actions CI

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Lint (ruff)
        run: ruff check cognithor/ --output-format=github

      - name: Type check (mypy)
        run: mypy cognithor/ --ignore-missing-imports --no-error-summary

      - name: Run tests
        run: |
          pytest tests/ \
            -x \
            --tb=short \
            --cov=cognithor \
            --cov-report=xml \
            --cov-report=term-missing \
            -q

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: false

  security:
    name: Security scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install bandit[toml] safety
      - run: bandit -r cognithor/ -ll -q
      - run: safety check --short-report
```

### Step 3 — Replace static shields.io badges with live badges

In `README.md`, replace any static badge images with live ones:

```markdown
[![CI](https://github.com/Alex8791-cyber/cognithor/actions/workflows/ci.yml/badge.svg)](https://github.com/Alex8791-cyber/cognithor/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Alex8791-cyber/cognithor/graph/badge.svg)](https://codecov.io/gh/Alex8791-cyber/cognithor)
[![PyPI version](https://img.shields.io/pypi/v/cognithor.svg)](https://pypi.org/project/cognithor/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
```

Remove or replace any badge that shows a hardcoded passing/green state without a live
CI backend to back it up.

### Step 4 — Drop the `Development Status :: 5` trove classifier

In `pyproject.toml`, remove or downgrade:
```toml
# REMOVE this line until v1.0.0 is tagged and CI is green:
# "Development Status :: 5 - Production/Stable",

# ADD instead:
"Development Status :: 4 - Beta",
```

Only restore `:: 5 - Production/Stable` after:
- v1.0.0 is tagged
- CI is green
- All tests pass on Python 3.12 and 3.13

### Step 5 — Tag v0.1.0

After CI is green and the core passes:
```bash
git tag -a v0.1.0 -m "First tagged release: core PGE + memory + CLI + Ollama"
git push origin v0.1.0
```

This signals to the community that the project has a stable baseline, even though it is
not yet feature-complete.

---

## ITEM 5 — Replace Regex-Based Security Analysis with AST Parsing

### Background
The reviewer identified two critical bypasses in the current implementation:

**Python bypass example:**
```python
# _DANGEROUS_PYTHON_PATTERNS regex is bypassed by:
getattr(os, "sys" + "tem")
getattr(os, chr(115) + chr(121) + chr(115) + chr(116) + chr(101) + chr(109))
__import__("o" + "s").system("rm -rf /")
```

**Shell bypass example:**
```bash
# Regex check on file-commands is bypassed by:
ec''ho hello      # command substitution inside the command
ls${IFS}&&${IFS}rm -rf /   # chained operators
$(printf '%s' 'rm' '-rf' '/')   # nested substitution
```

The fix is ~200 lines total using proper parsing instead of pattern matching.

### Step 1 — Python AST-based analyser

Create `cognithor/security/python_ast_guard.py`:

```python
"""
Python code safety analyser using AST parsing + NodeVisitor.

Replaces the regex-based _DANGEROUS_PYTHON_PATTERNS approach.
Analyses the AST, not the text — bypasses via string concatenation,
getattr, chr(), __import__(), etc. are detected at the call-site level.
"""
from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Violation:
    lineno: int
    col_offset: int
    rule: str
    detail: str


# Allowlist: fully-qualified calls that are PERMITTED.
# Everything not on this list that resolves to a dangerous category is blocked.
PERMITTED_CALLS: frozenset[str] = frozenset(
    {
        "print",
        "len",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sorted",
        "reversed",
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "float",
        "bool",
        "type",
        "isinstance",
        "issubclass",
        "hasattr",
        "getattr",   # allowed ONLY when first arg is not os/sys/subprocess
        "setattr",
        "delattr",
        "repr",
        "vars",
        "dir",
        "help",
        "id",
        "hash",
        "abs",
        "round",
        "min",
        "max",
        "sum",
        "open",      # allowed; file I/O is controlled separately
        "json.loads",
        "json.dumps",
        "pathlib.Path",
        "datetime.datetime",
        "collections.defaultdict",
        "itertools.chain",
    }
)

DANGEROUS_MODULES: frozenset[str] = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "ctypes",
        "signal",
        "multiprocessing",
        "threading",
        "importlib",
        "runpy",
        "code",
        "codeop",
        "pty",
        "tty",
        "termios",
        "fcntl",
        "resource",
        "mmap",
        "pickle",
        "marshal",
    }
)

DANGEROUS_BUILTINS: frozenset[str] = frozenset(
    {
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",    # conditionally dangerous; override in strict mode
        "globals",
        "locals",
        "vars",    # conditionally dangerous
        "breakpoint",
    }
)


class _ASTGuardVisitor(ast.NodeVisitor):
    """Traverse the AST and collect Violations."""

    DANGEROUS_MODULES: ClassVar[frozenset[str]] = DANGEROUS_MODULES
    DANGEROUS_BUILTINS: ClassVar[frozenset[str]] = DANGEROUS_BUILTINS

    def __init__(self, strict: bool = False) -> None:
        self.violations: list[Violation] = []
        self.strict = strict

    # --- Import checks ---

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in self.DANGEROUS_MODULES:
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-import",
                        detail=f"Import of restricted module: {alias.name!r}",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        top = module.split(".")[0]
        if top in self.DANGEROUS_MODULES:
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-import-from",
                    detail=f"Import from restricted module: {module!r}",
                )
            )
        self.generic_visit(node)

    # --- Call checks ---

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        # exec()/eval()/compile()/__import__() as bare names
        if isinstance(func, ast.Name) and func.id in self.DANGEROUS_BUILTINS:
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-builtin",
                    detail=f"Call to dangerous builtin: {func.id!r}",
                )
            )

        # getattr(os, ...) / getattr(sys, ...) etc.
        if (
            isinstance(func, ast.Name)
            and func.id == "getattr"
            and len(node.args) >= 1
        ):
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in self.DANGEROUS_MODULES:
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-getattr",
                        detail=(
                            f"getattr() on restricted module {first.id!r} — "
                            "bypasses import restrictions."
                        ),
                    )
                )

        # Attribute access on dangerous modules: os.system, subprocess.run, etc.
        if isinstance(func, ast.Attribute):
            if (
                isinstance(func.value, ast.Name)
                and func.value.id in self.DANGEROUS_MODULES
            ):
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-call",
                        detail=(
                            f"Call to {func.value.id!r}.{func.attr!r} on "
                            "restricted module."
                        ),
                    )
                )

        self.generic_visit(node)


def analyse_python(source: str, strict: bool = False) -> list[Violation]:
    """
    Parse `source` as Python code and return a list of security Violations.
    Returns an empty list if the source is safe.
    Raises SyntaxError if the source cannot be parsed.
    """
    tree = ast.parse(source, mode="exec")
    visitor = _ASTGuardVisitor(strict=strict)
    visitor.visit(tree)
    return visitor.violations


def is_safe_python(source: str, strict: bool = False) -> bool:
    """Return True only if analyse_python finds zero violations."""
    try:
        return len(analyse_python(source, strict=strict)) == 0
    except SyntaxError:
        return False  # unparseable code is treated as unsafe
```

### Step 2 — Shell AST-based analyser

Install `bashlex` (add to `pyproject.toml` extras or `[dev]` dependencies):
```toml
[project.optional-dependencies]
security = ["bashlex>=0.18"]
```

Create `cognithor/security/shell_ast_guard.py`:

```python
"""
Shell command safety analyser using bashlex AST parsing.

Replaces the regex-based file-command check. bashlex builds a proper
parse tree for bash, detecting command substitution, chained operators,
pipelines, and heredocs that trivially bypass regex approaches.
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:
    import bashlex
    _BASHLEX_AVAILABLE = True
except ImportError:
    _BASHLEX_AVAILABLE = False


@dataclass
class ShellViolation:
    pos: int
    rule: str
    detail: str


# Commands that are never permitted in sandboxed shell execution.
BLOCKED_COMMANDS: frozenset[str] = frozenset(
    {
        "rm",
        "rmdir",
        "dd",
        "mkfs",
        "fdisk",
        "parted",
        "shred",
        "wget",
        "curl",
        "nc",
        "ncat",
        "netcat",
        "ssh",
        "scp",
        "rsync",
        "chmod",
        "chown",
        "sudo",
        "su",
        "doas",
        "pkexec",
        "env",
        "xargs",
        "tee",
        "install",
        "mv",         # can overwrite system files
        "cp",         # can overwrite system files
        "ln",         # can create dangerous symlinks
        "mount",
        "umount",
        "insmod",
        "modprobe",
        "lsmod",
        "systemctl",
        "service",
        "init",
        "kill",
        "killall",
        "pkill",
        "reboot",
        "halt",
        "shutdown",
        "poweroff",
        "crontab",
        "at",
        "batch",
        "python",
        "python3",
        "perl",
        "ruby",
        "node",
        "php",
        "bash",
        "sh",
        "dash",
        "zsh",
        "fish",
        "csh",
        "tcsh",
        "ksh",
        "exec",
        "eval",
        "source",
        ".",          # POSIX source alias
    }
)


class _ShellASTVisitor:
    """Walk a bashlex part tree and collect ShellViolations."""

    def __init__(self) -> None:
        self.violations: list[ShellViolation] = []

    def visit(self, part: "bashlex.ast.node") -> None:
        method = f"visit_{part.kind}"
        getattr(self, method, self.generic_visit)(part)

    def generic_visit(self, part: "bashlex.ast.node") -> None:
        for child in getattr(part, "parts", []):
            self.visit(child)

    def visit_command(self, part: "bashlex.ast.node") -> None:
        if part.parts:
            first = part.parts[0]
            if first.kind == "word":
                cmd = first.word
                if cmd in BLOCKED_COMMANDS:
                    self.violations.append(
                        ShellViolation(
                            pos=part.pos[0],
                            rule="blocked-command",
                            detail=f"Blocked shell command: {cmd!r}",
                        )
                    )
        # Always recurse — even blocked commands may contain substitutions
        # that need to be flagged separately.
        self.generic_visit(part)

    def visit_commandsubstitution(self, part: "bashlex.ast.node") -> None:
        """Flag any $(...) or `...` — command substitution is always suspicious."""
        self.violations.append(
            ShellViolation(
                pos=part.pos[0],
                rule="command-substitution",
                detail=(
                    "Command substitution detected ($(...) or backticks). "
                    "This trivially bypasses command-name checks."
                ),
            )
        )
        self.generic_visit(part)

    def visit_processsubstitution(self, part: "bashlex.ast.node") -> None:
        self.violations.append(
            ShellViolation(
                pos=part.pos[0],
                rule="process-substitution",
                detail="Process substitution detected (<(...) or >(...)).",
            )
        )
        self.generic_visit(part)

    def visit_operator(self, part: "bashlex.ast.node") -> None:
        if part.op in {"&&", "||", ";", "|", "|&"}:
            self.violations.append(
                ShellViolation(
                    pos=part.pos[0],
                    rule="chained-operator",
                    detail=(
                        f"Chained operator {part.op!r} detected. "
                        "Chaining can inject additional commands after a "
                        "seemingly safe first command."
                    ),
                )
            )
        self.generic_visit(part)


def analyse_shell(command: str) -> list[ShellViolation]:
    """
    Parse `command` as bash and return a list of ShellViolations.
    Requires bashlex to be installed.
    Raises ImportError if bashlex is not available.
    Raises bashlex.errors.ParsingError if the command cannot be parsed.
    """
    if not _BASHLEX_AVAILABLE:
        raise ImportError(
            "bashlex is required for shell AST analysis. "
            "Install it with: pip install cognithor[security]"
        )

    parts = bashlex.parse(command)
    visitor = _ShellASTVisitor()
    for part in parts:
        visitor.visit(part)
    return visitor.violations


def is_safe_shell(command: str) -> bool:
    """Return True only if analyse_shell finds zero violations."""
    try:
        return len(analyse_shell(command)) == 0
    except Exception:  # noqa: BLE001 — parse errors = unsafe
        return False
```

### Step 3 — Wire the new analysers into the Gatekeeper

Find the existing Gatekeeper security check (likely in
`cognithor/core/gatekeeper.py` or similar). Replace the call to the old
regex-based `_DANGEROUS_PYTHON_PATTERNS` check and the shell file-command
check with calls to the new AST analysers:

**Before (example pattern):**
```python
if any(re.search(pat, code) for pat in _DANGEROUS_PYTHON_PATTERNS):
    raise SecurityViolation(f"Dangerous pattern detected in code block")
```

**After:**
```python
from cognithor.security.python_ast_guard import analyse_python, Violation
violations = analyse_python(code)
if violations:
    details = "; ".join(v.detail for v in violations)
    raise SecurityViolation(
        f"Security analysis found {len(violations)} violation(s): {details}"
    )
```

**Shell before (example):**
```python
if _file_command_pattern.search(shell_cmd):
    raise SecurityViolation("Blocked file command in shell string")
```

**Shell after:**
```python
from cognithor.security.shell_ast_guard import analyse_shell, ShellViolation
violations = analyse_shell(shell_cmd)
if violations:
    details = "; ".join(v.detail for v in violations)
    raise SecurityViolation(
        f"Shell security analysis found {len(violations)} violation(s): {details}"
    )
```

### Step 4 — Remove the old regex patterns

Once the Gatekeeper is wired to the new AST analysers and all existing security
tests pass, **delete** the following:
- `_DANGEROUS_PYTHON_PATTERNS` list (wherever it is defined)
- Any regex-based file-command check
- Any test that was specifically testing regex bypass-prevention (these were
  testing the wrong abstraction — replace with AST-aware tests)

### Step 5 — AST security tests

Create `tests/security/test_python_ast_guard.py`:

```python
import pytest
from cognithor.security.python_ast_guard import analyse_python, is_safe_python

# --- Should be flagged ---

DANGEROUS_CASES = [
    # Direct import
    ("import os", "dangerous-import"),
    ("import subprocess", "dangerous-import"),
    ("from os import system", "dangerous-import-from"),
    # Builtin abuse
    ("exec('rm -rf /')", "dangerous-builtin"),
    ("eval('__import__(\"os\").system(\"ls\")')", "dangerous-builtin"),
    # getattr bypass
    ("getattr(os, 'system')('ls')", "dangerous-getattr"),
    # String concat bypass — the key test
    ("getattr(os, 'sys' + 'tem')('ls')", "dangerous-getattr"),
    # Attribute call
    ("os.system('ls')", "dangerous-call"),
    ("subprocess.run(['ls'])", "dangerous-call"),
]

@pytest.mark.parametrize("source,expected_rule", DANGEROUS_CASES)
def test_dangerous_code_detected(source, expected_rule):
    violations = analyse_python(source)
    assert any(v.rule == expected_rule for v in violations), (
        f"Expected rule {expected_rule!r} not found in violations for: {source!r}"
    )

# --- Should NOT be flagged ---

SAFE_CASES = [
    "x = 1 + 2",
    "print('hello')",
    "result = [i*2 for i in range(10)]",
    "import json\ndata = json.loads('{}')",
    "from pathlib import Path\np = Path('/tmp/test')",
]

@pytest.mark.parametrize("source", SAFE_CASES)
def test_safe_code_passes(source):
    assert is_safe_python(source), f"Safe code was flagged: {source!r}"

def test_syntax_error_is_unsafe():
    assert not is_safe_python("def broken(: pass")

def test_chr_bypass_is_detected():
    # chr() used to build restricted module names
    source = "getattr(__builtins__, chr(101)+chr(118)+chr(97)+chr(108))('1+1')"
    violations = analyse_python(source)
    assert len(violations) > 0
```

Create `tests/security/test_shell_ast_guard.py`:

```python
import pytest
from cognithor.security.shell_ast_guard import analyse_shell, is_safe_shell

DANGEROUS_SHELL_CASES = [
    # Direct blocked command
    ("rm -rf /", "blocked-command"),
    ("sudo apt-get install vim", "blocked-command"),
    # Command substitution bypass
    ("$(echo hello)", "command-substitution"),
    ("`echo hello`", "command-substitution"),
    # Chained operator bypass
    ("ls && rm -rf /", "chained-operator"),
    ("ls; rm -rf /", "chained-operator"),
    ("ls || rm -rf /", "chained-operator"),
    # Combined bypass: the critical test case from the reviewer
    ("ls${IFS}&&${IFS}rm -rf /", "chained-operator"),
]

@pytest.mark.parametrize("cmd,expected_rule", DANGEROUS_SHELL_CASES)
def test_dangerous_shell_detected(cmd, expected_rule):
    pytest.importorskip("bashlex")
    violations = analyse_shell(cmd)
    assert any(v.rule == expected_rule for v in violations), (
        f"Expected rule {expected_rule!r} not found for: {cmd!r}"
    )

SAFE_SHELL_CASES = [
    "ls -la",
    "echo hello",
    "cat /tmp/output.txt",
    "grep -n pattern file.txt",
    "wc -l file.txt",
]

@pytest.mark.parametrize("cmd", SAFE_SHELL_CASES)
def test_safe_shell_passes(cmd):
    pytest.importorskip("bashlex")
    assert is_safe_shell(cmd), f"Safe command was flagged: {cmd!r}"
```

---

## Execution Order & Branching Strategy

Implement these items in the following order to minimise merge conflicts and
test failures:

```
1. ITEM 3  — _safe_call (no breaking changes, pure addition)
2. ITEM 1  — Rename jarvis → cognithor (breaking, do in one atomic PR)
3. ITEM 2  — README accuracy (no code changes, safe anytime)
4. ITEM 5  — AST security (additive, then delete old regex)
5. ITEM 4  — CI + scope (needs items 1–3 done first for clean green build)
```

Suggested branch names:
- `refactor/safe-call-observability`
- `refactor/complete-rename-jarvis-to-cognithor`
- `docs/readme-accuracy-pass`
- `security/ast-based-analysis`
- `ci/github-actions-v0.1.0`

---

## Definition of Done

- [ ] `grep -rn "jarvis" . --include="*.py"` returns zero results
- [ ] `grep -rn "JARVIS_" . --include="*.py"` returns zero results
- [ ] `grep -rn "~/.cognithor"` returns zero results
- [ ] All `except Exception: pass` patterns in optional subsystem inits converted to `_safe_call`
- [ ] `cognithor doctor --health` command exists and exits non-zero when subsystems failed
- [ ] `make health` target exists in Makefile
- [ ] README sandbox description matches actual code behaviour
- [ ] README default install / extras declaration matches `pyproject.toml`
- [ ] README clone URL is correct
- [ ] `_DANGEROUS_PYTHON_PATTERNS` regex list deleted
- [ ] Regex-based shell file-command check deleted
- [ ] `cognithor/security/python_ast_guard.py` exists with full NodeVisitor
- [ ] `cognithor/security/shell_ast_guard.py` exists using bashlex
- [ ] `tests/security/test_python_ast_guard.py` passes (incl. string-concat bypass test)
- [ ] `tests/security/test_shell_ast_guard.py` passes (incl. `${IFS}` bypass test)
- [ ] `.github/workflows/ci.yml` exists, green on current main
- [ ] Live CI badges in README (not static shields.io images)
- [ ] `Development Status :: 4 - Beta` in `pyproject.toml` (not `:: 5`)
- [ ] Full test suite (`pytest tests/ -x -q`) passes with zero failures

---

*Generated from Reddit code review by HoraceAndTheRest — Cognithor public thread.*
*Project scale: ~200K LOC production / ~100K LOC tests. Python 3.12+. v0.57.x → v1.0.0.*
