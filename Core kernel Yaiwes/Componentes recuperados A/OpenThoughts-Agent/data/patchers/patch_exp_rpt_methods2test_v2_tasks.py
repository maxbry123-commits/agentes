#!/usr/bin/env python3
"""
exp_rpt_methods2test-v2 patcher.

Bug (QC 2026-05-14):
  The v2 verifier (`tests/test.sh`) runs `mvn test -q` and uses the
  pipeline exit code as the only signal: any non-failure exit becomes
  reward=1. Maven Surefire happily reports a successful build when:
    - the agent ignores `/tests/TestSolution.java` entirely and writes
      its own tests in `/app/` (the verifier compiles the stub test
      class but finds 0 `@Test`-annotated methods → "Tests run: 0"),
    - the verifier short-circuits with empty stdout (still reward=1).

  QC evidence: 200 trials, only 4 reported reward=1. ALL 4 were vacuous:
    - methods2test-0134: Tests run: 0
    - methods2test-0135: empty stdout
    - methods2test-0137: empty stdout
    - methods2test-0357: empty stdout
  True solve rate = 0%, headline 2%.

  Test.sh is byte-identical (single md5) across all 500 task dirs and
  matches the methods2test-v3 layout exactly, so we reuse that fix.

Fix: Rewrite `tests/test.sh` so reward is gated on:
  - the runner exiting cleanly,
  - Surefire reporting at least one test run (`tests_run >= 1`),
  - zero failures and zero errors.

The patcher rewrites the whole file (uniform across the corpus).
Idempotency is enforced via the marker
  `# --- laion v2 patch: tests_found gate ---`
near the top of the new test.sh: if present, the file is left alone.

Usage:
  python data/patchers/patch_exp_rpt_methods2test_v2_tasks.py \\
    --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only `tests/test.sh` is touched. instruction.md, TestSolution.java,
    solution/, environment/Dockerfile, pom.xml are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
V2_MARKER = "# --- laion v2 patch: tests_found gate ---"

# New test.sh body. Same gating logic as patch_methods2test_v3_tasks.py.
NEW_TEST_SH = f"""#!/bin/bash
{V2_MARKER}
# Gate reward on (a) clean exit AND (b) Surefire reporting at least one
# test actually executed. The original test.sh scored reward=1 on any
# zero-exit `mvn test`, which let `Tests run: 0` outputs (agent wrote
# its own tests in /app/ and ignored /tests/TestSolution.java, etc.)
# pass. See QC 2026-05-14.

set +e  # we manage exit/reward explicitly; don't abort on first failure

mkdir -p /logs/verifier
# Reward floor: any abnormal exit below leaves this 0 in place.
echo "0" > /logs/verifier/reward.txt

cd /app

# Create Maven project structure if needed
mkdir -p src/main/java

# Copy pom.xml if not exists
if [ ! -f pom.xml ]; then
    cp /tests/pom.xml .
fi

echo "Compiling and running tests..."
mvn test -q 2>&1 | tee /logs/verifier/test_output.txt
runner_rc=${{PIPESTATUS[0]}}

# Parse the LAST Surefire summary line. Surefire emits
# "Tests run: N, Failures: F, Errors: E, Skipped: S" both per-class
# and as the aggregate "Results :" footer. We grab the last occurrence
# so we score the aggregate when present, and the only per-class line
# otherwise.
summary_line=$(grep -E 'Tests run: [0-9]+, Failures: [0-9]+, Errors: [0-9]+' \\
    /logs/verifier/test_output.txt | tail -1)

tests_run=$(echo "$summary_line" | grep -oE 'Tests run: [0-9]+' \\
    | grep -oE '[0-9]+' | head -1)
failures=$(echo "$summary_line" | grep -oE 'Failures: [0-9]+' \\
    | grep -oE '[0-9]+' | head -1)
errors=$(echo "$summary_line" | grep -oE 'Errors: [0-9]+' \\
    | grep -oE '[0-9]+' | head -1)

# Default to 0/0/0 if any field is missing (will fail the gate below,
# producing reward=0 — the safe direction).
tests_run=${{tests_run:-0}}
failures=${{failures:-0}}
errors=${{errors:-0}}

echo "v2 patch verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

if [ "$runner_rc" -eq 0 ] \\
        && [ "$tests_run" -ge 1 ] \\
        && [ "$failures" -eq 0 ] \\
        && [ "$errors" -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
    exit 0
else
    echo "0" > /logs/verifier/reward.txt
    if [ "$runner_rc" -ne 0 ]; then
        exit "$runner_rc"
    fi
    exit 1
fi
"""


def patch_one(test_sh: Path, dry_run: bool) -> str:
    """Patch a single tests/test.sh file. Returns one of:
    'patched', 'patched_unusual', 'already', 'missing', 'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if V2_MARKER in existing:
        return "already"

    # Sanity check: the original file contains `mvn test` and the EXIT trap.
    is_expected = ("mvn test" in existing) and ("trap cleanup EXIT" in existing)

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
        "unparseable": 0,
    }

    for i, td in enumerate(task_dirs, 1):
        test_sh = td / "tests" / "test.sh"
        result = patch_one(test_sh, dry_run=args.dry_run)
        counts[result] = counts.get(result, 0) + 1

        if i % 100 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] patched={counts['patched']} "
                f"patched_unusual={counts['patched_unusual']} "
                f"already={counts['already']} missing={counts['missing']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched={counts['patched']} "
        f"patched_unusual={counts['patched_unusual']} "
        f"already_patched={counts['already']} "
        f"missing={counts['missing']} "
        f"unparseable={counts['unparseable']} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
