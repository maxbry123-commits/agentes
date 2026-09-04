#!/usr/bin/env python3
"""
mix_h10_reward_binary v2 patcher: drop unsolvable / rubber-stamp tasks.

QC findings (2026-05-15 first-time triage, 200-trial validation pass)
=====================================================================
Headline metrics looked healthy: 200/200 infra-OK, 49 solves (24.5%).
Hand-reading 10 trajectories surfaced two distinct verifier-side bugs that
mirror the defects previously found in ``mix_h8_original_tests`` (same
codenet stdin/stdout family + same pytest-skipif family).

1. **Missing-input tasks (1000/3873 = 25.8%) — silently unsolvable.**
   Every task whose ``metadata.source`` is ``codenet-python-*`` ships a
   ``tests/test.sh`` that loops over ``/tests/inputs/input_*.txt``, runs
   ``python3 /app/solution.py < $input_file``, diffs the stdout against
   ``/tests/outputs/output_N.txt``, and gates reward on
   ``FAILED -eq 0 AND TOTAL -gt 0``. The gate is correct, BUT the task
   tarballs contain only::

       [instruction.md, metadata.json, task.toml,
        environment/Dockerfile, tests/test.sh]

   — no ``tests/inputs/`` and no ``tests/outputs/`` directories. The for
   loop iterates zero times, TOTAL stays at 0, the ``TOTAL -gt 0`` guard
   fails, and reward is ALWAYS 0 regardless of agent output. In the 200-
   trial sample this surfaced as 43 distinct ``Results: 0/0 passed``
   verifier outputs. Verified across the full 3873-task corpus: every
   one of the 1000 ``codenet-python-*`` tasks has the same broken
   skeleton. Both upstream source datasets
   (``DCAgent/exp_rpt_codenet-python`` and
   ``laion/exp_rpt_codenet-python-v2``) also ship empty fixture files,
   so this is an upstream-wide defect — we cannot patch in fixtures from
   anywhere we have access to.

2. **All-skipif tasks (11/3873 = 0.3%) — silently always-pass.**
   These pytest-based tasks decorate every test with ``@pytest.mark.skipif``
   (or equivalent unconditional guards on env vars / external services
   that the sandbox never has). The verifier runs pytest, treats exit
   code 0 as success, then echoes "All tests passed!" → reward=1. pytest
   exits 0 when every test SKIPs, so the agent gets a free pass without
   writing any solution.

Decision: filter, don't patch
-----------------------------
- Missing-input codenet tasks can't be patched in-place — both upstream
  source datasets carry empty fixture files (verified 0/10000 populated
  in each). Any verifier rewrite would just turn a deterministic
  reward=0 into a deterministic reward=0.
- All-skipif tasks could in theory be patched by rewriting the verifier
  to require at least one non-skipped test, but the skipif conditions
  are baked into the test bodies (HDA credentials, etc.); fixing them
  would mean rewriting the test logic per task, out of scope.
- Both classes are pure noise for an RL signal: type 1 is always-fail,
  type 2 is always-pass. Dropping them is the cheapest correct fix.

Total dropped: 1011 (= 1000 codenet + 11 all-skipif). Remaining: 2862
healthy tasks (74.2% of the original corpus).

Sibling-dataset impact
----------------------
This defect class affects the same source slices in any mix-family
dataset that includes them:

- ``codenet-python-*`` slice → all 1000 tasks broken. Already-known
  bug also addressed by ``patch_mix_h8_original_tests_tasks.py`` and
  ``patch_mix_h8_adversarial_tests_tasks.py`` (which drop the same
  1000 codenet tasks). Confirmed empty fixtures in both
  ``DCAgent/exp_rpt_codenet-python`` and
  ``laion/exp_rpt_codenet-python-v2`` upstream sources.
- The ``@pytest.mark.skipif`` family is a smaller, dataset-specific
  noise pocket — also present in ``mix_h8_original_tests`` (11 tasks)
  and now ``mix_h10_reward_binary`` (11 tasks). Sibling mix datasets
  in the h* family that draw from the same skill registry likely have
  similar small counts; not investigated here.

Snapshot impact
---------------
Filtering only removes task dirs; it does not introduce new Dockerfile
variants. Daytona snapshot caps (max_new_snapshots=10,
max_org_snapshots=60) are not approached.

Patcher contract
----------------
Operates on an extracted task tree (one subdir per task with
``instruction.md`` marker). Removes broken task subdirs in place so the
downstream ``scripts.harbor.tasks_parquet_converter`` re-packs
only the surviving tasks into the new parquet.

Idempotent: detection re-runs cleanly because removal is the only
mutation — if a task dir is already gone, there's nothing to do. The
marker file ``.mix_h10_v2_patched`` is dropped at the root of the
remaining tasks tree on completion so a re-run can short-circuit.

Usage
-----
  python data/patchers/patch_mix_h10_reward_binary_tasks.py \
      --root /path/to/extracted/mix_h10_reward_binary \
      [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# Idempotency marker — written at --root once patcher completes.
PATCH_MARKER_FILE = ".mix_h10_v2_patched"

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
    # The diagnostic substring is the for-loop header that every codenet
    # bash-only task in this corpus shares.
    if "/tests/inputs/input_" not in sh:
        return False
    inputs_dir = task_dir / "tests" / "inputs"
    if not inputs_dir.is_dir():
        return True
    # Also catch the case where the dir exists but is empty / has only
    # zero-byte placeholders (this is what upstream codenet ships).
    populated = any(
        p.is_file() and p.stat().st_size > 0 and p.name.startswith("input_")
        for p in inputs_dir.iterdir()
    )
    return not populated


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
            "mix_h10_reward_binary v2 patch applied\n"
            f"kept={n_kept}\n"
            f"removed_missing_inputs={n_missing_inputs}\n"
            f"removed_all_skipif={n_all_skipif}\n"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
