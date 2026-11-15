#!/usr/bin/env python3
"""
exp_rpt_stack-php-large v3 patcher.

Bug (v2 → v3, found in QC 2026-05-13):
  The dataset reports 100% solve rate but every single trial produces:

      Running PHPUnit tests...
      PHPUnit 10.5.63 by Sebastian Bergmann and contributors.
      Runtime:       PHP 8.2.30
      Configuration: /app/phpunit.xml

      No tests executed!

  PHPUnit 10 exits 0 on a zero-test run; the v2 `tests/test.sh` treats
  exit 0 as success → reward=1. Same disease as the
  `methods2test-v2 → v3` and `stack-junit-v2 → v3` fixes from prior
  batch_qc rounds. Agent's PHP solutions are non-trivial real code —
  they're just never tested.

Fix (v3): Rewrite `tests/test.sh` so the reward is gated on:
  - the runner exiting cleanly,
  - PHPUnit reporting at least one test actually executed
    (`--fail-on-no-tests` + parsing the "OK (N tests, ...)" /
    "Tests: N, Assertions: ..." summary line for N >= 1),
  - zero failures and zero errors.

Layout (verified across all 5000 v2 task dirs — byte-identical
test.sh files, single MD5 e18c9c6563080a53516460052f32cd78):
  - Single test.sh template that generates /app/phpunit.xml on the fly
    and runs `phpunit --configuration /app/phpunit.xml`.
  - Reward is decided by an EXIT trap on `$?`, which is the v2 bug
    (any zero exit = pass, including "No tests executed!").

The new test.sh replaces the trap-based scoring with explicit
runner_rc / tests_run / failures / errors gates and writes reward.txt
deterministically. Idempotency is enforced via the marker
  `# --- laion v3 patch: tests_found gate ---`
near the top of the new test.sh: if present, the file is left alone.

If a task has no `tests/test.sh` or its existing test.sh has no
`phpunit` invocation (i.e. it's not a PHPUnit task), it is left
untouched and counted as `skipped`.

Usage:
  python data/patchers/patch_stack_php_v3_tasks.py --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only `tests/test.sh` is touched. instruction.md, TestSolution.php,
    environment/Dockerfile, etc. are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
V3_MARKER = "# --- laion v3 patch: tests_found gate ---"

# The new test.sh body. We:
#   - drop the trap-based scoring (EXIT trap = the v2 bug; any zero
#     exit becomes reward=1, including PHPUnit's "No tests executed!").
#   - add `--fail-on-no-tests` so PHPUnit 10 returns non-zero when it
#     collects zero tests.
#   - add `--fail-on-skipped` as belt-and-suspenders against
#     skipped-only suites.
#   - parse the final summary line (`OK (N tests, A assertions)` or
#     `Tests: N, Assertions: A, Failures: F, Errors: E`) so we have a
#     numeric tests_run / failures / errors signal independent of the
#     exit code.
#   - require runner_rc == 0 AND tests_run >= 1 AND failures == 0 AND
#     errors == 0 to score reward=1. Anything else = 0.
NEW_TEST_SH = """#!/bin/bash
# --- laion v3 patch: tests_found gate ---
# v3 verifier: gate reward on (a) clean exit AND (b) PHPUnit reporting
# at least one test actually executed. v2 scored reward=1 on any
# zero-exit `phpunit` invocation, which let `No tests executed!`
# outputs pass with 100% (200/200 in 2026-05-13 QC).

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

echo "Running PHPUnit tests..."
# --fail-on-no-tests flips exit non-zero if 0 tests collected (PHPUnit 10).
# --fail-on-skipped optional belt-and-suspenders against skipped-only suites.
phpunit --fail-on-no-tests --fail-on-skipped 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# PHPUnit 10 summary line shapes:
#   "OK (3 tests, 5 assertions)"
#   "Tests: 3, Assertions: 5, Failures: 0, Errors: 0"
#   "No tests executed!"
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

echo "v3 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

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
    if V3_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke phpunit — they're
    # not PHPUnit tasks (or use some other harness) and we'd corrupt them
    # by replacing the file with our PHPUnit-specific gate.
    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    # Sanity: the v2 file we expect contains `phpunit --configuration`
    # and the EXIT trap. If it doesn't, we still rewrite (our new file
    # is self-contained and correct for the documented uniform layout),
    # but flag it so we can report any unexpected variants.
    is_expected = ("phpunit" in existing) and ("trap cleanup EXIT" in existing)

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
