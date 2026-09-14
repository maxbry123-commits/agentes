#!/usr/bin/env python3
"""Unified linter: orchestrates structural checks, dead-code detection, and lint tools."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from checks import CheckError, is_excluded, is_excepted, is_lintignored, collect_lintignores
from checks.structural import check_file_lines, check_folder_items, check_nested_imports
from checks.vulture import run_vulture
from checks.eslint import run_eslint
from checks.knip import run_knip
from checks.endpoints import run_endpoint_check
from checks.classes import run_class_check
from checks.cycles import run_cycle_check
from checks.dangling_refs import run_dangling_refs_check
from checks.no_underscore_names import run_underscore_check
from checks.p_private import run_p_private_check
from checks.ruff import run_ruff
from checks.pyright import run_pyright
from watchfiles import watch, DefaultFilter

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config" / "config.json"


def load_config() -> dict[str, Any]:
    with open(CONFIG_FILE) as f:
        return json.load(f)


def run_checks(root: Path) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str], list[str], list[str], list[str], list[str], list[str], list[str]]:
    config = load_config()
    enabled: dict[str, bool] = config.get("enabled", {})
    rules: dict[str, int] = config["rules"]
    excludes: list[str] = config["exclude"]
    exceptions: dict[str, list[str]] = config["exceptions"]
    extensions: list[str] = config["include_extensions"]
    ignores = collect_lintignores(root, excludes)

    max_lines: int = rules["max-file-lines"]
    max_items: int = rules["max-folder-items"]
    check_imports: bool = rules.get("no-nested-imports", False)
    structural_errors: list[str] = []
    grandfathered_oversize: list[str] = []

    file_lines_on = enabled.get("max-file-lines", True)
    folder_items_on = enabled.get("max-folder-items", True)
    nested_imports_on = enabled.get("no-nested-imports", True)

    for dirpath_str, dirnames, filenames in os.walk(root):
        dp = Path(dirpath_str)

        if is_excluded(dp, root, excludes):
            dirnames.clear()
            continue

        rel_dir = str(dp.relative_to(root))
        if (
            folder_items_on
            and rel_dir != "."
            and not is_excepted(rel_dir, "max-folder-items", exceptions)
            and not is_lintignored(dp, root, "max-folder-items", ignores)
        ):
            result = check_folder_items(dp, root, max_items, excludes)
            if result:
                structural_errors.append(result[0])

        for fname in filenames:
            fp = dp / fname
            if fp.suffix not in extensions:
                continue
            if is_excluded(fp, root, excludes):
                continue
            rel_file = str(fp.relative_to(root))
            # Debt counts only config-grandfathered files (ours, deferred); .lintignore is vendored/generated code and stays out of both numbers.
            if file_lines_on and not is_lintignored(fp, root, "max-file-lines", ignores):
                p_grandfathered = is_excepted(rel_file, "max-file-lines", exceptions)
                result = check_file_lines(fp, root, max_lines)
                if result:
                    if p_grandfathered:
                        # Debt is counted even where the gate is silenced: 82 of 102 oversized files were invisible because the exception list hid them from the tally too (ENG-192).
                        grandfathered_oversize.append(rel_file)
                    else:
                        structural_errors.append(result[0])
            if (
                nested_imports_on
                and check_imports
                and not is_excepted(rel_file, "no-nested-imports", exceptions)
                and not is_lintignored(fp, root, "no-nested-imports", ignores)
            ):
                structural_errors.extend(check_nested_imports(fp, root))

    if grandfathered_oversize:
        # The debt line, not a gate: the enforcement number alone made 82 silenced oversized files read as a clean repo.
        print(f"structural: NOTE {len(grandfathered_oversize)} grandfathered file(s) over {max_lines} lines (debt, not enforced); largest offenders:", flush=True)
        p_sized = sorted(((sum(1 for _ in open(root / f, errors='ignore')), f) for f in grandfathered_oversize), reverse=True)
        for p_n, p_f in p_sized[:5]:
            print(f"  {p_f}: {p_n} lines", flush=True)

    vulture_errors: list[str] = []
    if enabled.get("vulture", True):
        vulture_confidence = rules.get("vulture-min-confidence")
        if vulture_confidence is not None:
            vulture_error_threshold = rules.get("vulture-error-threshold", 100)
            vulture_errors = run_vulture(
                root, vulture_confidence, vulture_error_threshold, exceptions, ignores,
            )

    eslint_errors = run_eslint(root, ignores) if enabled.get("eslint", True) else []
    knip_errors = run_knip(root, ignores) if enabled.get("knip", True) else []
    endpoint_ignore_routes: list[str] = rules.get("endpoint-ignore-routes", [])
    endpoint_errors = run_endpoint_check(root, exceptions, endpoint_ignore_routes, ignores) if enabled.get("endpoints", True) else []
    class_errors = run_class_check(root, exceptions, excludes, ignores) if enabled.get("classes", True) else []
    aliases: dict[str, str] = rules.get("import-cycle-aliases", {})
    cycle_errors = run_cycle_check(root, excludes, aliases, exceptions, ignores) if enabled.get("import-cycles", True) else []

    # Convention checks (ported from Haik's linter): ban leading-underscore names
    # (dead-code tooling blind spot) and enforce p_-private access boundaries.
    underscore_errors = run_underscore_check(root, exceptions, excludes, ignores) if enabled.get("no-underscore-names", False) else []
    p_private_errors = run_p_private_check(root, exceptions, excludes, ignores) if enabled.get("p-private", False) else []

    # A dangling reference becomes a linter error at declaration time, not a blank card six months later.
    dangling_ref_errors: list[str] = []
    if enabled.get("dangling-refs", False):
        try:
            dangling_ref_errors = run_dangling_refs_check(root, exceptions, excludes, ignores)
        except CheckError as e:
            dangling_ref_errors = [f"dangling-refs: check could not run: {e.reason}"]

    # ruff (scoped dead-code codes) + pyright (existence errors), also from Haik's
    # linter. Both shell out to a tool, so a missing tool / timeout raises CheckError
    # and is surfaced as a loud error rather than a silently-clean empty result.
    ruff_errors: list[str] = []
    if enabled.get("ruff", False):
        try:
            ruff_errors = run_ruff(root, rules.get("ruff-select", "F401,F811,F841,ARG001,ARG002"), exceptions, ignores)
        except CheckError as e:
            ruff_errors = [f"ruff: check could not run: {e.reason}"]
    pyright_errors: list[str] = []
    if enabled.get("pyright", False):
        try:
            pyright_errors = run_pyright(root, exceptions, ignores)
        except CheckError as e:
            pyright_errors = [f"pyright: check could not run: {e.reason}"]

    return sorted(structural_errors), sorted(vulture_errors), sorted(eslint_errors), sorted(knip_errors), sorted(endpoint_errors), sorted(class_errors), sorted(cycle_errors), sorted(underscore_errors), sorted(p_private_errors), sorted(dangling_ref_errors), sorted(ruff_errors), sorted(pyright_errors)


def _print_section(name: str, errors: list[str]) -> None:
    print(f"{name}: checking...", flush=True)
    for e in errors:
        print(e, flush=True)
    print(f"{name}: done. {len(errors)} error(s) found.", flush=True)


def print_results(
    structural_errors: list[str], vulture_errors: list[str],
    eslint_errors: list[str], knip_errors: list[str],
    endpoint_errors: list[str], class_errors: list[str],
    cycle_errors: list[str], underscore_errors: list[str],
    p_private_errors: list[str], dangling_ref_errors: list[str],
    ruff_errors: list[str], pyright_errors: list[str],
) -> None:
    _print_section("structural", structural_errors)
    _print_section("vulture", vulture_errors)
    _print_section("eslint", eslint_errors)
    _print_section("knip", knip_errors)
    _print_section("endpoints", endpoint_errors)
    _print_section("classes", class_errors)
    _print_section("import-cycles", cycle_errors)
    _print_section("no-underscore-names", underscore_errors)
    _print_section("p-private", p_private_errors)
    _print_section("dangling-refs", dangling_ref_errors)
    _print_section("ruff", ruff_errors)
    _print_section("pyright", pyright_errors)


def watch_loop(root: Path) -> None:

    config_dir = SCRIPT_DIR / "config"

    print_results(*run_checks(root))

    class SourceFilter(DefaultFilter):
        allowed_extensions = (".py", ".ts", ".tsx", ".js", ".jsx")

        def __call__(self, change: Any, path: str) -> bool:
            if not super().__call__(change, path):
                return False
            if Path(path).suffix in self.allowed_extensions:
                return True
            p = Path(path)
            if p.suffix == ".json" and (p.parent == SCRIPT_DIR or p.parent == config_dir):
                return True
            if p.name.startswith(".lintignore"):
                return True
            return Path(path).is_dir()

    for _changes in watch(root, watch_filter=SourceFilter()):
        print_results(*run_checks(root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified linter")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--root", type=str, default=".", help="Root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.watch:
        watch_loop(root)
    else:
        results = run_checks(root)
        print_results(*results)
        sys.exit(1 if any(results) else 0)


if __name__ == "__main__":
    main()
