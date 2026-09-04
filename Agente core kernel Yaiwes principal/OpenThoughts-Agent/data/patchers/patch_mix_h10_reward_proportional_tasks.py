#!/usr/bin/env python3
"""
Patch DCAgent/mix_h10_reward_proportional by dropping the entire
`codenet-python-*` subset (1000/3873 tasks, 25.8% of the mix).

Bug (200-trial QC pass 2026-05-15)
----------------------------------
Headline metrics reported "100% infra-ok, 29.5% solved", which is
misleading. Per-source breakdown across the 200 sampled trials:

    source                 total  solved  rew0_passed0  rew0_empty_std
    codenet-python            43       0             0              43   <-- 100% silent zero
    codereval-python          19       2            13               0
    crosscodeeval-python      30       5            25               0
    e2egit                    22      12             7               0
    exercism-python            6       0             6               0
    pymethods2test            31      17            13               0
    stack-pytest              28       0            28               0
    unitsyn-python            21      12             6               0

The `codenet-python` subset accounts for **all 43 trials** that returned
``reward=0`` with an **empty verifier stdout** -- a strong "silent zero"
signature that is distinct from the other subsets' "Passed 0 / N tests"
stdout.

Root cause
----------
Every `codenet-python` task ships this `tests/test.sh`::

    #!/bin/bash
    set -uo pipefail
    mkdir -p /logs/verifier
    TOTAL=0
    PASSED=0
    for test_file in /tests/test_*.py; do
        [ -f "$test_file" ] || continue
        TEST_COUNT=$(grep -c "def test_" "$test_file" 2>/dev/null || true)
        TOTAL=$((TOTAL + TEST_COUNT))
        RESULT=$(cd /app && python -m pytest "$test_file" -v --tb=no 2>&1 || true)
        FILE_PASSED=$(echo "$RESULT" | grep -c " PASSED" || true)
        PASSED=$((PASSED + FILE_PASSED))
    done
    if [ $TOTAL -eq 0 ]; then
        echo "0" > /logs/verifier/reward.txt
        exit 1
    fi
    REWARD=$(python3 -c "print(round($PASSED / $TOTAL, 4))")
    echo "$REWARD" > /logs/verifier/reward.txt
    echo "Passed $PASSED / $TOTAL tests (reward=$REWARD)"
    ...

...but the tar contents only have::

    instruction.md
    metadata.json
    task.toml
    environment/Dockerfile
    tests/test.sh

There are **no `tests/test_*.py` files**. The for-loop body never runs
(``[ -f "$test_file" ]`` is false because the glob expands literally),
``TOTAL`` stays 0, the `TOTAL=0` branch fires, the script writes "0"
to reward.txt and exits 1 **without printing anything** (no `echo` in
that branch). Harbor sees a valid `reward.txt` (so the trial is not
"infra-failed"), reads reward=0, and records `verifier_result.stdout = ""`.

This was verified against all 1000 codenet-python tasks in the mix:
**1000/1000 (100%) ship `tests/test.sh` with NO `tests/test_*.py` files.**
None of these tasks can ever score above 0, regardless of agent quality.

Recovery from upstream is NOT possible
--------------------------------------
The would-be upstream `DCAgent/exp_rpt_codenet-python` ships a different
(I/O-based) test.sh and empty `tests/inputs/input_0.txt` +
`tests/outputs/output_0.txt`. Across all 10000 upstream rows, **0** have
non-empty test inputs. So even restoring upstream's test.sh would just
move the silent-zero failure mode (now: empty-vs-empty `cmp` would
arbitrarily PASS or FAIL with no real signal). The codenet-python
subset is unrecoverable in this dataset and the only honest fix is
to remove it.

Fix
---
For every extracted task whose ``metadata.json.source`` starts with
``codenet-python-``, delete the entire task directory. The remaining
2873 tasks (e2egit, pymethods2test, stack-pytest, unitsyn-python,
crosscodeeval-python, codereval-python, exercism-python,
nemotron-pytest-synthetic) keep their verification pipeline intact
and ship to v2.

Other subset diagnoses (informational, not patched)
---------------------------------------------------
The 0-solve rates on `stack-pytest`, `exercism-python`, and partly
`crosscodeeval-python` are **not** verifier defects -- those tasks
DO ship `tests/test_*.py` and the verifier honestly prints
``Passed 0 / N tests``. The agents are failing because the test files
import from package layouts (e.g. ``from lambdata.wallet import
Wallet``, ``from tree_building import Record, BuildTree``) that the
instructions don't disclose. That is intrinsic task hardness, not a
patcher target. Leave them alone.

Idempotency
-----------
Re-running the patcher is safe: missing task directories are silently
counted as "already dropped". No marker file needed -- the absence of
the codenet-python source dir IS the marker.

Snapshot impact
---------------
Daytona snapshot caps are not affected. The codenet-python tasks all
share one trivial Dockerfile (``FROM python:3.10-slim ... RUN pip
install pytest``). Dropping them reduces the new-snapshot count by 0
(the same image is reused by other subsets) or 1 (if they were the
sole user of that image). Well under the 10/dataset and 60/org caps.

Usage
-----
    python -m data.patchers.patch_mix_h10_reward_proportional_tasks --root <dir>
    python -m data.patchers.patch_mix_h10_reward_proportional_tasks --root <dir> --dry-run
    python -m data.patchers.patch_mix_h10_reward_proportional_tasks --root <dir> --limit 5
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path


# Source prefix to drop. Any task whose metadata.json.source starts with
# this prefix is removed entirely.
DROP_SOURCE_PREFIX = "codenet-python-"


def _task_source(task_dir: Path) -> str | None:
    """Read metadata.json and return the `source` field, or None."""
    meta_path = task_dir / "metadata.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    src = meta.get("source")
    return src if isinstance(src, str) else None


def patch_task(task_dir: Path, dry_run: bool) -> dict:
    """Process a single task. Returns ``{"status": ..., "reason": ...}``."""
    source = _task_source(task_dir)
    if source is None:
        return {
            "status": "skipped_no_metadata",
            "reason": "missing/unreadable metadata.json",
        }

    if not source.startswith(DROP_SOURCE_PREFIX):
        return {"status": "skipped_other_source", "reason": f"source={source}"}

    if dry_run:
        return {"status": "would_drop", "reason": f"source={source}"}

    shutil.rmtree(task_dir, ignore_errors=False)
    return {"status": "dropped", "reason": f"source={source}"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Drop unrecoverable `codenet-python-*` tasks from an extracted "
            "DCAgent/mix_h10_reward_proportional task tree. The verifier "
            "test.sh for that subset references `tests/test_*.py` files "
            "that don't exist in the tarball, producing a silent reward=0 "
            "with empty stdout. There is no upstream that can restore the "
            "missing tests, so the only honest fix is to drop the subset."
        ),
    )
    p.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing extracted mix-h10-proportional-* task subdirectories.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Stop after scanning N task directories (0 = all).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be dropped; remove nothing.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"[patcher] --root not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    print(f"[patcher] Scanning {len(task_dirs)} task directories under {root}")
    if args.dry_run:
        print("[patcher] DRY RUN -- nothing will be removed")

    counts: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for i, td in enumerate(task_dirs, 1):
        result = patch_task(td, dry_run=args.dry_run)
        status = result["status"]
        counts[status] += 1
        examples.setdefault(status, td.name)
        if i % 500 == 0 or i == len(task_dirs):
            print(
                f"[{i}/{len(task_dirs)}] "
                f"dropped={counts['dropped']} "
                f"would_drop={counts['would_drop']} "
                f"skipped_other={counts['skipped_other_source']} "
                f"skipped_no_md={counts['skipped_no_metadata']}",
                flush=True,
            )

    print("\n[patcher] Result summary:")
    for status, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")
    print(f"\n[patcher] Root:    {root}")
    print(f"[patcher] Dry run: {args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
