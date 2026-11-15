#!/usr/bin/env python3
"""
exp_rpt_pr v2 patcher.

Bug (v1 -> v2, found in QC 2026-05-13):
  DCAgent/exp_rpt_pr reports 47/200 (23.5%) solve rate, but inspecting the
  47 "solves" shows 27/47 (57%) of them are pytest sessions where ALL
  collected tests are SKIPPED (`pytest.importorskip(...)` or
  `pytest.skip(...)` when the agent's implementation can't be imported /
  located). Sample evidence (verifier/test-stdout.txt):

      ============================== 4 skipped in 0.02s ===============
      ============================== 5 skipped in 0.02s ===============
      ============================== 6 skipped in 0.06s ===============

  pytest exits 0 on a zero-pass / all-skip run, and the v1 `tests/test.sh`
  uses a bash EXIT trap on $? -> reward=1 for any zero exit. Identical
  disease to stack-php-v3, methods2test-v3, and stack-junit-v3 from prior
  batch_qc rounds.

  True solve rate is 20/200 = 10%, not 23.5%. The 27 "rubber-stamp" passes
  poison the RL signal: the agent learns it can `pass`-out / no-op the
  implementation and still receive reward=1 as long as test_pr.py manages
  to `importorskip` every test.

Layout (verified across all 4793 task dirs in DCAgent/exp_rpt_pr's
tasks.parquet -- byte-identical test.sh files, single MD5
bb184b8eee487434ddadec109b9ffd6b):
  - tests/test.sh runs `pytest /tests/test_pr.py -v --tb=short`.
  - Reward is decided by an EXIT trap on $?, which is the v1 bug.
  - tests/test_pr.py is per-task and uses `pytest.importorskip(...)` /
    `pytest.skip(...)` heavily as its fallback when the implementation
    isn't present.

Fix (v2): Rewrite `tests/test.sh` so the reward is gated on:
  - the runner exiting cleanly (rc=0),
  - pytest reporting at least one test that actually PASSED (>= 1 passed),
  - zero failures and zero errors,
  - we DO NOT require zero skips (some test_pr.py modules legitimately
    skip e.g. an "OpenMP-only" check while still passing the core tests);
    requiring >= 1 passed alongside the runner_rc gate is sufficient to
    reject the "all-skipped" rubber stamps.

Implementation detail:
  We rely on pytest's machine-parsable -rN report line. The cleanest /
  most-portable signal across pytest 7/8/9 is the summary footer line,
  e.g.:
      ============== 5 passed in 0.17s ==============
      ============== 4 skipped in 0.02s ==============
      ============== 3 passed, 2 skipped in 0.10s ====
      ============== 1 failed, 4 passed in 0.30s =====
      ============== 1 error in 0.08s ================
  We grep that line and parse the integer counts of passed / failed /
  errors. As belt-and-suspenders we also pass --tb=short (already there)
  so a collection-time error still surfaces in stdout.

Idempotency: each test.sh is scanned for the marker
  `# --- laion v2 patch: pytest_passed_gate ---`
and skipped if already present.

Tasks without `tests/test.sh` are reported as `missing` and untouched.
Tasks whose existing test.sh has no `pytest` invocation are reported as
`skipped_no_pytest` and untouched (we wouldn't know how to gate them).

Usage::

    python -m data.patchers.patch_exp_rpt_pr_tasks --root /tmp/exp_rpt_pr_src

    # Dry run (count only)
    python -m data.patchers.patch_exp_rpt_pr_tasks --root /tmp/exp_rpt_pr_src --dry-run

    # Process only the first 20 tasks
    python -m data.patchers.patch_exp_rpt_pr_tasks --root /tmp/exp_rpt_pr_src --limit 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
V2_MARKER = "# --- laion v2 patch: pytest_passed_gate ---"

# The new test.sh body. We:
#   - keep PYTHONPATH=/app:... so the agent's /app/ implementation is
#     importable (matches the v1 behavior),
#   - run pytest exactly as v1 did,
#   - drop the trap-based EXIT scoring (any zero exit -> reward=1, the
#     v1 bug that let all-skipped sessions pass),
#   - parse pytest's summary footer line for passed / failed / error
#     counts,
#   - require runner_rc == 0 AND passed >= 1 AND failed == 0 AND
#     errors == 0 to score reward=1. Anything else (incl. all-skipped) = 0.
NEW_TEST_SH = """#!/bin/bash
# --- laion v2 patch: pytest_passed_gate ---
# v2 verifier: gate reward on (a) clean pytest exit, (b) at least one
# test actually PASSED, (c) zero failures and zero errors. v1 scored
# reward=1 on any zero-exit pytest, which let all-skipped sessions
# (pytest.importorskip / pytest.skip fallbacks when the agent's
# implementation is missing) pass with 27/47 of "solves" in 2026-05-13 QC.

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt

