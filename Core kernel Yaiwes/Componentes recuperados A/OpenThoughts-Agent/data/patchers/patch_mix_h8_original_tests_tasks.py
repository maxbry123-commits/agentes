#!/usr/bin/env python3
"""
mix_h8_original_tests v2 patcher: drop unsolvable / rubber-stamp tasks.

QC findings (2026-05-14 200-trial validation pass with gpt-5-nano @ 1 turn)
=========================================================================
Headline metrics looked healthy: 200/200 infra-OK, 51 solves (25.5%).
Hand-reading 20 trajectories surfaced two distinct verifier-side bugs:

1. **Missing-input tasks (1000/3873 = 26%) — silently unsolvable.**
   The bash test.sh in these tasks loops over `/tests/inputs/input_*.txt`,
   diffs the agent's `/app/solution.py` stdout against
   `/tests/outputs/output_N.txt`, and gates reward on
   `FAILED -eq 0 AND TOTAL -gt 0`. The gate is correct, BUT the task
   tarballs ship only `tests/test.sh` — no `tests/inputs/` and no
   `tests/outputs/` directories. The for loop iterates zero times,
   TOTAL stays at 0, the `TOTAL -gt 0` guard fails, and reward is
   ALWAYS 0 regardless of agent output. Confirmed across 55/149
   "0/0 passed" failures in the 200-trial sample and verified by
   listing every tarball: every one of the 1000 bash-only tasks has
   the same skeleton `[instruction.md, metadata.json, task.toml,
   environment/Dockerfile, tests/test.sh]` — no I/O fixtures.

2. **All-skipif tasks (11/3873 = 0.3%) — silently always-pass.**
   These pytest-based tasks decorate every test with
   `@pytest.mark.skipif(NO_HDARC, ...)` (or equivalent unconditional
   guards on env vars / external services that the sandbox never has).
   The verifier (`tests/test.sh`) runs `pytest -v`, treats exit code 0
   as success, then echoes "All tests passed!" → reward=1. pytest exits
   0 when every test SKIPs, so the agent gets a free pass without
   writing any solution. Confirmed via 2/51 "passes" in the sample
   (0284, 2988) both showing only `SKIPPED (No access to HDA)` lines
   in test-stdout.txt with reward=1.

Decision: filter, don't patch
-----------------------------
- Missing-input tasks can't be patched in-place — we don't have the
  reference inputs/outputs anywhere in the task tarball or upstream
  source, so any verifier rewrite would just turn a deterministic
  reward=0 into a deterministic reward=0.
- All-skipif tasks could be patched by rewriting the verifier to
  require at least one non-skipped test, but the skipif conditions
  themselves are baked into the test bodies (HDA credentials, etc.);
  fixing them would mean rewriting the test logic per task, which is
  out of scope.
- Both classes of task are pure noise for an RL signal: type 1 is
  always-fail (no learning signal from agent quality), type 2 is
  always-pass (no learning signal at all). Dropping them is the
  cheapest correct fix.

Total dropped: 1011 (= 1000 + 11). Remaining: 2862 healthy tasks.

Snapshot impact: only 4 unique environment/Dockerfile hashes across
the full 3873-task corpus, so filtering does not approach the
Daytona caps (max_new_snapshots=10, max_org_snapshots=60).

Patcher contract
----------------
Operates on an extracted task tree (one subdir per task with
`instruction.md` marker). Removes broken task subdirs in place so the
downstream `scripts.harbor.tasks_parquet_converter` re-packs
only the surviving tasks into the new parquet.

Idempotent: detection re-runs cleanly because removal is the only
mutation — if a task dir is already gone, there's nothing to do. The
marker file `.mix_h8_v2_patched` is dropped at the root of the
remaining tasks tree on completion so a re-run can short-circuit.

Usage
-----
  python data/patchers/patch_mix_h8_original_tests_tasks.py \
      --root /path/to/extracted/mix_h8_original_tests \
      [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# Idempotency marker — written at --root once patcher completes.
PATCH_MARKER_FILE = ".mix_h8_v2_patched"

# Skip decorators that gate ALL tests are treated as "always-pass" indicators.
SKIPIF_RE = re.compile(
    r"@\s*(?:pytest\.mark\.skipif|pytest\.mark\.skip\b|unittest\.skip\b)"
)
TEST_DEF_RE = re.compile(r"^\s*def\s+(test_\w+)", re.MULTILINE)


def is_missing_inputs_task(task_dir: Path) -> bool:
    """True if test.sh expects /tests/inputs/* but no such fixtures ship."""
    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.is_file():
        return False
    sh = test_sh.read_text(errors="replace")
    # The diagnostic substring is the for-loop header that every bash-only
    # task in this corpus shares. If the verifier reads from /tests/inputs/
    # and there is no inputs/ subdir shipped, the loop iterates zero times.
    if "/tests/inputs/input_" not in sh:
        return False
    inputs_dir = task_dir / "tests" / "inputs"
    return not inputs_dir.is_dir()


def is_all_skipif_task(task_dir: Path) -> bool:
    """True if every test in tests/*.py is gated by an unconditional skip."""
    tests_dir = task_dir / "tests"
    if not tests_dir.is_dir():
        return False
    py_files = [p for p in tests_dir.glob("*.py") if p.is_file()]
    if not py_files:
        return False
    total_tests = 0
    total_skips = 0
    for p in py_files:
        text = p.read_text(errors="replace")
        n_tests = len(TEST_DEF_RE.findall(text))
        n_skips = len(SKIPIF_RE.findall(text))
        total_tests += n_tests
        total_skips += n_skips
    # If there are no test functions at all this isn't a pytest task;
    # treat that as not-skipif (a different bug, not in this patcher's
    # scope).
    if total_tests == 0:
        return False
    return total_skips >= total_tests


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument(
        "--root",
        required=True,
        help="Directory containing extracted task subdirs (each has instruction.md).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed without deleting.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Inspect at most N task dirs (0 = all). Inspection order is sorted.",
    )
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    marker_path = root / PATCH_MARKER_FILE
    if marker_path.exists() and not args.dry_run:
        print(f"[idempotent] Marker found at {marker_path}; nothing to do.")
        return 0

    task_dirs = sorted(
        d for d in root.iterdir() if d.is_dir() and (d / "instruction.md").is_file()
    )
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    n_missing_inputs = 0
    n_all_skipif = 0
    n_kept = 0
    sample_removed: list[str] = []

    for i, td in enumerate(task_dirs, 1):
        drop_reason: str | None = None
        if is_missing_inputs_task(td):
            drop_reason = "missing-inputs"
            n_missing_inputs += 1
        elif is_all_skipif_task(td):
            drop_reason = "all-skipif"
            n_all_skipif += 1
        else:
            n_kept += 1

        if drop_reason is not None:
            if len(sample_removed) < 10:
                sample_removed.append(f"{td.name} ({drop_reason})")
            if not args.dry_run:
                shutil.rmtree(td)

        if i % 500 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] kept={n_kept} missing_inputs={n_missing_inputs} "
                f"all_skipif={n_all_skipif}",
                flush=True,
            )

    print()
    print(
        f"Summary: total={n_total} kept={n_kept} "
        f"removed_missing_inputs={n_missing_inputs} "
        f"removed_all_skipif={n_all_skipif} dry_run={args.dry_run}"
    )
    if sample_removed:
        print("Sample removed:")
        for s in sample_removed:
            print(f"  - {s}")

    if not args.dry_run:
        marker_path.write_text(
            "mix_h8_original_tests v2 patch applied\n"
            f"kept={n_kept}\n"
            f"removed_missing_inputs={n_missing_inputs}\n"
            f"removed_all_skipif={n_all_skipif}\n"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
