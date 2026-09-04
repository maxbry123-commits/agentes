#!/usr/bin/env python3
"""
Patch DCAgent/mix_h11_single_skill_only by dropping the 1,000 broken
stdin/stdout-style ``codenet-python`` tasks whose verifier loops over a
non-existent ``/tests/inputs/input_*.txt`` glob.

Background (200/200 QC pass on DCAgent/mix_h11_single_skill_only)
---------------------------------------------------------------
The published dataset advertises 200/200 infra-OK / 42 solves on a 200-task
sample (21.0% solve rate). The high infra-OK is misleading: 56/200 trials
(28.0%) report ``verifier_result.stdout = "\nResults: 0/0 passed\n"`` and
reward=0 regardless of the agent's actions. The triage maps perfectly to
source family:

  family                 trials   zero-zero   solved
  codenet-python             56       56         0   <- 100% broken
  crosscodeeval-python       34        0         3
  stack-pytest               31        0        11
  pymethods2test             23        0         7
  unitsyn-python             20        0         8
  e2egit                     17        0        10
  codereval-python           12        0         2
  exercism-python             5        0         1
  nemotron-pytest-synthetic   2        0         0

Across the full 3,873-task corpus, 1,000 tasks (25.8%) are
``codenet-python-*``. Every one of them ships with the same broken layout:

* ``tests/test.sh`` is a Bash loop::

      for input_file in /tests/inputs/input_*.txt; do
          ...
          actual_output=$(python3 /app/solution.py < "$input_file" ...)
          ...
      done
      echo "Results: $PASSED/$TOTAL passed"

* but **no** ``tests/inputs/`` or ``tests/outputs/`` directory exists. The
  loop body never executes; ``TOTAL`` stays 0; the
  ``[ $FAILED -eq 0 ] && [ $TOTAL -gt 0 ]`` gate fails; ``reward.txt``
  always ends up ``0``. Always zero, regardless of agent behavior.

* the upstream ``DCAgent/exp_rpt_codenet-python`` ships ``tests/inputs/``
  and ``tests/outputs/`` directories — but every input/output file in the
  upstream is **zero bytes**. ``metadata.json`` even records this:
  ``"num_tests": 0``. So we cannot rehydrate the missing fixtures from
  upstream the way ``patch_mix_h7_dedup_diverse_1k_tasks.py`` rehydrates
  ``bugsinpy_mf/solution.py`` — the upstream itself is empty.

All other source families (crosscodeeval-python, stack-pytest, unitsyn-python,
e2egit, pymethods2test, codereval-python, exercism-python,
nemotron-pytest-synthetic) ship a sibling ``tests/test_solution.py`` driven
by pytest and are kept untouched.

Why drop, not repair
--------------------
Repairing the 1,000 broken codenet tasks would require, per task:
  (a) hand-deriving N test cases from instruction.md (each codenet task is
      a competitive-programming-style prompt with at most a single inline
      example),
  (b) populating ``tests/inputs/input_0.txt`` and
      ``tests/outputs/output_0.txt`` (and ideally more for robustness),
  (c) trusting that the derived I/O actually exercises the algorithm
      (sampled tasks include open-ended problems where the example doesn't
      cover edge cases).

That's too much per-task risk for a v2 corpus, and the upstream provides
no fixture data we can rehydrate from. Dropping is the safe, deterministic
action — exactly as ``patch_mix_h8_adversarial_tests_tasks.py`` does for
the same defect mode on a sibling mix.

What this patcher does
----------------------
For each ``mix-h11-single-skill-*`` subdirectory under --root:
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
    python -m data.patchers.patch_mix_h11_single_skill_only_tasks \
        --root /tmp/mix_h11_single_skill_only_src \
        [--limit N] [--dry-run] [--dropped-out path/to/file.tsv]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# Unique-enough substring of the broken bash loop. Present in 1,000/1,000
# broken codenet-python tasks, absent in all 2,873 pytest-style tasks
# (verified by scanning the full 3,873-task tree of
# DCAgent/mix_h11_single_skill_only on 2026-05-15).
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
            "Patch DCAgent/mix_h11_single_skill_only (v2). Drops the "
            "1,000 broken codenet-python tasks whose verifier loops over "
            "a non-existent /tests/inputs glob."
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
