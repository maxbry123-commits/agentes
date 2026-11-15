#!/usr/bin/env python3
"""
exp_rpt_stack-pytest-gpt5mini patcher (v2 -> v3).

QC of v2 (``laion/exp_rpt_stack-pytest-gpt5mini-v2``, n=200): 100%
infra-ok, 13.0% solve rate. Three problems surfaced in the failing
traces:

1. **src/tests/app misuse (50% of ModuleNotFoundError failures).**
   v2 had ``src``, ``tests``, ``app`` in ``ALWAYS_INSTALLED``, so tasks
   whose ``test_solution.py`` did ``from src.X import Y`` or
   ``from tests.X import Y`` passed the import-allowlist filter. But:

   - For ``src.X`` (34 tasks in this corpus): 100% have an instruction/
     test path mismatch. ``instruction.md`` tells the agent to write
     ``/app/<some_other_package>/<file>.py``, while ``test_solution.py``
     imports ``from src.metrics.<x> import Y``. The agent has
     ``max_episodes=1`` and never sees the test — it follows the
     instruction, places the solution at the instructed path, and the
     test fails at collection. Unsolvable.
   - For ``tests.X`` (50 tasks): 84% have the same mismatch.
     ``test_solution.py`` does ``from tests.common import something_helper``
     — these helper modules live in the source repo's test directory and
     were pruned during dataset extraction. No agent can create them
     because instruction.md doesn't describe them.
   - For ``app.X`` (rare): same shape.

   v3 drops ALL tasks whose ``test_solution.py`` does a top-level
   ``import src.*`` / ``import tests.*`` / ``import app.*`` /
   ``from src... import ...`` / ``from tests... import ...`` /
   ``from app... import ...``.

2. **Niche/private modules kept via instruction_tokens fuzzy-match
   (~30% of ModuleNotFoundError failures).** v2's ``imports_pass`` had
   a heuristic that rescued any import whose module name appeared as a
   token anywhere in ``instruction.md``. This was meant to handle cases
   like "place your solution under ``/app/foo`` so tests can do
   ``from foo import X``", but in practice it kept tasks where
   ``instruction.md`` mentions e.g. ``continuum`` (the AGENT's target
   package, named in the spec) but the test ALSO imports
   ``from continuum.datasets import CIFAR10`` — needing the upstream
   PyPI ``continuum`` package that doesn't exist under that name.
   183/554 tasks (33%) were kept solely via this loophole.

   v3 removes the instruction_tokens rescue path. An import is allowed
   only if it's stdlib, in ``ALWAYS_INSTALLED`` (just ``solution`` now),
   or in the expanded WHITELIST.

3. **All-skip rubber-stamp passes (3/26 successes in QC).** Three of
   v2's 26 "solved" tasks were 100%-skipped: pytest collected the test
   file, every test had ``@pytest.mark.skip`` / used
   ``pytest.importorskip`` on a missing module at module level →
   pytest exits 0 → reward = 1. No code was actually tested.

   v3 drops tasks where ALL ``test_*`` functions are decorated with
   ``@*skip*``, AND tasks with a module-level ``pytest.importorskip``
   on a non-whitelisted module.

4. **Expand pip whitelist with legitimate PyPI modules from v2 failures
   that weren't in v2's WHITELIST_PIP_TO_IMPORTS.** Added (modest-size
   only — skipping torch/airflow/mindspore/pennylane because they have
   slow/heavy install paths that often time out in 2 CPU / 4GB
   containers): ``psutil``, ``alembic``, ``bokeh``, ``Faker``,
   ``scrapy``, ``tzdata``, ``praw``, ``geoalchemy2``, ``matplotlib``,
   ``tqdm``, ``redis``, ``toml``, ``attrs``, ``rich``.

Simulated yield on the source v2 dataset (n=554):
- v3 KEEP: 326 (58.8%)
- drop_src_tests_app: 100 (18.1%)
- drop_import: 125 (22.6%) — niche/private modules from #2
- drop_all_skip / drop_importorskip: 3 (0.6%)

CLI mirrors the v2 patcher::

    python data/patchers/patch_exp_rpt_stack_pytest_gpt5mini_v3_tasks.py \\
        --root /path/to/extracted_tasks_dir \\
        [--dry-run] [--limit N] [--drop-log path.tsv]

Apply on TOP of the v2 dataset (after re-extracting v2's tasks.parquet).
Target HF repo: ``laion/exp_rpt_stack-pytest-gpt5mini-v3``.
"""

