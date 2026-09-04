#!/usr/bin/env python3
"""
exp_rpt_stack-rust v2 patcher.

Bug (v1 -> v2, found in QC 2026-05-14):
  Reported solve rate 21/200 (10.5%). 200/200 trials "infra-OK", but cargo
  test exits 0 in two distinct situations:

    (1) Real tests in tests/test_solution.rs compiled and passed (legitimate
        reward=1).
    (2) tests/test_solution.rs is present but contains zero `#[test]`
        functions, so cargo test reports:
            running 0 tests
            test result: ok. 0 passed; 0 failed; ...
        for BOTH the unit-test binary and the integration-test binary, and
        exits 0. v1 test.sh treats exit 0 as success -> reward=1.

  Confirmed in 2/21 (~10%) reward=1 trials from QC sample
  (stack-rust-5514, stack-rust-6572): no real tests, no real signal,
  rubber-stamped reward=1. The other 19 had real `running N tests` lines
  with N>=1 and `test result: ok` — those are real solves.

  Failed (reward=0) trials are unaffected: cargo compile errors / runtime
  failures all exit non-zero, which v1 already maps to reward=0 correctly.
  This patch tightens reward=1 only.

Fix (v2): Rewrite `tests/test.sh` so reward=1 requires ALL of:
  - cargo test exits 0,
  - the integration-test binary (tests/test_solution.rs target) actually
    ran at least one test (`running N tests` with N>=1 immediately followed
    by a `test result: ok. N passed; 0 failed; ...` line where N>=1, scoped
    to the `Running tests/test_solution.rs` section).

  Specifically, we PARSE the cargo test output and look for the section
  emitted after `Running tests/test_solution.rs (target/debug/deps/...)`.
  Inside that section we require both a `running N tests` line with N>=1
  and a `test result: ok. M passed; 0 failed; ...` line. If either is
  missing, reward = 0 regardless of exit code.

  We also keep the original `cargo init` + copy-test-file scaffolding
  untouched; only the scoring logic changes.

Layout (verified across all 9987 v2 task dirs — byte-identical test.sh
files, single MD5 1425d9c0630f68c00563009912a41dcd):
  tests/test.sh runs `cargo test` and scores reward via an EXIT trap on
  `$?`, which is the v1 bug. The new test.sh replaces the trap-based
  scoring with explicit gate parsing.

Idempotency is enforced via the marker
  `# --- laion v2 patch: cargo_tests_found gate ---`
near the top of the new test.sh: if present, the file is left alone.

If a task has no `tests/test.sh` or its existing test.sh has no `cargo
test` invocation, it is left untouched and counted as `skipped`.

Usage:
  python data/patchers/patch_exp_rpt_stack_rust_tasks.py \
    --root <dir> [--dry-run] [--limit N]

Constraints (per upload spec):
  - Only `tests/test.sh` is touched. instruction.md, test_solution.rs,
    environment/Dockerfile, task.toml, metadata.json are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Marker we drop into the new test.sh so re-runs are idempotent.
V2_MARKER = "# --- laion v2 patch: cargo_tests_found gate ---"

# The new test.sh body. We:
#   - drop the trap-based scoring (EXIT trap = the v1 bug; any zero
#     exit becomes reward=1, including cargo's "running 0 tests" output).
#   - keep the original cargo init + copy-test-file scaffolding.
#   - parse the cargo test output for a "Running tests/test_solution.rs"
#     section followed by a "running N tests" line (N>=1) AND a
#     "test result: ok. M passed; 0 failed; ..." line (M>=1) in that section.
#   - require runner_rc == 0 AND integration_tests_run >= 1 AND
#     integration_failures == 0 to score reward=1. Anything else = 0.
NEW_TEST_SH = """#!/bin/bash
# --- laion v2 patch: cargo_tests_found gate ---
# v2 verifier: gate reward on (a) clean cargo exit AND (b) the
# integration-test binary (tests/test_solution.rs) actually running >=1
# test. v1 scored reward=1 on any zero-exit `cargo test`, which let
# "running 0 tests" outputs (test files with no #[test] functions) pass
# with reward=1 (confirmed in 2/21 reward=1 trials in 2026-05-14 QC).

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

