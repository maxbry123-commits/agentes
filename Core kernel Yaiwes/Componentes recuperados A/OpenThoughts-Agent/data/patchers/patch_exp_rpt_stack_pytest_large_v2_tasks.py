#!/usr/bin/env python3
"""Make the Stack-Pytest large corpus dependency-complete and snapshot-safe.

The upstream 5,000-task corpus has one shared image but its verifier only
installs pytest.  Tests consequently fail at collection when they import a
real third-party library.  This patcher uses each task's ``target_module``
metadata to distinguish the package that an agent must implement from genuine
test dependencies.  It writes explicit, task-local requirements and installs
them in the same venv for both the agent instructions and verifier.

Tasks with invalid tests, an ambiguous target, unsupported/private imports, or
unresolvable fixtures are removed rather than silently shipping a broken or
leaky verifier.  The supported dependency map deliberately excludes large ML
frameworks and packages whose import name cannot be resolved unambiguously.
"""

from __future__ import annotations

import argparse
import ast
import json
import py_compile
import re
import shutil
import sys
from collections import Counter
from pathlib import Path


MARKER = "# --- laion stack-pytest-large v2 dependency bootstrap ---"
INSTRUCTION_MARKER = "<!-- laion stack-pytest-large v2 dependency bootstrap -->"
STDLIB = frozenset(sys.stdlib_module_names) | frozenset(
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
PIP_BY_IMPORT = {
    "aiohttp": "aiohttp",
    "attrs": "attrs",
    "boto3": "boto3",
    "botocore": "botocore",
    "bs4": "beautifulsoup4",
    "click": "click",
    "cryptography": "cryptography",
    "cv2": "opencv-python-headless",
    "dask": "dask",
    "dateutil": "python-dateutil",
    "django": "Django",
    "dotenv": "python-dotenv",
    "faker": "Faker",
    "fastapi": "fastapi",
    "flask": "Flask",
    "freezegun": "freezegun",
    "httpx": "httpx",
    "hypothesis": "hypothesis",
    "importlib_metadata": "importlib-metadata",
    "jinja2": "Jinja2",
    "keras": "keras",
    "lxml": "lxml",
    "loguru": "loguru",
    "marshmallow": "marshmallow",
    "matplotlib": "matplotlib",
    "mock": "mock",
    "networkx": "networkx",
    "nose": "nose",
    "notebook": "notebook",
    "nltk": "nltk",
    "numpy": "numpy",
    "nbformat": "nbformat",
    "pandas": "pandas",
    "pathlib2": "pathlib2",
    "PIL": "Pillow",
    "pydantic": "pydantic",
    "pygments": "Pygments",
    "pymongo": "pymongo",
    "pytest_cov": "pytest-cov",
    "pytz": "pytz",
    "redis": "redis",
    "regex": "regex",
    "requests": "requests",
    "requests_mock": "requests-mock",
    "responses": "responses",
    "rich": "rich",
    "scipy": "scipy",
    "seaborn": "seaborn",
    "setuptools": "setuptools",
    "six": "six",
    "sklearn": "scikit-learn",
    "spacy": "spacy",
    "sqlalchemy": "SQLAlchemy",
    "statsmodels": "statsmodels",
    "sympy": "sympy",
    "toml": "toml",
    "typer": "typer",
    "ujson": "ujson",
    "unittest2": "unittest2",
    "werkzeug": "Werkzeug",
    "xarray": "xarray",
    "yaml": "PyYAML",
}
PYTEST_BUILTIN_FIXTURES = frozenset(
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
        "request",
        "subtests",
        "testdir",
        "tmp_path",
        "tmp_path_factory",
        "tmpdir",
        "tmpdir_factory",
        "pytester",
    }
)
BAD_LOCAL_IMPORTS = frozenset({"app", "src", "test", "tests"})


