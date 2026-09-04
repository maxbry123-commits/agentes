#!/usr/bin/env python3
"""
Patch DCAgent/mix_h8_adversarial_tests by dropping the ~1000 broken
stdin/stdout-style tasks whose verifier loops over a non-existent
``/tests/inputs/input_*.txt`` glob.

Background (200/200 QC pass)
----------------------------
The published dataset advertises 200/200 infra-OK / 25 solves on a 200-task
sample. The high infra-OK is misleading: 55/200 trials (27.5%) report
verifier_result.stdout = "\nResults: 0/0 passed\n" and reward=0 regardless of
the agent's actions. Across the full 3,873-task tree, **1,000 tasks** (26%)
ship with this broken layout:

* ``tests/test.sh`` is a Bash loop:

    for input_file in /tests/inputs/input_*.txt; do
        ...
        actual_output=$(python3 /app/solution.py < "$input_file" ...)
        ...
    done
    echo "Results: $PASSED/$TOTAL passed"

* but **no** ``tests/inputs/`` or ``tests/outputs/`` directory exists. The
  loop body never executes; ``TOTAL`` stays 0; the ``$FAILED -eq 0 && $TOTAL
  -gt 0`` gate fails; ``echo "0" > reward.txt``. Always zero.

* a sibling ``tests/test_adversarial.py`` *does* exist with adversarial
  pytest cases, but it is dead code from the verifier's perspective and
  furthermore is syntactically incomplete on 999/1000 broken tasks (no
  ``import pytest``, no ``from solution import ...``) so it could not be
  swapped in without per-task repairs.

The remaining ~2,873 tasks use a working pytest verifier
(``pytest /tests/test_solution.py``) and are kept.

Why drop, not repair
--------------------
Repairing the broken tasks would require, per task:
  (a) deriving the agent-facing function signature from
      instruction.md (parsed from natural language — fragile),
  (b) writing the correct ``from <module> import <fn>`` line,
  (c) adding ``import pytest``,
  (d) replacing ``test.sh`` with a pytest invocation,
  (e) hoping the adversarial cases in ``test_adversarial.py`` actually
      reflect the problem statement (sampled cases included tests that
      assert ``is_odd_product`` raises TypeError on string input — but
      the *instruction* says A and B are integers, so the adversarial
      contract is invented post-hoc).

That's too much per-task risk for a v2 corpus. Dropping is the safe,
deterministic action.

What this patcher does
----------------------
For each ``mix-h8-adversarial-*`` subdirectory under --root:
  * If ``tests/test.sh`` exists AND contains the unique broken-loop marker
    string ``input_file in /tests/inputs``, the task directory is removed
    (idempotent — second runs are no-ops because the dir is gone).
  * Otherwise the task is left untouched (it's a pytest-style task).

Idempotency
-----------
This patcher uses no in-place markers because its only action is deletion.
A second run on an already-patched tree simply observes that the broken
tasks no longer exist and reports them in the ``already_dropped`` bucket.

Output schema (per-task)
------------------------
  * ``ok_kept``               — pytest-style task, left alone
  * ``dropped_stdin_broken``  — stdin-style task with no inputs/, deleted
  * ``error_no_tests_dir``    — task is missing ``tests/`` entirely
  * ``error_no_test_sh``      — task has tests/ but no test.sh

Usage
-----
    python -m data.patchers.patch_mix_h8_adversarial_tests_tasks \
        --root /tmp/mix_h8_adversarial_src \
        [--limit N] [--dry-run] [--dropped-out path/to/file.tsv]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# Unique-enough substring of the broken bash loop. Present in 1000/1000
# broken tasks, absent in all 2,873 pytest-style tasks (verified by hand
# on a 200-task QC sample and by grep across the full 3,873-task tree).
BROKEN_TEST_SH_MARKER = "input_file in /tests/inputs"


def classify_task(task_dir: Path) -> str:
    """Return a status string for ``task_dir`` without modifying disk."""
    tests_dir = task_dir / "tests"
    if not tests_dir.is_dir():
        return "error_no_tests_dir"
    test_sh = tests_dir / "test.sh"
    if not test_sh.is_file():
        return "error_no_test_sh"
    try:
        text = test_sh.read_text()
    except (OSError, UnicodeDecodeError):
        return "error_no_test_sh"
    if BROKEN_TEST_SH_MARKER in text:
        return "dropped_stdin_broken"
    return "ok_kept"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Patch DCAgent/mix_h8_adversarial_tests (v2). Drops the "
            "1,000 broken stdin/stdout-style tasks whose verifier loops "
            "over a non-existent /tests/inputs glob."
        ),
    )
    p.add_argument(
        "--root",
        required=True,
        help="Tasks dir (one subdir per task, e.g. extracted parquet output)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify only; do not delete anything",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N tasks (0 = all). Useful for smoke tests.",
    )
    p.add_argument(
        "--dropped-out",
        default=None,
        help="Optional TSV path: writes one `<task_name>\\t<status>` line per non-kept task.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts: dict[str, int] = {
        "ok_kept": 0,
        "dropped_stdin_broken": 0,
        "error_no_tests_dir": 0,
        "error_no_test_sh": 0,
    }
    dropped_log: list[str] = []

    for i, td in enumerate(task_dirs, 1):
        status = classify_task(td)
        counts[status] = counts.get(status, 0) + 1
        if status != "ok_kept":
            dropped_log.append(f"{td.name}\t{status}")
        if status == "dropped_stdin_broken" and not args.dry_run:
            shutil.rmtree(td)
        if i % 500 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] "
                f"kept={counts['ok_kept']} "
                f"dropped_stdin_broken={counts['dropped_stdin_broken']} "
                f"error_no_tests_dir={counts['error_no_tests_dir']} "
                f"error_no_test_sh={counts['error_no_test_sh']}",
                flush=True,
            )

    print(
        "\nDone. "
        f"kept={counts['ok_kept']}/{n_total}, "
        f"dropped_stdin_broken={counts['dropped_stdin_broken']}, "
        f"error_no_tests_dir={counts['error_no_tests_dir']}, "
        f"error_no_test_sh={counts['error_no_test_sh']}, "
        f"dry_run={args.dry_run}"
    )

    if args.dropped_out and dropped_log:
        Path(args.dropped_out).write_text("\n".join(dropped_log) + "\n")
        print(f"Wrote dropped/error list to {args.dropped_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
