#!/usr/bin/env python3
"""
Filter ``DCAgent/exp_rle_minimal_instructions`` tasks to drop those whose
``tests/test_solution.py`` cannot run in the daytona sandbox image.

Background
----------
``exp_rle_minimal_instructions`` is the "minimal instructions" prompt-engineering
treatment of the same 5,000-task pool that backs ``exp_rle_heavy_padding`` and
the ``exp_flat25_*`` variants. QC of the 200 sampled traces shows the same
failure mode that motivated ``patch_rle_flat25_tasks.py``:

  * 200/200 trials reach the verifier (infra-OK 1.000).
  * Only 2/200 trials get reward=1, and BOTH are rubber-stamps: the test
    file pytest-collects only ``SKIPPED`` cases ("3 skipped, 1 warning" /
    "1 skipped"), which the verifier still classifies as "All tests passed".
  * The remaining 198 fail almost exclusively because
    ``tests/test_solution.py`` does ``import X`` for a package ``X`` that is
    neither in the container image, in the pip whitelist installed by
    ``tests/test.sh``, nor in the (very short) "minimal" instruction. The
    minimal instructions never name the import target, so the agent has
    no way to discover it from the prompt alone. Examples observed:
        - test imports ``openeo``, instruction says "RestApiConnection /
          Connection / load_collection" with no module name
        - test imports ``cmd2``, instruction says "package named smart"
        - test imports ``traveling_salesperson`` / ``celery`` / ``aiocron``
          / ``namedlist`` / ``soocii_pubsub_lib`` / ``illud`` / ``dagather``
          / ``core`` / ``tests`` — all unrelated to the instruction text.

The container's pip whitelist (from ``environment/test.sh``) is:

    requests numpy pandas scipy scikit-learn sklearn torch tensorflow keras
    httpx aiohttp ddtrace django flask fastapi matplotlib seaborn pillow
    pydantic pytest-mock requests-mock faker pyyaml pytz cryptography bcrypt
    hypothesis

Filter logic (identical to ``patch_rle_flat25_tasks.py``)
---------------------------------------------------------
For each task:
  1. ``py_compile`` ``tests/test_solution.py`` → drop on syntax error.
  2. AST-parse top-level imports. Drop the task if ANY top-level import is
     not in:
       - Python stdlib (``sys.stdlib_module_names``)
       - The container's pip whitelist (above)
       - A token mentioned literally in ``instruction.md``
  3. Otherwise keep the task untouched. The patcher never mutates tasks;
     it only drops them.

Usage
-----
    python data/patchers/patch_exp_rle_minimal_instructions_tasks.py --root /path/to/tasks_dir
    python data/patchers/patch_exp_rle_minimal_instructions_tasks.py --root /path/to/tasks_dir --dry-run
    python data/patchers/patch_exp_rle_minimal_instructions_tasks.py --root /path/to/tasks_dir --limit 200

Idempotency
-----------
A marker file ``.patched_exp_rle_minimal_instructions`` is written under
``--root`` after a successful (non-dry-run) pass. Re-running on the same
root short-circuits with a notice so we don't double-trim.
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
# Allowlist (mirrors patch_rle_flat25_tasks.py — same 5K pool + same image)
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

MARKER_NAME = ".patched_exp_rle_minimal_instructions"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _top_level_imports(tree: ast.AST) -> set[str]:
    """Top-level package names imported by an AST module.

    ``import a.b.c`` and ``from a.b import c`` → ``a``.
    Relative ``from . import x`` → ignored (local package only).
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def _instruction_tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text)}


def evaluate_task(task_dir: Path) -> dict:
    test_file = task_dir / "tests" / "test_solution.py"
    instruction_file = task_dir / "instruction.md"

    if not test_file.exists():
        return {"kept": False, "reason": "no_test_file", "bad_imports": []}

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

    return {"kept": True, "reason": "", "bad_imports": []}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--show-bad",
        type=int,
        default=20,
        help="Print the first N bad-import samples.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    marker = root / MARKER_NAME
    if marker.exists() and not args.dry_run:
        print(
            f"[patch_exp_rle_minimal_instructions] marker {marker} exists — "
            f"already patched, skipping (delete the marker to force re-run)."
        )
        return

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    print(
        f"[patch_exp_rle_minimal_instructions] inspecting {len(task_dirs)} "
        f"tasks under {root}"
    )

    syntax_dropped = 0
    no_test_dropped = 0
    import_dropped = 0
    kept = 0

    bad_import_samples: list[tuple[str, list[str]]] = []
    verdicts: dict[str, dict] = {}

    for td in task_dirs:
        v = evaluate_task(td)
        verdicts[td.name] = v
        if v["kept"]:
            kept += 1
            continue
        if v["reason"] == "no_test_file":
            no_test_dropped += 1
        elif (
            v["reason"].startswith("syntax_error")
            or v["reason"].startswith("ast_syntax")
            or v["reason"].startswith("compile_error")
        ):
            syntax_dropped += 1
        elif v["reason"] == "missing_import":
            import_dropped += 1
            if len(bad_import_samples) < args.show_bad:
                bad_import_samples.append((td.name, v["bad_imports"]))

    total = len(task_dirs)
    syntax_passed = total - syntax_dropped - no_test_dropped
    import_passed = syntax_passed - import_dropped

    print()
    print(f"[patch_exp_rle_minimal_instructions] total:          {total}")
    print(f"[patch_exp_rle_minimal_instructions] no test file:   {no_test_dropped}")
    print(f"[patch_exp_rle_minimal_instructions] syntax errors:  {syntax_dropped}")
    print(f"[patch_exp_rle_minimal_instructions] syntax passed:  {syntax_passed}")
    print(f"[patch_exp_rle_minimal_instructions] import dropped: {import_dropped}")
    print(f"[patch_exp_rle_minimal_instructions] import passed:  {import_passed}")
    print(f"[patch_exp_rle_minimal_instructions] kept:           {kept}")

    if bad_import_samples:
        print()
        print(
            f"[patch_exp_rle_minimal_instructions] sample bad-import drops "
            f"(first {len(bad_import_samples)}):"
        )
        for tid, bad in bad_import_samples:
            print(f"  {tid}: {bad}")

    if args.report_json:
        args.report_json.write_text(json.dumps(verdicts, indent=2))
        print(
            f"[patch_exp_rle_minimal_instructions] wrote per-task verdicts: "
            f"{args.report_json}"
        )

    if args.dry_run:
        print(
            "[patch_exp_rle_minimal_instructions] dry-run: not deleting dropped tasks."
        )
        return

    removed = 0
    for tid, v in verdicts.items():
        if v["kept"]:
            continue
        target = root / tid
        if target.exists():
            shutil.rmtree(target)
            removed += 1
    print(
        f"[patch_exp_rle_minimal_instructions] removed {removed} dropped task directories."
    )

    marker.write_text("patched\n")
    print(f"[patch_exp_rle_minimal_instructions] wrote idempotency marker {marker}")


if __name__ == "__main__":
    main()