# Initialize cargo project if needed
if [ ! -f Cargo.toml ]; then
    cargo init --name solution
fi

# Copy test file to tests directory
mkdir -p tests
cp /tests/test_solution.rs tests/

echo "Running Rust tests..."
cargo test 2>&1 | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# Parse cargo test output for the integration-test binary section.
# Cargo prints sections like:
#   Running unittests src/main.rs (target/debug/deps/solution-...)
#   running 0 tests
#   test result: ok. 0 passed; 0 failed; ...
#   Running tests/test_solution.rs (target/debug/deps/test_solution-...)
#   running 3 tests
#   test tests::foo ... ok
#   test result: ok. 3 passed; 0 failed; ...
# We look ONLY at the tests/test_solution.rs section. The unit-test binary
# section is irrelevant — most agent solutions have no `#[cfg(test)]` mod,
# so "running 0 tests" there is expected and not a bug.
python3 - <<'PYEOF'
import re, sys, pathlib

p = pathlib.Path("/logs/verifier/test_output.txt")
if not p.exists():
    sys.exit(2)
text = p.read_text(errors="replace")

# Find the "Running tests/test_solution.rs ..." anchor; take everything
# after it up to the next "Running " line (next test binary) or EOF.
m = re.search(r"^[ \\t]*Running tests/test_solution\\.rs\\b.*$",
              text, flags=re.MULTILINE)
if not m:
    # Integration-test binary never ran (compile failure, etc.).
    pathlib.Path("/logs/verifier/_gate.txt").write_text("no-integration-binary\\n")
    sys.exit(1)

section = text[m.end():]
# Truncate at next test-binary section if any.
nxt = re.search(r"^[ \\t]*Running .*$", section, flags=re.MULTILINE)
if nxt:
    section = section[:nxt.start()]

# Require both:
#   "running N tests"        with N >= 1
#   "test result: ok. M passed; 0 failed"   with M >= 1
mn = re.search(r"^running\\s+(\\d+)\\s+tests?\\b", section, flags=re.MULTILINE)
mr = re.search(
    r"^test result:\\s*ok\\.\\s*(\\d+)\\s+passed;\\s*(\\d+)\\s+failed",
    section, flags=re.MULTILINE,
)

if not mn or not mr:
    pathlib.Path("/logs/verifier/_gate.txt").write_text("missing-result-lines\\n")
    sys.exit(1)

n_running = int(mn.group(1))
n_passed = int(mr.group(1))
n_failed = int(mr.group(2))

ok = (n_running >= 1) and (n_passed >= 1) and (n_failed == 0)
pathlib.Path("/logs/verifier/_gate.txt").write_text(
    f"running={n_running} passed={n_passed} failed={n_failed} ok={ok}\\n"
)
sys.exit(0 if ok else 1)
PYEOF
gate_rc=$?

echo "v2 verifier: runner_rc=$runner_rc gate_rc=$gate_rc"
if [ -f /logs/verifier/_gate.txt ]; then
    echo "v2 verifier gate: $(cat /logs/verifier/_gate.txt)"
fi

if [ "$runner_rc" -eq 0 ] && [ "$gate_rc" -eq 0 ]; then
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
    'skipped_no_cargo', 'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if V2_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke cargo test — they're
    # not Rust-cargo-test tasks (or use some other harness) and we'd corrupt
    # them by replacing the file with our cargo-specific gate.
    if "cargo test" not in existing.lower() and "cargo  test" not in existing.lower():
        return "skipped_no_cargo"

    # Sanity: the v1 file we expect contains `cargo test` and the EXIT trap.
    # If it doesn't, we still rewrite (our new file is self-contained and
    # correct for the documented uniform layout), but flag it.
    is_expected = ("cargo test" in existing) and ("trap cleanup EXIT" in existing)

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
        "skipped_no_cargo": 0,
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
                f"skipped_no_cargo={counts['skipped_no_cargo']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched={counts['patched']} "
        f"patched_unusual={counts['patched_unusual']} "
        f"already_patched={counts['already']} "
        f"missing={counts['missing']} "
        f"skipped_no_cargo={counts['skipped_no_cargo']} "
        f"unparseable={counts['unparseable']} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
