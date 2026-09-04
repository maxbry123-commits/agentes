#!/usr/bin/env python3
"""
exp_rpt_stack-php-v2 → v5 patcher.

Bug fixed in v5 (found in QC 2026-05-17, 200-trial sample from
``laion/exp_rpt_stack-php-v2-v4/traces/``):

  v4 took the CLI-only invocation path
    ``phpunit --bootstrap=... --test-suffix=Solution.php /tests/TestSolution.php``
  on the (correct) theory that this would let PHPUnit 10.5 discover and
  run the test class. It did not. 0 / 200 trials produced reward=1. The
  full failure-mode distribution across the 200-trial sample:

      65  Class TestSolution cannot be found in /tests/TestSolution.php
      45  Class "PHPUnit_Framework_TestCase" not found
      23  must be compatible with PHPUnit (setUp signature drift)
      21  Class "Tests\\TestCase" not found
      46  Other framework bases (Cake\\TestSuite\\TestCase,
          Orchestra\\Testbench\\TestCase, Zend\\..., Xpmock\\TestCase,
          Yii\\..., RDS\\Hydrogen\\..., etc.)
       0  OK (...) / Tests: N lines

  Root cause #1 (65/200): PHPUnit 10's ``Runner\\TestSuiteLoader::load``
    requires the file basename ("TestSolution") to match a declared class
    inside the file. Real TestSolution.php files declare classes named
    after their upstream repo (e.g. ``DataTest``, ``AuthTest``, ``EditorTest``)
    not ``TestSolution``. ``--test-suffix=Solution.php`` only filters
    *which files* PHPUnit looks at; it does not relax the basename rule
    once a file is selected.

  Root cause #2 (45 + 21 + portions of "other" = ~75/200): The container
    only ships PHPUnit 10.5 with the namespaced ``PHPUnit\\Framework\\TestCase``.
    Upstream test files commonly reference PHPUnit 4-6 era
    ``PHPUnit_Framework_TestCase`` or framework-specific bases like
    ``Tests\\TestCase`` (Laravel) that aren't defined unless the project's
    own composer install ran. v4 didn't ship any aliasing or stub
    classes, so these references die at class-load time.

  Root cause #3 (23/200): Method-signature drift between PHPUnit majors.
    A test class with ``public function setUp()`` (no return type)
    extending a PHPUnit-10 ``PHPUnit\\Framework\\TestCase`` (which has
    ``protected function setUp(): void``) triggers a PHP fatal at class
    load. Not fixable from test.sh.

Fix (v5):

  This is a verbatim port of the v4 design that was originally written
  for laion/exp_rpt_stack-php-large (root causes #1 and #2 are identical
  across the two datasets — same container, same Harbor mount layout,
  same upstream test-file authoring style). The two patchers now share
  the test.sh template via ``_stack_php_common.new_test_sh`` so a future
  fix lands in one place.

  Key differences vs. v4 (this dataset's previous generation):
    - Drops the CLI-only invocation; uses /app/phpunit.xml with a
      bootstrap shim instead.
    - Bootstrap pre-includes /tests/TestSolution.php inside a
      try/catch, then walks ``get_declared_classes()`` to find the
      class extending ``PHPUnit\\Framework\\TestCase``, then
      ``class_alias``es it as ``TestSolution`` to satisfy PHPUnit's
      basename rule. **This is the principal fix for root cause #1.**
    - Bootstrap pre-defines ``PHPUnit_Framework_TestCase`` (via
      class_alias) and ``Tests\\TestCase`` (via eval'd stub) before
      the test file is required. **This is the fix for root cause #2.**
    - composer dump-autoload runs opportunistically so the agent's
      namespaced solution classes resolve.

  Expected recovery: the basename + legacy-base failure modes
  (65 + 45 + 21 = 131 / 200, ~65%) should pass to the test-execution
  stage. The remaining ~35% are signature drift or long-tail
  framework-specific bases that can't be fixed without modifying
  TestSolution.php (out of scope per the upload spec) or installing
  upstream packages (out of scope for a test.sh-only patch).

Idempotency marker (also embedded as a shell comment at the top of
the generated test.sh):

    # --- laion stack-php-v2-v5 patch: alias_TestSolution + shim_bootstrap ---

Usage:
  python data/patchers/patch_exp_rpt_stack_php_v2_v5_tasks.py \
      --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only ``tests/test.sh`` is touched. instruction.md, TestSolution.php,
    environment/Dockerfile, etc. are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow this script to run as a script (no package context) by ensuring
# the parent directory is on sys.path so ``_stack_php_common`` resolves.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _stack_php_common import new_test_sh, patch_marker  # noqa: E402

DATASET_TAG = "stack-php-v2-v5"

# Idempotency marker — checked first to skip already-patched tasks.
PATCH_MARKER = patch_marker(DATASET_TAG)

# Markers from earlier patch generations — we want to overwrite any of these
# so re-runs converge on v5.
PRIOR_MARKERS = (
    "# --- laion exp_rpt_stack-php-v2 v4 patch: tests-on-/tests + cli-only ---",  # v4
    "# --- laion exp_rpt_stack-php-v2 v3 patch: phpunit_xml + tests_found gate ---",  # v3
    "# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---",  # v2-v2
    "# --- laion v3 patch: tests_found gate ---",  # stack-php-large v3 misapplied
)

NEW_TEST_SH = new_test_sh(DATASET_TAG)


def patch_one(test_sh: Path, dry_run: bool) -> str:
    """Patch a single tests/test.sh file.

    Returns one of: ``patched_from_v4``, ``patched_from_v3``,
    ``patched_from_v2_v2``, ``patched_from_v3_large``, ``patched_from_original``,
    ``patched_unusual``, ``already``, ``missing``, ``skipped_no_phpunit``,
    ``unparseable``.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if PATCH_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke phpunit — they're
    # not PHPUnit tasks (or use some other harness) and we'd corrupt them
    # by replacing the file with our PHPUnit-specific gate.
    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    # Classify the prior generation for forensics (the result body is the
    # same regardless of source).
    if PRIOR_MARKERS[0] in existing:
        source = "patched_from_v4"
    elif PRIOR_MARKERS[1] in existing:
        source = "patched_from_v3"
    elif PRIOR_MARKERS[2] in existing:
        source = "patched_from_v2_v2"
    elif PRIOR_MARKERS[3] in existing:
        source = "patched_from_v3_large"
    elif "trap cleanup EXIT" in existing:
        source = "patched_from_original"
    else:
        source = "patched_unusual"

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
    return source


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Path to extracted tasks root")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts: dict[str, int] = {
        "patched_from_v4": 0,
        "patched_from_v3": 0,
        "patched_from_v2_v2": 0,
        "patched_from_v3_large": 0,
        "patched_from_original": 0,
        "patched_unusual": 0,
        "already": 0,
        "missing": 0,
        "skipped_no_phpunit": 0,
        "unparseable": 0,
    }

    for i, td in enumerate(task_dirs, 1):
        test_sh = td / "tests" / "test.sh"
        result = patch_one(test_sh, dry_run=args.dry_run)
        counts[result] = counts.get(result, 0) + 1

        if i % 1000 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] "
                f"from_v4={counts['patched_from_v4']} "
                f"from_v3={counts['patched_from_v3']} "
                f"from_v2_v2={counts['patched_from_v2_v2']} "
                f"from_v3_large={counts['patched_from_v3_large']} "
                f"from_original={counts['patched_from_original']} "
                f"unusual={counts['patched_unusual']} "
                f"already={counts['already']} missing={counts['missing']} "
                f"skipped_no_phpunit={counts['skipped_no_phpunit']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched_from_v4={counts['patched_from_v4']} "
        f"patched_from_v3={counts['patched_from_v3']} "
        f"patched_from_v2_v2={counts['patched_from_v2_v2']} "
        f"patched_from_v3_large={counts['patched_from_v3_large']} "
        f"patched_from_original={counts['patched_from_original']} "
        f"patched_unusual={counts['patched_unusual']} "
        f"already_patched={counts['already']} "
        f"missing={counts['missing']} "
        f"skipped_no_phpunit={counts['skipped_no_phpunit']} "
        f"unparseable={counts['unparseable']} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
