#!/usr/bin/env python3
"""
exp_rpt_stack-php-v2 → v4 patcher.

Bug (v3, found in QC 2026-05-16):
  v3 took a different approach from sibling stack-php-large-v3: it generated a
  /app/phpunit.xml on the fly with `<file>tests/TestSolution.php</file>` and
  ran `phpunit --configuration /app/phpunit.xml ...` after `cd /app`. Every
  single trial (200/200) died with:

      Running PHPUnit tests...
      PHPUnit 10.5.63 by Sebastian Bergmann and contributors.

      Test file "/app/tests/TestSolution.php" not found
      exp_rpt_stack-php-v2 v3 verifier: runner_rc=2 tests_run=0 failures=0 \
        errors=0 bootstrap=/app/autoload.php

  Root cause (verified across 10 sampled traces):
    Harbor copies the task's `tests/` directory into the container at **`/tests/`**
    (see harbor/src/harbor/models/trial/paths.py:39 → `tests_dir = PurePosixPath("/tests")`
    and harbor/src/harbor/verifier/verifier.py:139-147 → uploads tests/ to
    `env_paths.tests_dir` = `/tests` and executes `/tests/test.sh`).

    The v3 phpunit.xml used the relative path `tests/TestSolution.php` with
    `cd /app`, which expanded to `/app/tests/TestSolution.php` — a path that
    does not exist in the container. The Dockerfile never copies tests
    anywhere under /app/ (`COPY tests` is not in the Dockerfile and Harbor's
    `copy_tests_if_referenced` only acts on COPY/ADD-referenced trees).

    Bootstrap fallback chain worked (`bootstrap=/app/autoload.php` per the
    verifier output line), and the phpunit.xml itself was parsed cleanly —
    PHPUnit's "Test file not found" message proves both. The single broken
    leg was the test file's *location*.

Fix (v4):
  Converge with the sibling stack-php-large-v3 patcher (which uses the
  CLI-flag-only approach and has the SAME container layout):
    - Drop the runtime phpunit.xml generation entirely. It added complexity
      without buying anything that CLI flags can't do, and one of its
      attributes (the relative <file> path) caused the failure.
    - Invoke phpunit with explicit /tests/TestSolution.php (absolute path).
    - Use --test-suffix=Solution.php so PHPUnit accepts `TestSolution.php`
      (default suffix is `Test.php`).
    - Use --fail-on-empty-test-suite (real PHPUnit 10.5 flag) + --fail-on-skipped.
    - Prefer /app/vendor/autoload.php (composer-generated PSR-4) and fall
      back to /app/autoload.php (Dockerfile-baked naive `<class>` mapper).
      The composer path is the one that actually resolves the
      Rodacker\\Sleddog\\... -> /app/app/... class layout the instruction
      asks the agent to create; the naive fallback is a last-resort gate
      so PHPUnit at least loads.
    - Keep the same numeric parse + tests_run≥1 + failures==0 + errors==0
      reward gate as v3 (independent of exit code).

  Idempotency marker:
      `# --- laion exp_rpt_stack-php-v2 v4 patch: tests-on-/tests + cli-only ---`

  The same root cause may apply to other PHP datasets that adopted the
  "generate phpunit.xml" approach; this v4 template converges them all
  back to the CLI-only flow that the sibling stack-php-large-v3 already
  uses successfully.

If a task has no `tests/test.sh` or its existing test.sh has no `phpunit`
invocation, it is left untouched and counted as `skipped_no_phpunit`.

Usage:
  python data/patchers/patch_exp_rpt_stack_php_v2_v4_tasks.py \
      --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only `tests/test.sh` is touched. instruction.md, TestSolution.php,
    environment/Dockerfile, etc. are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
PATCH_MARKER = (
    "# --- laion exp_rpt_stack-php-v2 v4 patch: tests-on-/tests + cli-only ---"
)

# Markers from earlier patch generations — we want to overwrite all of these.
PRIOR_MARKERS = (
    "# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---",  # v2-v2
    "# --- laion v3 patch: tests_found gate ---",  # stack-php-large v3 misapplied
    "# --- laion exp_rpt_stack-php-v2 v3 patch: phpunit_xml + tests_found gate ---",  # v3
)

# The new test.sh body. Same shape as the sibling stack-php-large-v3 fix:
# explicit /tests/TestSolution.php + --test-suffix=Solution.php +
# --fail-on-empty-test-suite. The only diff is the dataset name in the
# logging line, and an extra bootstrap probe that prefers composer's
# vendor/autoload.php when the agent has run `composer dump-autoload`.
NEW_TEST_SH = """#!/bin/bash
# --- laion exp_rpt_stack-php-v2 v4 patch: tests-on-/tests + cli-only ---
# Verifier: gate reward on (a) PHPUnit exiting cleanly AND (b) PHPUnit
# reporting at least one test actually executed (and zero failures/errors).
#
# History:
#   v2 (upstream)   : trap-based scoring on `phpunit` exit. PHPUnit 10
#                     exits 0 on "No tests executed!", so any zero-exit
#                     invocation scored reward=1 → 100% rubber-stamp.
#   v2-v2 (broken)  : tried to gate via `--fail-on-no-tests`, which does
#                     NOT exist in PHPUnit 10.5.x → "Unknown option" at
#                     argument parsing → runner_rc=2 → reward=0 on every
#                     trial.
#   v3 (broken)     : generated /app/phpunit.xml at runtime with
#                     `<file>tests/TestSolution.php</file>` and `cd /app`
#                     → expanded to /app/tests/TestSolution.php, which
#                     does not exist. Harbor copies tests/ into the
#                     container at /tests/ (not /app/tests/), so the
#                     XML's relative path was wrong. 0/200 trials passed.
#   v4 (this file)  : drop the XML, use CLI flags only, name the test
#                     file at /tests/TestSolution.php absolute. Aligns
#                     with the sibling stack-php-large-v3 fix that uses
#                     the same Dockerfile + the same Harbor mount layout.

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