def test_imports(test_path: Path) -> set[str]:
    """Return all non-relative imports in a test module."""
    tree = ast.parse(
        test_path.read_text(encoding="utf-8", errors="replace"), filename=str(test_path)
    )
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def imported_modules(test_path: Path) -> set[str]:
    """Return full non-relative module paths needed at test collection time."""
    tree = ast.parse(
        test_path.read_text(encoding="utf-8", errors="replace"), filename=str(test_path)
    )
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            modules.add(node.module)
    return modules


def fixtures_in_file(path: Path) -> set[str]:
    """Return fixture names declared directly in one Python file."""
    if not path.is_file():
        return set()
    tree = ast.parse(
        path.read_text(encoding="utf-8", errors="replace"), filename=str(path)
    )
    fixtures: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            function = decorator.func if isinstance(decorator, ast.Call) else decorator
            if (isinstance(function, ast.Attribute) and function.attr == "fixture") or (
                isinstance(function, ast.Name) and function.id == "fixture"
            ):
                fixtures.add(node.name)
    return fixtures


def fixture_error(test_path: Path) -> str | None:
    tree = ast.parse(
        test_path.read_text(encoding="utf-8", errors="replace"), filename=str(test_path)
    )
    known = (
        PYTEST_BUILTIN_FIXTURES
        | fixtures_in_file(test_path)
        | fixtures_in_file(test_path.parent / "conftest.py")
    )
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) or not node.name.startswith("test_"):
            continue
        for argument in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            if argument.arg not in {"self", "cls"} and argument.arg not in known:
                return f"fixture:{node.name}({argument.arg})"
    return None


def missing_test_asset(test_path: Path) -> str | None:
    """Reject a test that names an absent file under Harbor's mounted /tests."""
    tree = ast.parse(
        test_path.read_text(encoding="utf-8", errors="replace"), filename=str(test_path)
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        if not value.startswith("/tests/"):
            continue
        relative = value.removeprefix("/tests/")
        if relative and not (test_path.parent / relative).is_file():
            return f"missing-test-asset:{relative}"
    return None


def target_module(task_dir: Path) -> str:
    metadata = json.loads((task_dir / "metadata.json").read_text(encoding="utf-8"))
    target = str(metadata.get("target_module", "")).strip().split(".")[0]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
        raise ValueError("invalid-target")
    return target


def task_requirements(task_dir: Path) -> tuple[list[str] | None, str | None]:
    """Resolve safe test dependencies, returning a drop reason when ambiguous."""
    test_path = task_dir / "tests" / "test_solution.py"
    if not test_path.is_file():
        return None, "missing-test"
    try:
        py_compile.compile(str(test_path), doraise=True)
        target = target_module(task_dir)
        imports = test_imports(test_path)
        modules = imported_modules(test_path)
    except py_compile.PyCompileError:
        return None, "syntax"
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError):
        return None, "invalid-test-or-metadata"
    if target not in imports:
        return None, "target-not-imported"
    instruction = (
        (task_dir / "instruction.md")
        .read_text(encoding="utf-8", errors="replace")
        .lower()
    )
    for module in modules:
        if module.startswith(f"{target}.") and module.lower() not in instruction:
            return None, f"unexplained-target-submodule:{module}"
    external = imports - STDLIB - {target}
    if external & BAD_LOCAL_IMPORTS:
        return None, f"ambiguous-local-import:{sorted(external & BAD_LOCAL_IMPORTS)[0]}"
    unsupported = external - PIP_BY_IMPORT.keys()
    if unsupported:
        return None, f"unsupported-import:{sorted(unsupported)[0]}"
    bad_fixture = fixture_error(test_path)
    if bad_fixture:
        return None, bad_fixture
    absent_asset = missing_test_asset(test_path)
    if absent_asset:
        return None, absent_asset
    requirements = {PIP_BY_IMPORT[name] for name in external}
    for import_name, package in PIP_BY_IMPORT.items():
        if re.search(
            rf"(?<![a-z0-9_]){re.escape(import_name.lower())}(?![a-z0-9_])", instruction
        ):
            requirements.add(package)
    return sorted(requirements, key=str.lower), None


