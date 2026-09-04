#!/usr/bin/env python3
"""
Filter DCAgent/exp_rle_expert tasks (one of the 5k-task-pool RLE variants)
to drop tasks whose ``tests/test_solution.py`` cannot produce a useful
reward signal in the daytona sandbox image.

Background
----------
QC on DCAgent/exp_rle_expert (200/200 infra-OK, 2/200 solved) found two
distinct verifier-leniency / setup-failure modes hiding behind the
``infra-ok`` flag:

1. **Missing-import failures (163/200 = 82%)** — ``test_solution.py`` does
   ``import <third_party>`` where the package is neither in the container
   image (``python3 + pytest`` + ``tests/test.sh`` whitelist) nor the
   package the agent is supposed to implement (i.e. the test description
   names a totally different module from what the test imports). The agent
   has no way to make the test runnable, so pytest fails at collection
   with ``ModuleNotFoundError`` for ALL trials. These tasks are dead
   weight in an RL dataset.

   This filter is identical in spirit to ``patch_rle_flat25_tasks.py`` and
   re-uses its WHITELIST / ALWAYS_INSTALLED / STDLIB constants.

2. **All-skipped-→-pass rubber stamps (2/200 = 1%)** — every test in
   ``test_solution.py`` is decorated with ``@pytest.mark.skip(...)`` /
   ``@pytest.mark.skipif(...)``, or the module-level ``pytestmark`` is
   ``skip``/``skipif``. Pytest then collects N tests, skips all N, and
   exits 0 → ``test.sh`` prints ``"All tests passed!"`` → reward = 1.
   Both QC-solved trials match this pattern (e.g.
   ``5k-expert-0792``: ``@pytest.mark.skip(reason="New hire will work on this")``
   on every method, and ``5k-expert-1876``: module-level
   ``pytestmark = pytest.mark.skipif('raft' not in sys.argv, ...)``).
   These tasks produce a 100% positive reward regardless of agent action
   and corrupt the training signal.

Filter logic
------------
For each task:
  1. ``py_compile`` ``tests/test_solution.py`` → drop on syntax error.
  2. AST parse top-level imports. Drop if ANY top-level import is not in
     stdlib + container whitelist + instruction.md token set.
  3. AST inspect for unconditionally-skipped tests:
     - module-level ``pytestmark`` assigned to ``pytest.mark.skip`` /
       ``pytest.mark.skipif`` / a list thereof → drop.
     - EVERY top-level / class-level ``test_*`` function has at least one
       ``@pytest.mark.skip`` or ``@pytest.mark.skipif`` decorator → drop.
     (If at least one test is unconditionally runnable, the task can still
     produce a meaningful 0/1 reward, so we keep it.)
  4. Otherwise keep the task untouched.

The patcher NEVER mutates a task directory; it only deletes dropped
tasks (or reports them in dry-run mode).

Idempotency
-----------
A marker file ``.exp_rle_expert_patched`` is written to ``--root`` on
successful completion. If the marker is present on a subsequent run, the
script exits with a no-op (unless ``--force`` is passed).

Usage
-----
    python data/patchers/patch_exp_rle_expert_tasks.py --root /path/to/tasks_dir
    python data/patchers/patch_exp_rle_expert_tasks.py --root /path/to/tasks_dir --dry-run
    python data/patchers/patch_exp_rle_expert_tasks.py --root /path/to/tasks_dir --limit 200
"""

from __future__ import annotations

import argparse
import ast
import json
import py_compile
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Allowlist (mirrors patch_rle_flat25_tasks.py — keep in sync)
# ---------------------------------------------------------------------------

STDLIB: frozenset[str] = frozenset(getattr(sys, "stdlib_module_names", set()))

ALWAYS_INSTALLED: frozenset[str] = frozenset(
    {
        "pytest",
        "_pytest",
        "py",
        "pluggy",
        "iniconfig",
        "packaging",
        "tomli",
        "exceptiongroup",
    }
)

WHITELIST_PIP_TO_IMPORTS: dict[str, tuple[str, ...]] = {
    "requests": ("requests",),
    "numpy": ("numpy",),
    "pandas": ("pandas",),
    "scipy": ("scipy",),
    "scikit-learn": ("sklearn",),
    "sklearn": ("sklearn",),
    "torch": ("torch",),
    "tensorflow": ("tensorflow", "tf"),
    "keras": ("keras",),
    "httpx": ("httpx",),
    "aiohttp": ("aiohttp",),
    "ddtrace": ("ddtrace",),
    "django": ("django",),
    "flask": ("flask",),
    "fastapi": ("fastapi",),
    "matplotlib": ("matplotlib",),
    "seaborn": ("seaborn",),
    "pillow": ("PIL",),
    "pydantic": ("pydantic",),
    "pytest-mock": ("pytest_mock",),
    "requests-mock": ("requests_mock",),
    "faker": ("faker",),
    "pyyaml": ("yaml",),
    "pytz": ("pytz",),
    "cryptography": ("cryptography",),
    "bcrypt": ("bcrypt",),
    "hypothesis": ("hypothesis",),
}