# Prefer composer's PSR-4 autoload (which actually maps
# Rodacker\\Sleddog\\... → /app/app/...) if the agent ran
# `composer dump-autoload`. Fall back to the Dockerfile-baked
# /app/autoload.php (naive <class>→/app/<class>.php mapper) so PHPUnit
# at least bootstraps — even if class resolution then fails, it'll be
# a deterministic test error rather than a missing-bootstrap silent skip.
if [ -f /app/vendor/autoload.php ]; then
    BOOTSTRAP=/app/vendor/autoload.php
else
    BOOTSTRAP=/app/autoload.php
fi

echo "Running PHPUnit tests..."
# Flags used (all PHPUnit-10.5-valid):
#   --bootstrap <file>           : load $BOOTSTRAP before discovery so the
#                                  test's `use Rodacker\\Sleddog\\...` lines
#                                  can resolve to /app/.
#   --fail-on-empty-test-suite   : real PHPUnit 10 flag; flips exit non-zero
#                                  if 0 tests were collected (replaces the
#                                  non-existent --fail-on-no-tests).
#   --fail-on-skipped            : belt-and-suspenders against skipped-only
#                                  suites.
#   --test-suffix=Solution.php   : our test class file is named
#                                  TestSolution.php; default suffix is
#                                  Test.php. Without this, PHPUnit treats
#                                  /tests/TestSolution.php as not-a-test
#                                  and --fail-on-empty-test-suite fires.
#   /tests/TestSolution.php      : absolute path. Harbor mounts tests/ at
#                                  /tests/, not /app/tests/.
phpunit \\
    --bootstrap "$BOOTSTRAP" \\
    --fail-on-empty-test-suite \\
    --fail-on-skipped \\
    --test-suffix=Solution.php \\
    /tests/TestSolution.php 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# PHPUnit 10 summary line shapes (most-common first):
#   "OK (3 tests, 5 assertions)"
#   "Tests: 3, Assertions: 5, Failures: 0, Errors: 0"
#   "No tests executed!"   (suppressed when --fail-on-empty-test-suite
#                           flips the exit, but we still parse defensively)
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

echo "exp_rpt_stack-php-v2 v4 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors bootstrap=$BOOTSTRAP"

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
    'patched_from_v3', 'patched_from_v2_v2', 'patched_from_v3_large',
    'patched_from_original', 'patched_unusual', 'already', 'missing',
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

    # Skip tasks whose test.sh doesn't actually invoke phpunit — they're not
    # PHPUnit tasks (or use some other harness) and we'd corrupt them by
    # replacing the file with our PHPUnit-specific gate.
    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    # Classify the prior generation so the summary can report what we're
    # overwriting (sanity / forensics).
    if PRIOR_MARKERS[2] in existing:
        source = "patched_from_v3"  # exp_rpt_stack-php-v2 v3 patch
    elif PRIOR_MARKERS[0] in existing:
        source = "patched_from_v2_v2"
    elif PRIOR_MARKERS[1] in existing:
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
    counts = {
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