cd /app
export PYTHONPATH="/app:${PYTHONPATH:-}"

echo "Running tests..."
pytest /tests/test_pr.py -v --tb=short 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# Pytest summary-footer shapes we accept:
#   ============== 5 passed in 0.17s ==============
#   ============== 3 passed, 2 skipped in 0.10s ====
#   ============== 4 skipped in 0.02s ==============
#   ============== 1 failed, 4 passed in 0.30s =====
#   ============== 1 error in 0.08s ================
# Grab the LAST line bracketed by '=' that contains 'in <time>s' so we
# don't get tripped up by intermediate dividers.
summary=$(grep -E '^=+ .* in [0-9]+\\.[0-9]+s' /logs/verifier/test_output.txt | tail -1)

extract_count() {
    # $1 = label (passed|failed|error|errors|skipped)
    # echo 0 if not present; otherwise the integer just before the label.
    echo "$summary" \\
        | grep -oE "[0-9]+ $1" \\
        | head -1 \\
        | grep -oE '[0-9]+' \\
        | head -1
}

passed=$(extract_count passed)
failed=$(extract_count failed)
# pytest prints "1 error" (singular, collection-time) or "N errors".
errors_s=$(extract_count error)
errors_p=$(extract_count errors)
passed=${passed:-0}
failed=${failed:-0}
errors_s=${errors_s:-0}
errors_p=${errors_p:-0}
errors=$(( errors_s > errors_p ? errors_s : errors_p ))

echo "v2 verifier: runner_rc=$runner_rc passed=$passed failed=$failed errors=$errors"
echo "v2 verifier: summary=$summary"

if [ "$runner_rc" -eq 0 ] \\
        && [ "$passed" -ge 1 ] \\
        && [ "$failed" -eq 0 ] \\
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
    'skipped_no_pytest', 'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if V2_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke pytest -- we'd
    # corrupt them by replacing the file with our pytest-specific gate.
    if "pytest" not in existing.lower():
        return "skipped_no_pytest"

    # Sanity: the v1 file we expect contains `pytest /tests/test_pr.py`
    # and `trap cleanup EXIT`. If both, mark patched; otherwise still
    # rewrite (the new test.sh is self-contained) but flag as unusual
    # so we can investigate any variants.
    is_expected = ("pytest /tests/test_pr.py" in existing) and (
        "trap cleanup EXIT" in existing
    )

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
    return "patched" if is_expected else "patched_unusual"


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Patch DCAgent/exp_rpt_pr task tests/test.sh files to require at "
            "least one actually-PASSED test for reward=1 (rejects rubber-stamp "
            "all-skipped sessions)."
        ),
    )
    p.add_argument(
        "--root",
        required=True,
        help="Path to extracted tasks root (directory of pr-NNNN/ dirs).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change; write nothing.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Stop after processing N tasks (default: all).",
    )
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
        "patched": 0,
        "patched_unusual": 0,
        "already": 0,
        "missing": 0,
        "skipped_no_pytest": 0,
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
                f"skipped_no_pytest={counts['skipped_no_pytest']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched={counts['patched']} "
        f"patched_unusual={counts['patched_unusual']} "
        f"already_patched={counts['already']} "
        f"missing={counts['missing']} "
        f"skipped_no_pytest={counts['skipped_no_pytest']} "
        f"unparseable={counts['unparseable']} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
