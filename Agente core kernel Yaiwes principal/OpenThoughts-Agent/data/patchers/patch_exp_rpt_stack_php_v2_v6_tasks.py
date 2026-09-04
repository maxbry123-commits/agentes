#!/usr/bin/env python3
"""
exp_rpt_stack-php-v2 → v6 patcher.

Background
==========
The v5 patcher (``patch_exp_rpt_stack_php_v2_v5_tasks.py``) tried to fix
PHPUnit-load failures by leaving the upstream ``tests/TestSolution.php``
untouched and using a bootstrap-side ``class_alias`` to satisfy PHPUnit
10's strict file-basename rule. v5 still produced **0/200** solve rate
across all four checkpoints. Post-mortem from QC on
``laion/exp_rpt_stack-php-v2-v5``:

* **Mode (a) ~94/200**:
  ``Class testsolution declared in /tests/TestSolution.php does not
  extend PHPUnit\\Framework\\TestCase`` — the bootstrap's class_alias
  produced an alias whose target failed PHPUnit's strict-inheritance
  check (often because the file declared multiple classes and the
  alias picked a stub).
* **Mode (b) ~70/200**:
  ``Declaration of X::setUp() must be compatible with PHPUnit\\Framework\\
  TestCase::setUp(): void`` — PHPUnit 10's parent declares
  ``protected function setUp(): void`` and the scraped upstream code
  used the pre-PHPUnit-10 signature.
* **Mode (c) ~36/200**:
  ``Class TestSolution cannot be found in /tests/TestSolution.php`` —
  the bootstrap-side alias never ran (e.g. an earlier fatal in
  ``require_once`` killed the include).

All three failure modes share a common root cause: we tried to keep
``tests/TestSolution.php`` verbatim. v6 abandons that constraint and
**directly rewrites** the file into a single canonical shape:

::

    <?php
    <use lines preserved>
    class TestSolution extends \\PHPUnit\\Framework\\TestCase
    {
        <test methods, with setUp/tearDown signatures fixed>
    }

The bootstrap shim from v5 is preserved (legacy ``PHPUnit_Framework_TestCase``
alias, ``Tests\\TestCase`` stub, project autoload chains) because the
test bodies still reference upstream framework types via ``use`` lines.

Algorithm
=========
For each task:

1. Read ``tests/TestSolution.php`` (skip if missing).
2. Lex the file: extract the namespace, the ``use`` imports, the FIRST
   class declaration extending some flavor of ``TestCase`` (or
   ``PHPUnit_Framework_TestCase``, ``Tests\\TestCase``, etc.), and the
   class body.
3. If no test-class candidate is found, mark the task as DROPPED.
4. Rewrite signatures inside the class body:
   * ``public function setUp()`` / ``protected function setUp()``
     / ``function setUp()`` (no return type) → ``protected function setUp(): void``
   * Same for ``tearDown``, ``setUpBeforeClass``, ``tearDownBeforeClass``
     (the *BeforeClass variants become ``public static`` with ``: void``).
   * Lowercase ``setup()``/``teardown()`` → ``setUp()``/``tearDown()``.
5. Emit the rewritten file:
   * No ``namespace`` declaration (drop it).
   * Preserve the original ``use`` lines verbatim.
   * Single class ``TestSolution`` extending ``\\PHPUnit\\Framework\\TestCase``.
6. Validate the rewritten file with ``php -l`` inside a
   ``php:8.2-cli`` Docker container. Drop the task if PHP linting fails.
7. Also overwrite ``tests/test.sh`` with the v5 test.sh template
   (dataset_tag = ``stack-php-v2-v6``). The bootstrap shim's
   ``class_alias`` walk now becomes a no-op (the class is already named
   ``TestSolution``) but the legacy-base-class shims and autoload chain
   are still useful for the test method bodies.

Counters reported at end:
  - ``patched``: TestSolution.php rewritten + lint-passed + test.sh updated.
  - ``dropped_no_class``: lexer couldn't find a test-class declaration.
  - ``dropped_lint_fail``: rewritten file failed ``php -l``.
  - ``missing``: tests/TestSolution.php not present.
  - ``already``: marker present, no work needed.

Validation gate target: ≥150 of 200 tasks survive.

Usage::

  python data/patchers/patch_exp_rpt_stack_php_v2_v6_tasks.py \\
      --root <dir> [--dry-run] [--limit N] [--no-lint]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Allow this script to run as a script (no package context).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _stack_php_common import new_test_sh, patch_marker  # noqa: E402

DATASET_TAG = "stack-php-v2-v6"

PATCH_MARKER = patch_marker(DATASET_TAG)

# Marker we embed at the top of tests/TestSolution.php so we can detect
# already-patched files cheaply.
TS_PATCH_MARKER = "// --- laion stack-php-v2-v6 patch: rewritten TestSolution class ---"

NEW_TEST_SH = new_test_sh(DATASET_TAG)

# ---------------------------------------------------------------------------
# Lexer / rewriter for TestSolution.php
# ---------------------------------------------------------------------------

# Match a class declaration whose ``extends`` clause looks PHPUnit-ish.
# We match BOTH bare and namespaced variants:
#   class FooTest extends TestCase
#   class FooTest extends \PHPUnit\Framework\TestCase
#   class FooTest extends PHPUnit_Framework_TestCase
#   class FooTest extends \Tests\TestCase
#   class FooTest extends Tests\TestCase
#   class FooTest extends CakeTestCase
# Anything with "TestCase" in the parent name (case-insensitive) is treated
# as a candidate; this is intentionally permissive to capture the long tail
# of framework-specific bases.
_CLASS_RE = re.compile(
    r"""
    (?P<prefix>(?:abstract\s+|final\s+)*)
    class\s+
    (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    \s+extends\s+
    (?P<parent>\\?[A-Za-z_][A-Za-z0-9_\\]*)
    (?:\s+implements\s+[^{]+)?
    \s*\{
    """,
    re.VERBOSE,
)

_NAMESPACE_RE = re.compile(
    r"^\s*namespace\s+[A-Za-z_][A-Za-z0-9_\\]*\s*;\s*$", re.MULTILINE
)

_USE_RE = re.compile(
    r"^\s*use\s+(?:function\s+|const\s+)?[A-Za-z_][A-Za-z0-9_\\,\s{}]*;\s*$",
    re.MULTILINE,
)

# Signatures we rewrite (with or without explicit visibility / return type).
# Order matters: longer names first so ``setUpBeforeClass`` isn't matched
# by the ``setUp`` rule.
_SIG_REWRITES: list[tuple[re.Pattern[str], str]] = [
    # setUpBeforeClass / tearDownBeforeClass (public static, : void).
    (
        re.compile(
            r"(?:public\s+|protected\s+|private\s+)?(?:static\s+)?function\s+setUpBeforeClass\s*\([^)]*\)(?:\s*:\s*void)?",
            re.IGNORECASE,
        ),
        "public static function setUpBeforeClass(): void",
    ),
    (
        re.compile(
            r"(?:public\s+|protected\s+|private\s+)?(?:static\s+)?function\s+tearDownBeforeClass\s*\([^)]*\)(?:\s*:\s*void)?",
            re.IGNORECASE,
        ),
        "public static function tearDownBeforeClass(): void",
    ),
    # setUp / tearDown (protected, : void). Also rewrites lowercase ``setup``.
    (
        re.compile(
            r"(?:public\s+|protected\s+|private\s+)?function\s+setUp\s*\([^)]*\)(?:\s*:\s*void)?",
            re.IGNORECASE,
        ),
        "protected function setUp(): void",
    ),
    (
        re.compile(
            r"(?:public\s+|protected\s+|private\s+)?function\s+tearDown\s*\([^)]*\)(?:\s*:\s*void)?",
            re.IGNORECASE,
        ),
        "protected function tearDown(): void",
    ),
]


def _strip_php_open(src: str) -> str:
    """Strip an opening ``<?php`` tag (with optional declare(strict_types=1)
    on the same line) so we can re-emit a clean header."""
    src = src.lstrip("﻿")  # BOM
    # Match e.g. "<?php" or "<?php declare(strict_types=1);" or "<?php\n..."
    m = re.match(r"\s*<\?php(?:\s*declare\s*\([^)]*\)\s*;)?\s*", src)
    if m:
        return src[m.end() :]
    return src


def _match_brace(src: str, start: int) -> int:
    """Given index ``start`` pointing at ``{``, return the index of the
    matching ``}`` (inclusive). Skips strings, single/double quoted, and
    line + block comments. Returns -1 if no match.

    This is a deliberately simple matcher — PHP heredocs/nowdocs are NOT
    handled, but the scraped test files in this dataset don't use them
    inside class bodies in practice.
    """
    assert src[start] == "{", f"expected '{{' at {start}, got {src[start]!r}"
    depth = 0
    i = start
    n = len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            # // line comment
            nl = src.find("\n", i)
            if nl < 0:
                return -1
            i = nl + 1
            continue
        if c == "#":
            nl = src.find("\n", i)
            if nl < 0:
                return -1
            i = nl + 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            end = src.find("*/", i + 2)
            if end < 0:
                return -1
            i = end + 2
            continue
        if c == "'":
            # single-quoted string
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "'":
                    break
                j += 1
            i = j + 1
            continue
        if c == '"':
            # double-quoted string
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == '"':
                    break
                j += 1
            i = j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _rewrite_signatures(body: str) -> str:
    for pat, repl in _SIG_REWRITES:
        body = pat.sub(repl, body)
    return body


def _extract_uses(src: str) -> list[str]:
    """Return ``use ...;`` lines (verbatim, in source order). Skips the
    standard PHPUnit\\Framework\\TestCase import (we hard-code that)."""
    out = []
    for m in _USE_RE.finditer(src):
        line = m.group(0).strip()
        if "PHPUnit\\Framework\\TestCase" in line and "as " not in line.lower():
            # Already covered by our explicit FQN in ``extends``.
            continue
        out.append(line)
    return out


def rewrite_test_solution(src: str) -> tuple[str | None, str]:
    """Rewrite a TestSolution.php source.

    Returns ``(new_src, status)``. ``new_src`` is ``None`` on failure.
    """
    if TS_PATCH_MARKER in src:
        return None, "already"

    # 1. Strip <?php opener.
    after_open = _strip_php_open(src)

    # 2. Find a test-class declaration. We look for ANY class that
    #    extends something containing "TestCase" (case-insensitive),
    #    OR extends ``PHPUnit_Framework_TestCase``.
    candidate: re.Match[str] | None = None
    for m in _CLASS_RE.finditer(after_open):
        parent = m.group("parent")
        parent_lc = parent.lower()
        if "testcase" in parent_lc or "phpunit_framework_testcase" in parent_lc:
            candidate = m
            break

    if candidate is None:
        return None, "no_class"

    body_start = candidate.end() - 1  # index of '{'
    body_end = _match_brace(after_open, body_start)
    if body_end < 0:
        return None, "unbalanced_braces"

    inner = after_open[body_start + 1 : body_end]
    inner = _rewrite_signatures(inner)

    # 3. Extract use lines.
    uses = _extract_uses(after_open)

    # 4. Sanity check: at least one ``function test`` method or ``@test``
    #    annotation. If none, the verifier will report tests_run=0 even
    #    after we patch.
    if (
        not re.search(r"function\s+test[A-Za-z0-9_]*\s*\(", inner, re.IGNORECASE)
        and "@test" not in inner.lower()
    ):
        return None, "no_test_methods"

    # 5. Emit rewritten file.
    header = "<?php declare(strict_types=1);\n\n"
    header += TS_PATCH_MARKER + "\n"
    header += (
        "// Original class signature rewritten by v6 patcher; namespace dropped.\n\n"
    )
    if uses:
        header += "\n".join(uses) + "\n\n"
    new_src = (
        header
        + "class TestSolution extends \\PHPUnit\\Framework\\TestCase\n{"
        + inner
        + "}\n"
    )
    return new_src, "patched"


# ---------------------------------------------------------------------------
# Validation (docker php -l)
# ---------------------------------------------------------------------------

DOCKER_IMAGE = "php:8.2-cli"


def docker_php_lint(file_path: Path) -> tuple[bool, str]:
    """Run ``php -l`` on a file inside the official php:8.2-cli image.

    Returns ``(ok, message)``.
    """
    try:
        proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{file_path.parent.resolve()}:/work",
                DOCKER_IMAGE,
                "php",
                "-l",
                f"/work/{file_path.name}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, "docker_timeout"
    except FileNotFoundError:
        return False, "docker_missing"
    out = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0 and "No syntax errors" in out
    return ok, out.strip().splitlines()[0] if out else ""


# ---------------------------------------------------------------------------
# Per-task driver
# ---------------------------------------------------------------------------


def patch_task(task_dir: Path, *, dry_run: bool, do_lint: bool) -> str:
    """Patch one task. Returns a status string used as a counter key."""
    test_sh = task_dir / "tests" / "test.sh"
    test_php = task_dir / "tests" / "TestSolution.php"

    if not test_php.is_file() or not test_sh.is_file():
        return "missing"

    try:
        php_src = test_php.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"

    if TS_PATCH_MARKER in php_src and PATCH_MARKER in test_sh.read_text(
        encoding="utf-8", errors="replace"
    ):
        return "already"

    new_php, status = rewrite_test_solution(php_src)
    if new_php is None:
        if status == "no_class":
            return "dropped_no_class"
        if status == "no_test_methods":
            return "dropped_no_test_methods"
        if status == "unbalanced_braces":
            return "dropped_unbalanced_braces"
        return f"dropped_{status}"

    if not dry_run:
        test_php.write_text(new_php, encoding="utf-8")

    if do_lint:
        # Lint the *written* file (or a tempfile in dry-run mode).
        if dry_run:
            tmp = task_dir / "tests" / ".TestSolution.lintcheck.php"
            tmp.write_text(new_php, encoding="utf-8")
            try:
                ok, msg = docker_php_lint(tmp)
            finally:
                tmp.unlink(missing_ok=True)
        else:
            ok, msg = docker_php_lint(test_php)
        if not ok:
            # Roll back on lint failure to keep the dataset state clean.
            if not dry_run:
                test_php.write_text(php_src, encoding="utf-8")
            return "dropped_lint_fail"

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")

    return "patched"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Path to extracted tasks root")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip docker-based php -l validation (faster, less safe).",
    )
    p.add_argument(
        "--drop-failed",
        action="store_true",
        help="rm -rf any task directory whose status is in {dropped_*, missing}. "
        "Required for a final upload — verifier would emit reward=0 forever on "
        "these.",
    )
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts: dict[str, int] = {}
    drop_list: list[Path] = []

    for i, td in enumerate(task_dirs, 1):
        try:
            result = patch_task(td, dry_run=args.dry_run, do_lint=not args.no_lint)
        except Exception as e:  # noqa: BLE001
            result = "error"
            print(f"  [error] {td.name}: {e}", file=sys.stderr)
        counts[result] = counts.get(result, 0) + 1
        if result.startswith("dropped") or result == "missing":
            drop_list.append(td)

        if i % 25 == 0 or i == n_total:
            line = f"[{i}/{n_total}] " + " ".join(
                f"{k}={v}" for k, v in sorted(counts.items())
            )
            print(line, flush=True)

    print()
    print(
        f"=== v6 patcher summary (dry_run={args.dry_run}, lint={not args.no_lint}) ==="
    )
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    print(f"  total: {n_total}")

    if args.drop_failed and not args.dry_run and drop_list:
        print(f"\nDropping {len(drop_list)} failed task directories...")
        for d in drop_list:
            shutil.rmtree(d, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
