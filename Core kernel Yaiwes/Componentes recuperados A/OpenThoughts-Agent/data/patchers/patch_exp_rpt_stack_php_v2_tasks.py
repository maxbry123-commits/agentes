#!/usr/bin/env python3
"""
exp_rpt_stack-php-v2 patcher (sibling dataset to stack-php-large-v2).

Observed failure mode (QC 2026-05-13, batch_qc local-Mac runner):
  0/200 trials reached the verifier — every trial died at sandbox
  creation with:

      DaytonaError: Failed to create sandbox: Cannot connect to host
      app.daytona.io:443 ssl:default
      [nodename nor servname provided, or not known]

  i.e. the QC runner couldn't resolve `app.daytona.io` (DNS / network
  outage on the QC host). The Dockerfile was NEVER built; the
  verifier (`tests/test.sh`) was NEVER executed. So the 0/200
  infra_ok score is NOT a defect in the task tarballs — it's a
  transient network failure on the QC host that no patch to the
  task data can fix.

Why we still ship a patcher:
  Across all 200 failure dirs in this QC bundle, both
  `tests/test.sh` (MD5 e18c9c6563080a53516460052f32cd78) and
  `environment/Dockerfile` (MD5 1d161fff6accc1b6cc97087ac3bcf277)
  are byte-identical to the stack-php-large-v2 layout that was
  already fixed via `patch_stack_php_v3_tasks.py`. That sibling
  dataset's v2 `test.sh` has the SAME upstream "No tests executed!"
  rubber-stamp bug: PHPUnit 10 exits 0 on a zero-test run and the
  v2 EXIT trap scores reward=1 on any zero-exit. Once Daytona
  connectivity is restored and re-QC runs the trials, this dataset
  will hit exactly that bug.

  So this patcher applies the same gating fix as the sibling
  patcher (different marker, different repo target). Re-QC after
  this patch should show genuine infra+solve rates instead of
  either (a) 0/200 from the DNS outage or (b) 200/200 rubber-stamps
  if Daytona comes back without the patch.

Fix: Rewrite `tests/test.sh` so the reward is gated on:
  - the runner exiting cleanly,
  - PHPUnit reporting at least one test actually executed
    (`--fail-on-no-tests` + parsing the "OK (N tests, ...)" /
    "Tests: N, Assertions: ..." summary line for N >= 1),
  - zero failures and zero errors.

The new test.sh replaces the trap-based scoring with explicit
runner_rc / tests_run / failures / errors gates and writes
reward.txt deterministically. Idempotency is enforced via the
marker
  `# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---`
near the top of the new test.sh: if present, the file is left alone.

If a task has no `tests/test.sh` or its existing test.sh has no
`phpunit` invocation (i.e. it's not a PHPUnit task), it is left
untouched and counted as `skipped_no_phpunit`.

Usage:
  python data/patchers/patch_exp_rpt_stack_php_v2_tasks.py \
      --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only `tests/test.sh` is touched. instruction.md, TestSolution.php,
    environment/Dockerfile, etc. are preserved verbatim.
  - Distinct marker from the sibling `patch_stack_php_v3_tasks.py`
    so re-running either patcher on the wrong tree leaves a
    different-but-still-idempotent fingerprint.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
# Distinct from the sibling patch_stack_php_v3_tasks.py marker so we
# can tell at a glance which patcher produced a given test.sh.
PATCH_MARKER = "# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---"

# The new test.sh body. Equivalent in intent to the sibling
# stack-php-v3 fix: replace trap-based scoring with an explicit
# runner_rc / tests_run / failures / errors gate.
NEW_TEST_SH = """#!/bin/bash
# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---
# Verifier: gate reward on (a) clean PHPUnit exit AND (b) PHPUnit
# reporting at least one test actually executed. The v2 layout
# scored reward=1 on any zero-exit `phpunit` invocation, which lets
# `No tests executed!` (PHPUnit 10 default) pass as 100%. Once
# Daytona connectivity is restored on the QC runner, this gate
# stops that rubber-stamp from showing up as a solve.

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

echo "exp_rpt_stack-php-v2 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

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