from __future__ import annotations

import argparse
import ast
import py_compile
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# v3 allowlist (expanded from v4 / v2 — see module docstring point 4).
# ---------------------------------------------------------------------------

STDLIB: frozenset[str] = frozenset(getattr(sys, "stdlib_module_names", set()))

# v3 difference from v4/v2: ``src``, ``tests``, ``app`` are REMOVED. Tasks
# whose test_solution.py imports from these top-level names are dropped
# by the dedicated ``src_tests_app_pass`` filter — see #1 in the module
# docstring.
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
        # Conventional agent-provided entrypoint module: tests in this corpus
        # commonly do ``from solution import X`` to import what the agent
        # produced at ``/app/solution.py``.
        "solution",
    }
)


WHITELIST_PIP_TO_IMPORTS: dict[str, tuple[str, ...]] = {
    # v4 carry-over
    "requests": ("requests",),
    "numpy": ("numpy",),
    "pandas": ("pandas",),
    "scipy": ("scipy",),
    "scikit-learn": ("sklearn",),
    "httpx": ("httpx",),
    "aiohttp": ("aiohttp",),
    "django": ("django",),
    "flask": ("flask",),
    "fastapi": ("fastapi",),
    "pydantic": ("pydantic",),
    "pyyaml": ("yaml",),
    "pytz": ("pytz",),
    "cryptography": ("cryptography",),
    "pillow": ("PIL",),
    "hypothesis": ("hypothesis",),
    "click": ("click",),
    "jinja2": ("jinja2",),
    "lxml": ("lxml",),
    "beautifulsoup4": ("bs4",),
    "mock": ("mock",),
    "sympy": ("sympy",),
    "networkx": ("networkx",),
    "werkzeug": ("werkzeug",),
    "traitlets": ("traitlets",),
    "xarray": ("xarray",),
    "ecdsa": ("ecdsa",),
    "sqlalchemy": ("sqlalchemy",),
    # NEW in v3 — modest-size PyPI packages from gpt5mini-v2 failure traces.
    # Excluded: torch, apache-airflow, mindspore, pennylane (heavy ML deps
    # that often time out in 2-CPU / 4GB containers).
    "psutil": ("psutil",),
    "alembic": ("alembic",),
    "bokeh": ("bokeh",),
    "Faker": ("faker",),
    "scrapy": ("scrapy",),
    "tzdata": ("tzdata",),
    "praw": ("praw",),
    "geoalchemy2": ("geoalchemy2",),
    "matplotlib": ("matplotlib",),
    "tqdm": ("tqdm",),
    "redis": ("redis",),
    "toml": ("toml",),
    "attrs": ("attr", "attrs"),
    "rich": ("rich",),
}

WHITELIST_IMPORTS: frozenset[str] = frozenset(
    name for imports in WHITELIST_PIP_TO_IMPORTS.values() for name in imports
)

IMPORT_TO_PIP_PKG: dict[str, str] = {
    imp: pip_pkg
    for pip_pkg, imports in WHITELIST_PIP_TO_IMPORTS.items()
    for imp in imports
}

