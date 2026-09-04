#!/usr/bin/env python3
"""
exp_rpt_stack-php-large-v2 -> v3 patcher.

Observed failure mode (QC 2026-05-14, 200-trial sample from
``laion/exp_rpt_stack-php-large-v2/traces/``):
  All 200 trials returned reward=0 with the SAME verifier stdout:

      Running PHPUnit tests...
      PHPUnit 10.5.63 by Sebastian Bergmann and contributors.

      Unknown option "--fail-on-no-tests"
      v3 verifier: runner_rc=2 tests_run=0 failures=0 errors=0

  i.e. PHPUnit 10.5.63 rejects ``--fail-on-no-tests`` at option-parse
  time, so it never collects/executes anything. ``runner_rc=2``,
  ``tests_run=0``, and the (correct, defensive) tests_found gate
  writes reward=0 for every trial. Result: 100% infra_ok, 0% solve --
  not a rubber-stamp, but the agent's solution quality is irrelevant
  because the verifier cannot even start.

Root cause (two bugs in tests/test.sh that was baked into the v2
tarballs):

  1. ``--fail-on-no-tests`` does NOT exist in PHPUnit 10.5.x. The
     valid PHPUnit 10 flag is ``--fail-on-empty-test-suite``. The
     v2 tarballs of stack-php-large were produced with a "v3 patch:
     tests_found gate" marker (see ``patch_stack_php_v3_tasks.py``
     / ``patch_exp_rpt_stack_php_v2_tasks.py``) that hard-codes
     ``--fail-on-no-tests``. Confirmed by string-scan of
     phpunit-10.phar 10.5.63: the LONG_OPTIONS table includes
     ``fail-on-empty-test-suite``, ``fail-on-skipped``,
     ``fail-on-warning``, etc., but NOT ``fail-on-no-tests``.

  2. The current ``cd /app`` + bare ``phpunit`` invocation never
     names the test file. Harbor uploads ``tests/`` to ``/tests/``
     inside the container (see
     ``harbor/src/harbor/verifier/verifier.py:90``), not to
     ``/app/tests/``. Even if option parsing succeeded, PHPUnit
     scanning ``/app`` would find no ``*Test.php`` files (the test
     class is named ``TestSolution.php``, which also doesn't match
     the default ``Test.php`` suffix). So the gate would still
     correctly reward=0, but for the wrong reason.

Fix: rewrite ``tests/test.sh`` to:

  - Invoke phpunit against the actual uploaded test file
    (``/tests/TestSolution.php``) with the autoloader bootstrap
    that the Dockerfile already drops at ``/app/autoload.php``,
    AND with ``--test-suffix=Solution.php`` so PHPUnit will accept
    the non-default ``TestSolution.php`` filename.
  - Use the valid PHPUnit 10 flag ``--fail-on-empty-test-suite``
    instead of the made-up ``--fail-on-no-tests``.
  - Keep the original tests_found gate (parse "OK (N tests, ...)"
    / "Tests: N, ..." summary) so reward=1 still requires PHPUnit
    to have actually executed >= 1 test with zero failures and
    zero errors.

Idempotency marker:
  ``# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---``

This marker is distinct from
  - ``# --- laion v3 patch: tests_found gate ---`` (stack-php-v3
    sibling, patch_stack_php_v3_tasks.py)
  - ``# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---``
    (exp_rpt_stack-php-v2 sibling)
so a quick ``grep`` on any test.sh tells you which generation it
came from.

Cross-flag: the sibling dataset ``laion/exp_rpt_stack-php-v2-v2``
has the identical defect (same QC sample: 200/200 trials, same
``Unknown option "--fail-on-no-tests"`` stdout, same
``runner_rc=2 tests_run=0`` line). Whoever re-patches that dataset
should apply an equivalent fix (or just reuse this file's NEW_TEST_SH
under its own marker).

Usage:
  python data/patchers/patch_exp_rpt_stack_php_large_tasks.py \\
      --root <dir> [--dry-run] [--limit N]

Constraints:
  - Only ``tests/test.sh`` is touched. ``instruction.md``,
    ``tests/TestSolution.php``, ``environment/Dockerfile``,
    ``task.toml``, etc. are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Idempotency marker -- distinct from sibling patchers so we can tell
# at a glance which patcher produced a given test.sh.
PATCH_MARKER = "# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---"

# Replacement test.sh body. Same intent as the sibling v3 fix
# (gate reward on runner_rc==0 AND tests_run>=1 AND no failures/errors),
# but with two corrections vs. the v2 baseline:
#   (a) phpunit invocation names the actual test file at /tests/...
#       and bootstraps /app/autoload.php so the autoloader finds the
#       agent's solution classes under /app/.
#   (b) uses the real PHPUnit 10 flag name --fail-on-empty-test-suite
#       (the v2 file used --fail-on-no-tests which doesn't exist in
#       PHPUnit 10.5.x and short-circuits the entire run at option-
#       parse time with runner_rc=2).
NEW_TEST_SH = """#!/bin/bash
# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---
# Verifier: gate reward on (a) clean PHPUnit exit AND (b) PHPUnit
# reporting at least one test actually executed. The v2 test.sh
# invoked `phpunit --fail-on-no-tests` -- a flag that does NOT exist
# in PHPUnit 10.5.63 -- so every trial died at option parse with
# `Unknown option "--fail-on-no-tests"` and runner_rc=2, regardless
# of solution quality. This file uses the valid PHPUnit 10 flag
# (--fail-on-empty-test-suite) AND names the actual test file at
# /tests/TestSolution.php (Harbor uploads tests/ to /tests/, not
# /app/tests/). --test-suffix=Solution.php is required because
# PHPUnit's default suffix is `Test.php` and our class file is
# `TestSolution.php`.

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