PIP_WHITELIST: frozenset[str] = frozenset(
    name for imports in WHITELIST_PIP_TO_IMPORTS.values() for name in imports
)

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")

MARKER_FILENAME = ".exp_rle_expert_patched"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _top_level_imports(tree: ast.AST) -> set[str]:
    """Return the set of top-level package names imported by an AST module."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative — local package only
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def _instruction_tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text)}


def _is_skip_marker(node: ast.AST) -> bool:
    """True if ``node`` looks like ``pytest.mark.skip(...)`` /
    ``pytest.mark.skipif(...)`` (with or without a call).

    Accepts:
      - ``pytest.mark.skip``
      - ``pytest.mark.skip(...)``
      - ``pytest.mark.skipif(...)``
      - bare ``Name('skip')``-style attributes when re-imported (rare; we
        don't try to follow aliases — over-counting here would only over-
        drop a tiny number of tasks).
    """
    target = node.func if isinstance(node, ast.Call) else node
    # We want a dotted chain ending in ``skip`` or ``skipif``.
    if isinstance(target, ast.Attribute):
        if target.attr in ("skip", "skipif"):
            # Walk down to ensure the chain mentions ``mark``.
            cur: ast.AST = target.value
            while isinstance(cur, ast.Attribute):
                if cur.attr == "mark":
                    return True
                cur = cur.value
            # Fallback: ``mark`` not in chain (e.g. ``pytest.skip``) — also
            # treat as skip-equivalent. ``pytest.skip(...)`` at module/test
            # body level would not be a decorator, but ``mark.skip`` is the
            # standard form anyway.
            return True
    return False


def _decorator_skips(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if any decorator on ``func`` is a pytest skip/skipif marker."""
    for dec in func.decorator_list:
        if _is_skip_marker(dec):
            return True
    return False


def _pytestmark_value_is_all_skip(value: ast.AST) -> bool:
    """Inspect the RHS of a ``pytestmark = ...`` assignment and decide if
    every mark in it is a skip/skipif marker (and therefore the whole
    module is unconditionally skipped).

    Accepts a single marker or a list/tuple of markers. A single non-skip
    marker in a list is enough to NOT trigger the all-skip drop (we are
    intentionally conservative — false-negatives are fine, false-positives
    would drop legitimate tasks).
    """
    if isinstance(value, (ast.List, ast.Tuple)):
        if not value.elts:
            return False
        return all(_is_skip_marker(el) for el in value.elts)
    return _is_skip_marker(value)


def _module_level_pytestmark_skip(tree: ast.Module) -> bool:
    """True if the module has a top-level assignment
    ``pytestmark = pytest.mark.skip[if](...)`` or a list of skip markers.
    """
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [
                t
                for t in node.targets
                if isinstance(t, ast.Name) and t.id == "pytestmark"
            ]
            if targets and _pytestmark_value_is_all_skip(node.value):
                return True
        elif isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == "pytestmark"
                and node.value is not None
                and _pytestmark_value_is_all_skip(node.value)
            ):
                return True
    return False