PYTEST_BUILTIN_FIXTURES: frozenset[str] = frozenset(
    {
        "cache",
        "capfd",
        "capfdbinary",
        "caplog",
        "capsys",
        "capsysbinary",
        "capteesys",
        "doctest_namespace",
        "monkeypatch",
        "pytestconfig",
        "record_property",
        "record_testsuite_property",
        "record_xml_attribute",
        "recwarn",
        "subtests",
        "tmp_path",
        "tmp_path_factory",
        "tmpdir",
        "tmpdir_factory",
        "request",
        "testdir",
        "pytester",
    }
)

# Distinct from v4/v2 markers so v3 patches don't collide with prior runs.
V3_MARKER = "# --- laion gpt5mini v3 patch: install detected test imports ---"
# Older markers we treat as "already patched" — leave alone (idempotency).
PREVIOUS_MARKERS = (
    "# --- laion gpt5mini patch: install detected test imports ---",  # v2
    "# --- laion v4 patch: install detected test imports ---",  # v4 synthetic
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_token(s: str) -> str:
    return s.strip().lower()


def _tokens_in_text(text: str) -> set[str]:
    return {_normalize_token(t) for t in re.findall(r"[A-Za-z0-9_\-\.]+", text)}


def _import_is_allowed(name: str) -> bool:
    """v3: NO instruction_tokens rescue. Only stdlib + ALWAYS + WHITELIST."""
    top = name.split(".")[0]
    if top in STDLIB:
        return True
    if top in ALWAYS_INSTALLED:
        return True
    if top in WHITELIST_IMPORTS:
        return True
    return False


def _top_level_imports(tree: ast.AST) -> tuple[list[str], bool, bool]:
    """Walk the AST; return ``(top_module_names, has_relative, has_src_tests_app)``.

    ``has_src_tests_app`` is True if ANY top-level import has a top-level
    module name in ``{"src", "tests", "app"}``. v3 drops these tasks
    (see module docstring #1).
    """
    names: list[str] = []
    has_relative = False
    has_src_tests_app = False
    bad_tops = {"src", "tests", "app"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
                if alias.name.split(".")[0] in bad_tops:
                    has_src_tests_app = True
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                has_relative = True
                continue
            mod = node.module or ""
            names.append(mod)
            if mod.split(".")[0] in bad_tops:
                has_src_tests_app = True
    return names, has_relative, has_src_tests_app


def _conftest_fixtures(test_dir: Path) -> set[str]:
    cf = test_dir / "conftest.py"
    if not cf.is_file():
        return set()
    try:
        tree = ast.parse(cf.read_text(), filename=str(cf))
    except Exception:
        return set()
    fixtures: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if (
                    (isinstance(dec, ast.Attribute) and dec.attr == "fixture")
                    or (isinstance(dec, ast.Name) and dec.id == "fixture")
                    or (
                        isinstance(dec, ast.Call)
                        and (
                            (
                                isinstance(dec.func, ast.Attribute)
                                and dec.func.attr == "fixture"
                            )
                            or (
                                isinstance(dec.func, ast.Name)
                                and dec.func.id == "fixture"
                            )
                        )
                    )
                ):
                    fixtures.add(node.name)
                    break
    return fixtures


def _test_function_param_names(tree: ast.AST) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test_"):
            params: list[str] = []
            args = node.args
            for a in args.posonlyargs + args.args + args.kwonlyargs:
                if a.arg in ("self", "cls"):
                    continue
                params.append(a.arg)
            out[node.name] = params
    return out


# ---------------------------------------------------------------------------
# Filter passes
# ---------------------------------------------------------------------------


def syntax_passes(test_solution: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(test_solution), doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, f"syntax:{e.msg.splitlines()[0] if e.msg else 'error'}"
    except Exception as e:
        return False, f"compile:{e}"


def src_tests_app_pass(test_solution: Path) -> tuple[bool, str]:
    """v3 NEW: drop tasks whose test_solution.py imports ``src.*``,
    ``tests.*``, or ``app.*`` at file scope. See module docstring #1."""
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception as e:
        return False, f"parse:{e}"
    _, _, has = _top_level_imports(tree)
    if has:
        return False, "src_tests_app"
    return True, ""


def imports_pass(test_solution: Path) -> tuple[bool, str]:
    """v3: NO instruction_tokens rescue (see module docstring #2)."""
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception as e:
        return False, f"parse:{e}"
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _import_is_allowed(alias.name):
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            mod = node.module or ""
            if not _import_is_allowed(mod):
                bad.append(mod)
    if bad:
        return False, f"import:{bad[0]}"
    return True, ""


def fixtures_pass(test_solution: Path) -> tuple[bool, str]:
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception as e:
        return False, f"parse:{e}"
    conftest = _conftest_fixtures(test_solution.parent)
    funcs = _test_function_param_names(tree)
    for name, params in funcs.items():
        for p in params:
            if p in PYTEST_BUILTIN_FIXTURES:
                continue
            if p in conftest:
                continue
            return False, f"fixture:{name}({p})"
    return True, ""


def relative_imports_pass(test_solution: Path) -> tuple[bool, str]:
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception as e:
        return False, f"parse:{e}"
    _, has_relative, _ = _top_level_imports(tree)
    if has_relative:
        return False, "relative_import"
    return True, ""


def rubber_stamp_pass(test_solution: Path) -> tuple[bool, str]:
    """v3 NEW: drop tasks where either
    (a) ALL ``test_*`` functions are decorated with anything containing
        ``skip`` (e.g. ``@pytest.mark.skip``, ``@unittest.skipIf``,
        ``@pytest.mark.skipif(True, ...)``)
    or
    (b) a module-level ``pytest.importorskip("X")`` exists where ``X`` is
        not in ``ALWAYS_INSTALLED`` / stdlib / WHITELIST — i.e. the
        import will always fail in the verifier container, leading to
        all tests being skipped → rubber-stamp pass.
    """
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception as e:
        return False, f"parse:{e}"

    # (b) — module-level importorskip
    for node in tree.body:
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets.append(node.value)
        elif isinstance(node, ast.Expr):
            targets.append(node.value)
        for v in targets:
            if isinstance(v, ast.Call):
                f = v.func
                if (
                    isinstance(f, ast.Attribute)
                    and f.attr == "importorskip"
                    and isinstance(f.value, ast.Name)
                    and f.value.id == "pytest"
                ):
                    if v.args and isinstance(v.args[0], ast.Constant):
                        mod = str(v.args[0].value).split(".")[0]
                        if (
                            mod not in WHITELIST_IMPORTS
                            and mod not in ALWAYS_INSTALLED
                            and mod not in STDLIB
                        ):
                            return False, f"importorskip:{mod}"

    # (a) — all test_* funcs are @*skip*
    test_funcs = [
        n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name.startswith("test_")
    ]
    if test_funcs:
        all_skipped = True
        for tf in test_funcs:
            has_skip = False
            for dec in tf.decorator_list:
                try:
                    src_dec = ast.unparse(dec)
                except Exception:
                    src_dec = ""
                if "skip" in src_dec.lower():
                    has_skip = True
                    break
            if not has_skip:
                all_skipped = False
                break
        if all_skipped:
            return False, "all_test_funcs_skipped"

    return True, ""


# ---------------------------------------------------------------------------
# Mutation: inject pip-installs into test.sh
# ---------------------------------------------------------------------------


def _detect_pip_packages(test_solution: Path) -> list[str]:
    try:
        tree = ast.parse(test_solution.read_text(), filename=str(test_solution))
    except Exception:
        return []
    names, _, _ = _top_level_imports(tree)
    pkgs: list[str] = []
    seen: set[str] = set()
    for full in names:
        top = full.split(".")[0]
        if not top:
            continue
        if top in STDLIB or top in ALWAYS_INSTALLED:
            continue
        pip_pkg = IMPORT_TO_PIP_PKG.get(top)
        if pip_pkg is None:
            continue
        if pip_pkg in seen:
            continue
        seen.add(pip_pkg)
        pkgs.append(pip_pkg)
    return pkgs


def patch_test_sh(test_sh: Path, pkgs: list[str]) -> tuple[bool, str]:
    """Inject the pip-install line into ``test.sh`` after the existing
    ``pip install ... pytest`` line. Idempotent w.r.t. v3, v2 (gpt5mini),
    and v4 (synthetic) markers — any of them being present means we
    leave the file alone (functionally equivalent injections)."""
    if not test_sh.is_file():
        return False, "no-test.sh"
    text = test_sh.read_text()
    if V3_MARKER in text:
        return False, "already-patched-v3"
    for old in PREVIOUS_MARKERS:
        if old in text:
            # An older patcher already injected an install line. The v3
            # patcher's MOTIVATION was different (filter changes, not the
            # injection content). Replace the old block with the v3 block
            # so the install line reflects the v3 expanded whitelist —
            # but only if the new package set is non-empty and DIFFERS
            # from what's already there.
            return _replace_existing_block(test_sh, text, old, pkgs)
    if not pkgs:
        return False, "no-pkgs"

    lines = text.splitlines(keepends=True)
    insert_at: int | None = None
    pip_pytest_re = re.compile(r"pip3?\s+install[^\n]*\bpytest\b")
    for i, ln in enumerate(lines):
        if pip_pytest_re.search(ln):
            insert_at = i + 1
            break
    if insert_at is None:
        return False, "no-pytest-install-line"

    block = _injection_block(pkgs)
    indent = re.match(r"[ \t]*", lines[insert_at - 1]).group(0)
    indented_block = "".join(indent + ln for ln in block.splitlines(keepends=True))

    new_lines = lines[:insert_at] + [indented_block] + lines[insert_at:]
    test_sh.write_text("".join(new_lines))
    return True, f"patched:{','.join(pkgs)}"


def _injection_block(pkgs: list[str]) -> str:
    pkg_str = " ".join(pkgs)
    return (
        f"{V3_MARKER}\n"
        f"pip3 install --break-system-packages --quiet {pkg_str} 2>/dev/null"
        f" || pip3 install --quiet {pkg_str} 2>/dev/null || true\n"
    )


def _replace_existing_block(
    test_sh: Path, text: str, old_marker: str, pkgs: list[str]
) -> tuple[bool, str]:
    """Replace a previous patcher's marker+install line with the v3 block.

    The previous patchers wrote exactly two lines: marker line, then a
    ``pip3 install ... <pkgs> ...`` line. Find that 2-line block and
    swap with the v3 equivalent (which has v3's potentially expanded
    pkg set). If the resulting pkg set is empty AND the old block had
    none, leave the file alone."""
    if not pkgs:
        # Old block exists but v3 detects no pkgs — surprising; leave alone.
        return False, "already-patched-no-pkgs"

    lines = text.splitlines(keepends=True)
    marker_idx: int | None = None
    for i, ln in enumerate(lines):
        if old_marker in ln:
            marker_idx = i
            break
    if marker_idx is None:
        # Shouldn't happen — marker was in text. Fall back to inserting
        # after pytest install.
        return False, "old-marker-not-located"
    # The line right after the marker is the install line written by the
    # old patcher.
    if marker_idx + 1 >= len(lines):
        return False, "truncated-old-block"

    new_block = _injection_block(pkgs)
    indent = re.match(r"[ \t]*", lines[marker_idx]).group(0)
    indented_new = "".join(indent + ln for ln in new_block.splitlines(keepends=True))

    new_lines = lines[:marker_idx] + [indented_new] + lines[marker_idx + 2 :]
    test_sh.write_text("".join(new_lines))
    return True, f"replaced-old-marker:{','.join(pkgs)}"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def filter_one_task(task_dir: Path) -> tuple[str, str]:
    """Run all filter passes. Return ``(verdict, reason)``.

    Pass order:
      1. syntax
      2. src_tests_app (NEW in v3)
      3. imports (v3: no instr_tokens rescue)
      4. fixtures
      5. relative imports
      6. rubber_stamp (NEW in v3)
    """
    test_solution = task_dir / "tests" / "test_solution.py"

    if not test_solution.is_file():
        return "drop", "no-test_solution"

    ok, why = syntax_passes(test_solution)
    if not ok:
        return "drop", why

    ok, why = src_tests_app_pass(test_solution)
    if not ok:
        return "drop", why

    ok, why = imports_pass(test_solution)
    if not ok:
        return "drop", why

    ok, why = fixtures_pass(test_solution)
    if not ok:
        return "drop", why

    ok, why = relative_imports_pass(test_solution)
    if not ok:
        return "drop", why

    ok, why = rubber_stamp_pass(test_solution)
    if not ok:
        return "drop", why

    return "keep", ""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--drop-log", type=str, default=None)
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    counts = {
        "keep": 0,
        "drop_syntax": 0,
        "drop_src_tests_app": 0,
        "drop_import": 0,
        "drop_fixture": 0,
        "drop_relative": 0,
        "drop_rubber_stamp": 0,
        "drop_other": 0,
        "patched": 0,
        "patch_skipped": 0,
    }
    drop_log_lines: list[str] = []
    examples: dict[str, list[str]] = {}

    total = len(task_dirs)
    for i, td in enumerate(task_dirs, 1):
        verdict, reason = filter_one_task(td)
        if verdict == "keep":
            counts["keep"] += 1
            test_sh = td / "tests" / "test.sh"
            test_solution = td / "tests" / "test_solution.py"
            pkgs = _detect_pip_packages(test_solution)
            if not args.dry_run:
                changed, _why = patch_test_sh(test_sh, pkgs)
                if changed:
                    counts["patched"] += 1
                else:
                    counts["patch_skipped"] += 1
            else:
                if pkgs and test_sh.is_file():
                    text = test_sh.read_text()
                    if V3_MARKER not in text:
                        counts["patched"] += 1
                    else:
                        counts["patch_skipped"] += 1
                else:
                    counts["patch_skipped"] += 1
        else:
            if (
                reason.startswith("syntax")
                or reason.startswith("compile")
                or reason.startswith("parse")
            ):
                key = "drop_syntax"
            elif reason.startswith("src_tests_app"):
                key = "drop_src_tests_app"
            elif reason.startswith("import"):
                key = "drop_import"
            elif reason.startswith("fixture"):
                key = "drop_fixture"
            elif reason.startswith("relative"):
                key = "drop_relative"
            elif reason.startswith("importorskip") or reason.startswith(
                "all_test_funcs_skipped"
            ):
                key = "drop_rubber_stamp"
            else:
                key = "drop_other"
            counts[key] += 1
            drop_log_lines.append(f"{td.name}\t{reason}")
            examples.setdefault(key, [])
            if len(examples[key]) < 5:
                examples[key].append(f"{td.name}: {reason}")
            if not args.dry_run:
                shutil.rmtree(td, ignore_errors=True)

        if i % 1000 == 0 or i == total:
            print(f"[{i}/{total}] {counts}", flush=True)

    print()
    print("=" * 60)
    yld = counts["keep"] / total * 100 if total else 0.0
    print(f"Total: {total}  Kept: {counts['keep']} ({yld:.1f}%)  Dry={args.dry_run}")
    for k in (
        "keep",
        "drop_syntax",
        "drop_src_tests_app",
        "drop_import",
        "drop_fixture",
        "drop_relative",
        "drop_rubber_stamp",
        "drop_other",
        "patched",
        "patch_skipped",
    ):
        v = counts[k]
        print(f"  {k:<22}: {v:>5}")
        for ex in examples.get(k, [])[:5]:
            print(f"      {ex}")

    if args.drop_log and drop_log_lines:
        Path(args.drop_log).write_text("\n".join(drop_log_lines) + "\n")
        print(f"\nDrop log: {args.drop_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