echo "Running PHPUnit tests..."
# --fail-on-empty-test-suite: real PHPUnit 10 flag; exits non-zero if
#   0 tests were collected.
# --fail-on-skipped: belt-and-suspenders against suites that are all
#   skipped.
# --bootstrap /app/autoload.php: registers the PSR-4-style autoloader
#   the Dockerfile drops at build time so PHPUnit can resolve the
#   agent's solution classes under /app/.
# --test-suffix=Solution.php: our test class file is named
#   TestSolution.php, which does NOT match the default Test.php
#   suffix. Without this, --fail-on-empty-test-suite would (correctly)
#   fire because PHPUnit would scan and find no tests.
# /tests/TestSolution.php: explicit test path; Harbor mounts tests/
#   at /tests/, not /app/tests/.
phpunit \\
    --bootstrap /app/autoload.php \\
    --fail-on-empty-test-suite \\
    --fail-on-skipped \\
    --test-suffix=Solution.php \\
    /tests/TestSolution.php 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# PHPUnit 10 summary line shapes:
#   "OK (3 tests, 5 assertions)"
#   "Tests: 3, Assertions: 5, Failures: 0, Errors: 0"
#   "No tests executed!"  (suppressed when --fail-on-empty-test-suite
#                          flips exit to non-zero, but we still parse
#                          defensively)
ok_line=$(grep -oE 'OK \\([0-9]+ tests?, [0-9]+ assertions?\\)' \\
    /logs/verifier/test_output.txt | tail -1)
detail_line=$(grep -oE 'Tests: [0-9]+(, Assertions: [0-9]+)?(, Failures: [0-9]+)?(, Errors: [0-9]+)?' \\
    /logs/verifier/test_output.txt | tail -1)

tests_run=0
failures=0
errors=0
if [ -n "$ok_line" ]; then
    tests_run=$(echo "$ok_line" | grep -oE '[0-9]+' | head -1)
elif [ -n "$detail_line" ]; then
    tests_run=$(echo "$detail_line" | grep -oE 'Tests: [0-9]+' | grep -oE '[0-9]+' | head -1)
    failures=$(echo "$detail_line" | grep -oE 'Failures: [0-9]+' | grep -oE '[0-9]+' | head -1)
    errors=$(echo "$detail_line"   | grep -oE 'Errors: [0-9]+'   | grep -oE '[0-9]+' | head -1)
fi
tests_run=${tests_run:-0}
failures=${failures:-0}
errors=${errors:-0}

echo "exp_rpt_stack-php-large-v3 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

if [ "$runner_rc" -eq 0 ] \\
        && [ "$tests_run" -ge 1 ] \\
        && [ "$failures" -eq 0 ] \\
        && [ "$errors" -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
    exit 0
else
    echo "0" > /logs/verifier/reward.txt
    if [ "$runner_rc" -ne 0 ]; then exit "$runner_rc"; fi
    exit 1
fi
"""


def patch_one(test_sh: Path, dry_run: bool) -> str:
    """Patch a single tests/test.sh file. Returns one of:
    'patched', 'patched_unusual', 'already', 'missing',
    'skipped_no_phpunit', 'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if PATCH_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke phpunit -- they're
    # not PHPUnit tasks (or use some other harness) and we'd corrupt them
    # by replacing the file with our PHPUnit-specific gate.
    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    # Sanity: the broken v2 file we're patching has either the original
    # "laion v3 patch: tests_found gate" marker (from
    # patch_stack_php_v3_tasks.py) and/or the bare `--fail-on-no-tests`
    # invocation. Anything else is unusual and worth flagging.
    is_expected = (
        "--fail-on-no-tests" in existing
        or "laion v3 patch: tests_found gate" in existing
    )

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
    return "patched" if is_expected else "patched_unusual"


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
    counts = {
        "patched": 0,
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
                f"[{i}/{n_total}] patched={counts['patched']} "
                f"patched_unusual={counts['patched_unusual']} "
                f"already={counts['already']} missing={counts['missing']} "
                f"skipped_no_phpunit={counts['skipped_no_phpunit']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched={counts['patched']} "
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