def patch_dockerfile(dockerfile: Path) -> None:
    """Pre-create the common venv so agents and verifiers use one runtime."""
    text = dockerfile.read_text(encoding="utf-8")
    if MARKER in text:
        return
    text = text.replace("python3-venv bsdutils", "python3-venv bsdutils git")
    text = text.rstrip() + (
        f"\n\n{MARKER}\nRUN python3 -m venv /app/.venv\nENV PATH=/app/.venv/bin:$PATH\n"
    )
    dockerfile.write_text(text, encoding="utf-8")


def patch_test_script(test_script: Path) -> None:
    text = test_script.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        return
    needle = "pip install --quiet pytest"
    if needle not in text:
        raise ValueError("missing-pytest-install")
    bootstrap = (
        f"{MARKER}\n"
        "# Dependencies are statically resolved from this task's test imports.\n"
        "if [ -s /tests/requirements.txt ]; then\n"
        "    pip install --quiet -r /tests/requirements.txt\n"
        "fi"
    )
    test_script.write_text(
        text.replace(needle, f"{needle}\n\n{bootstrap}", 1), encoding="utf-8"
    )


def patch_instruction(instruction: Path, requirements: list[str]) -> None:
    text = instruction.read_text(encoding="utf-8", errors="replace")
    if INSTRUCTION_MARKER in text:
        return
    requirement_text = (
        "\n".join(f"- `{requirement}`" for requirement in requirements)
        or "- No third-party packages beyond pytest."
    )
    block = (
        f"\n\n{INSTRUCTION_MARKER}\n"
        "## Runtime dependencies\n\n"
        "The task container has a shared virtual environment at `/app/.venv`. "
        "Before executing code that imports a listed dependency, activate it and install the "
        "task's captured requirements:\n\n"
        "```bash\nsource /app/.venv/bin/activate\npip install --quiet -r /tests/requirements.txt\n```\n\n"
        "Captured third-party test dependencies:\n"
        f"{requirement_text}\n"
    )
    instruction.write_text(text.rstrip() + block, encoding="utf-8")


def patch_task(task_dir: Path, dry_run: bool) -> str:
    requirements, reason = task_requirements(task_dir)
    if reason:
        return reason
    assert requirements is not None
    if dry_run:
        return "keep"
    patch_dockerfile(task_dir / "environment" / "Dockerfile")
    (task_dir / "tests" / "requirements.txt").write_text(
        "\n".join(requirements) + ("\n" if requirements else ""), encoding="utf-8"
    )
    patch_test_script(task_dir / "tests" / "test.sh")
    patch_instruction(task_dir / "instruction.md", requirements)
    return "keep"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="0 means all tasks")
    parser.add_argument("--drop-log", type=Path)
    args = parser.parse_args()
    task_dirs = sorted(path for path in args.root.iterdir() if path.is_dir())
    if args.limit > 0:
        task_dirs = task_dirs[: args.limit]
    counts: Counter[str] = Counter()
    dropped: list[str] = []
    for index, task_dir in enumerate(task_dirs, 1):
        result = patch_task(task_dir, args.dry_run)
        counts[result] += 1
        if result != "keep":
            dropped.append(f"{task_dir.name}\t{result}")
            if not args.dry_run:
                shutil.rmtree(task_dir)
        if index % 500 == 0 or index == len(task_dirs):
            print(
                f"[{index}/{len(task_dirs)}] kept={counts['keep']} dropped={index - counts['keep']}",
                flush=True,
            )
    if args.drop_log:
        args.drop_log.write_text(
            "\n".join(dropped) + ("\n" if dropped else ""), encoding="utf-8"
        )
    print(
        f"total={len(task_dirs)} kept={counts['keep']} dropped={len(task_dirs) - counts['keep']} dry_run={args.dry_run}"
    )
    for reason, count in sorted(counts.items()):
        print(f"{reason}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