def _iter_test_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Collect top-level ``test_*`` functions and methods of top-level
    classes whose name starts with ``Test`` (pytest's default discovery).
    """
    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test_"):
            out.append(node)
        elif isinstance(node, ast.ClassDef) and (
            node.name.startswith("Test") or node.name.startswith("test_")
        ):
            for sub in node.body:
                if isinstance(
                    sub, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and sub.name.startswith("test_"):
                    out.append(sub)
    return out


def _all_tests_skipped(tree: ast.Module) -> bool:
    tests = _iter_test_functions(tree)
    if not tests:
        return False  # no tests at all → handled by import filter / pytest collects 0
    return all(_decorator_skips(t) for t in tests)


# ---------------------------------------------------------------------------
# Per-task evaluation
# ---------------------------------------------------------------------------


def evaluate_task(task_dir: Path) -> dict:
    """Return a per-task verdict dict.

    Keys:
      kept: bool
      reason: str
      bad_imports: list[str]
    """
    test_file = task_dir / "tests" / "test_solution.py"
    instruction_file = task_dir / "instruction.md"

    if not test_file.exists():
        return {"kept": False, "reason": "no_test_file", "bad_imports": []}

    # 1. py_compile
    try:
        with tempfile.NamedTemporaryFile(suffix=".pyc", delete=True) as tmp:
            py_compile.compile(str(test_file), cfile=tmp.name, doraise=True)
    except py_compile.PyCompileError as exc:
        return {
            "kept": False,
            "reason": f"syntax_error: {exc.msg.splitlines()[0][:80]}",
            "bad_imports": [],
        }
    except Exception as exc:
        return {
            "kept": False,
            "reason": f"compile_error: {type(exc).__name__}",
            "bad_imports": [],
        }

    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return {
            "kept": False,
            "reason": f"ast_syntax: {exc.msg[:60]}",
            "bad_imports": [],
        }

    # 2. Import filter
    imports = _top_level_imports(tree)
    instr_tokens: set[str] = set()
    if instruction_file.exists():
        instr_tokens = _instruction_tokens(
            instruction_file.read_text(encoding="utf-8", errors="replace")
        )

    bad: list[str] = []
    for name in sorted(imports):
        if name in STDLIB:
            continue
        if name in ALWAYS_INSTALLED:
            continue
        if name in PIP_WHITELIST:
            continue
        if name.lower() in instr_tokens:
            continue
        bad.append(name)

    if bad:
        return {"kept": False, "reason": "missing_import", "bad_imports": bad}

    # 3. All-skip rubber-stamp filter
    if _module_level_pytestmark_skip(tree):
        return {"kept": False, "reason": "module_pytestmark_skip", "bad_imports": []}
    if _all_tests_skipped(tree):
        return {"kept": False, "reason": "all_tests_skipped", "bad_imports": []}

    return {"kept": True, "reason": "", "bad_imports": []}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Directory containing extracted task folders.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report counts; do not delete dropped task folders.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only inspect the first N tasks (debug).",
    )
    p.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Write per-task verdict JSON to this file.",
    )
    p.add_argument(
        "--show-bad", type=int, default=20, help="Print the first N bad-import samples."
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if the idempotency marker is present.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    marker = root / MARKER_FILENAME
    if marker.exists() and not args.force and not args.dry_run:
        print(
            f"[patch_exp_rle_expert] marker present at {marker}; skipping (use --force to re-run)."
        )
        return

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    print(f"[patch_exp_rle_expert] inspecting {len(task_dirs)} tasks under {root}")

    syntax_dropped = 0
    no_test_dropped = 0
    import_dropped = 0
    module_skip_dropped = 0
    all_tests_skip_dropped = 0
    kept = 0

    bad_import_samples: list[tuple[str, list[str]]] = []
    verdicts: dict[str, dict] = {}

    for td in task_dirs:
        v = evaluate_task(td)
        verdicts[td.name] = v
        if v["kept"]:
            kept += 1
            continue
        r = v["reason"]
        if r == "no_test_file":
            no_test_dropped += 1
        elif (
            r.startswith("syntax_error")
            or r.startswith("ast_syntax")
            or r.startswith("compile_error")
        ):
            syntax_dropped += 1
        elif r == "missing_import":
            import_dropped += 1
            if len(bad_import_samples) < args.show_bad:
                bad_import_samples.append((td.name, v["bad_imports"]))
        elif r == "module_pytestmark_skip":
            module_skip_dropped += 1
        elif r == "all_tests_skipped":
            all_tests_skip_dropped += 1

    total = len(task_dirs)
    after_syntax = total - syntax_dropped - no_test_dropped
    after_imports = after_syntax - import_dropped
    after_skip = after_imports - module_skip_dropped - all_tests_skip_dropped

    print()
    print(f"[patch_exp_rle_expert] total:                {total}")
    print(f"[patch_exp_rle_expert] no test file:         {no_test_dropped}")
    print(f"[patch_exp_rle_expert] syntax errors:        {syntax_dropped}")
    print(f"[patch_exp_rle_expert] after syntax:         {after_syntax}")
    print(f"[patch_exp_rle_expert] missing imports:      {import_dropped}")
    print(f"[patch_exp_rle_expert] after imports:        {after_imports}")
    print(f"[patch_exp_rle_expert] module pytestmark=skip: {module_skip_dropped}")
    print(f"[patch_exp_rle_expert] every test @skip:     {all_tests_skip_dropped}")
    print(f"[patch_exp_rle_expert] after skip filter:    {after_skip}")
    print(f"[patch_exp_rle_expert] kept:                 {kept}")

    if bad_import_samples:
        print()
        print(
            f"[patch_exp_rle_expert] sample bad-import drops (first {len(bad_import_samples)}):"
        )
        for tid, bad in bad_import_samples:
            print(f"  {tid}: {bad}")

    if args.report_json:
        args.report_json.write_text(json.dumps(verdicts, indent=2))
        print(f"[patch_exp_rle_expert] wrote per-task verdicts: {args.report_json}")

    if args.dry_run:
        print("[patch_exp_rle_expert] dry-run: not deleting dropped tasks.")
        return

    # Apply: remove dropped task directories.
    removed = 0
    for tid, v in verdicts.items():
        if v["kept"]:
            continue
        target = root / tid
        if target.exists():
            shutil.rmtree(target)
            removed += 1
    print(f"[patch_exp_rle_expert] removed {removed} dropped task directories.")

    # Write idempotency marker.
    marker.write_text(f"total={total}\nkept={kept}\nremoved={removed}\n")
    print(f"[patch_exp_rle_expert] wrote idempotency marker: {marker}")


if __name__ == "__main__":
    main()
