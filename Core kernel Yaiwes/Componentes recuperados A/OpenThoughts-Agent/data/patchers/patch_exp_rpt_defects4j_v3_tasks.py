#!/usr/bin/env python3
"""
exp_rpt_defects4j v3 -> v2 patcher (uploaded as `laion/exp_rpt_defects4j-v3-v2`).

Bug (found in QC 2026-05-14):
  Headline solve rate is 9/200 (4.5%) on `DCAgent/exp_rpt_defects4j-v3` with
  infra_rate=1.000. The 4.5% pass rate looks low but plausible; the dataset
  hides two compounding defects that together poison both the prompt set
  AND the verifier:

  Defect 1 (poisoned prompts):
    160 of 464 (34.5%) task dirs in the source parquet ship with
    `instruction.md` of byte-length 0. The Harbor terminus-2 prompt template
    fills in the field unconditionally, so the agent receives literally:

        Task Description:


        Current terminal state:
        ...

    i.e. zero guidance. Empirically across QC (10 trials, 200 total):
      - 74 of the 200 sampled trials hit this empty-instruction path.
      - 7 of the 9 reported "solves" came from empty-instruction tasks.

  Defect 2 (rubber-stamp verifier):
    `tests/test.sh` is byte-identical across all 464 tasks (MD5
    3ec2eb617c870ac370507c0fac024b1d). It contains:

        cd /app
        if [ ! -f /app/Solution.java ]; then
            cp /tests/initial/Solution.java /app/Solution.java
        fi
        javac ... ; java -jar junit ...
        # via `trap cleanup EXIT`: reward = (final $? == 0)

    The fallback `cp` is the rubber-stamp. The agent gets dropped into a
    `/app/` whose ONLY contents are an empty `classes/` dir — no
    `Solution.java`, no instruction text, no README. When the agent does
    nothing (which is the only sensible outcome when the instruction is
    blank), test.sh silently swaps in the BUGGY initial Solution.java from
    `/tests/initial/Solution.java`, compiles it, and runs JUnit. For some
    Defects4J bugs (Compress-35 = defects4j-0000 is one example), the
    buggy version happens to pass all four JUnit tests that ship with the
    task — so the agent gets reward=1 for doing literally nothing. The
    other "buggy-but-passes-tests" cases similarly become free solves.

  Combined evidence (verified across all 9 reward=1 trials in the v3 QC
  export at /Users/benjaminfeuer/Documents/agent-traces-analysis/
  DCAgent__exp_rpt_defects4j-v3/traces):
    - 7/9 reward=1 trials had EMPTY instruction.md AND no Solution.java
      in /app at agent-run time (the agent's `ls -la /app` shows just
      `classes/`).
    - 2/9 reward=1 trials had a real instruction AND the agent attempted a
      fix; we cannot distinguish a real solve from a rubber-stamp on those
      from the trial export alone — but the defect-2 fallback would have
      also produced reward=1 if the agent had bailed, so they are
      *consistent* with rubber-stamping.
    - All 191 reward=0 trials we inspected at the test-stdout level showed
      real Java compile errors from the agent's (broken) edits or from
      the buggy initial copied in by test.sh — i.e. the failure mode is
      genuine, not infra. So the 4.5% headline reflects real agent failure
      ON TOP of a verifier that systematically grades the *buggy* initial
      whenever the agent does nothing.

Fix (uploaded as v2):
  1. DROP tasks where `instruction.md` is empty (whitespace-only). These
     are unrecoverable from the task data alone — `metadata.json` only
     contains `{source, bug_id, project}`, not the bug description we'd
     need to synthesise an instruction. Roughly 160/464 task dirs dropped.

  2. REWRITE `tests/test.sh` for surviving tasks to KILL the rubber-stamp:
     - Require the agent to have placed `/app/Solution.java` itself. If
       the file is missing -> reward 0, no fallback copy.
     - Otherwise compile + run JUnit as before, score from the runner
       exit code AND the JUnit "X tests successful" / "Y tests failed"
       summary lines (so a zero-test discovery still scores 0).
     - Reward floor is written first; only upgraded to 1 if all gates
       pass. The `trap EXIT` based scoring of v1 is removed (it can
       silently overwrite gated 0s with 1 on a clean script exit).

  3. Idempotency: a `.laion_v2_patched` marker file is dropped at each
     surviving task root; a top-level `_LAION_V2_PATCH_REPORT.txt` is
     written at --root with the dropped-task list for audit. Re-runs that
     find the marker skip the task. Dropped tasks (deleted) don't need a
     marker since they're gone.

Constraints (per upload spec):
  - `environment/Dockerfile`, `task.toml`, `metadata.json`, `solution/*`,
    `tests/initial/*`, and `tests/TestSolution.java` are NOT touched —
    only `tests/test.sh` is rewritten and a marker file added. Dropped
    tasks have their entire task dir removed.
  - The patcher is deterministic and idempotent.

Usage:
  python data/patchers/patch_exp_rpt_defects4j_v3_tasks.py \
      --root /path/to/extracted-tasks [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Markers (idempotency)
# --------------------------------------------------------------------------- #

_V2_MARKER_FILE = ".laion_v2_patched"
_V2_TESTSH_MARKER = "# --- laion v2 patch: no-fallback gate ---"
_V2_REPORT_FILENAME = "_LAION_V2_PATCH_REPORT.txt"

# --------------------------------------------------------------------------- #
# New tests/test.sh.
#
# Semantics:
#   - Reward floor 0; only upgraded after all gates pass.
#   - Gate A (no rubber-stamp): if /app/Solution.java is missing, exit 1
#     with reward 0. v1 silently copied the buggy initial file here; we
#     remove that fallback to stop scoring "agent did nothing" as a pass.
#   - Gate B (compile): javac must succeed (rc == 0).
#   - Gate C (real tests): JUnit's summary block must report at least one
#     test "started" AND zero failures AND zero containers failed. We parse
#     the well-known JUnit Platform summary lines:
#         [         N tests started     ]
#         [         M tests failed      ]
#         [         K containers failed ]
#     A "0 tests started" run -> reward 0 (vacuous; same defect class as
#     the methods2test/stack-php v3 fixes).
#   - Gate D (clean exit): the JUnit invocation's exit code must be 0.
#
# We deliberately do NOT use `trap cleanup EXIT` based scoring (the v1 bug)
# — explicit reward writes near the script end supersede any trap pattern.
# --------------------------------------------------------------------------- #
NEW_TEST_SH = f"""#!/bin/bash
{_V2_TESTSH_MARKER}
# v2 verifier: gate reward on (a) agent placed /app/Solution.java,
# (b) javac success, (c) JUnit running >=1 test with zero failures, and
# (d) clean JUnit exit. v1 silently copied a buggy initial Solution.java
# into /app when the agent did nothing -> free reward=1 whenever the
# buggy version happened to pass the unit tests. See QC follow-up
# 2026-05-14.

set +e  # we manage exit/reward explicitly; don't abort on first failure

mkdir -p /logs/verifier
# Reward floor: any abnormal exit below leaves this 0 in place.
echo "0" > /logs/verifier/reward.txt

cd /app

# Gate A: the agent must have placed /app/Solution.java itself. The v1
# fallback `cp /tests/initial/Solution.java /app/Solution.java` is gone:
# scoring the buggy initial as a pass is exactly the rubber-stamp we're
# eliminating.
if [ ! -f /app/Solution.java ]; then
    echo "FAIL: agent did not write /app/Solution.java" \\
        | tee /logs/verifier/test_output.txt
    echo "0" > /logs/verifier/reward.txt
    exit 1
fi

echo "=== Compiling solution and tests ==="
mkdir -p /app/classes
javac -cp /junit/junit-platform-console-standalone.jar:/app:/tests \\
    /app/Solution.java /tests/TestSolution.java -d /app/classes 2>&1 \\
    | tee /logs/verifier/test_output.txt
javac_rc=${{PIPESTATUS[0]}}

if [ "$javac_rc" -ne 0 ]; then
    echo "COMPILATION FAILED" | tee -a /logs/verifier/test_output.txt
    echo "0" > /logs/verifier/reward.txt
    exit 1
fi

echo "=== Running JUnit tests ==="
java -jar /junit/junit-platform-console-standalone.jar \\
    --class-path /app/classes \\
    --scan-class-path 2>&1 | tee -a /logs/verifier/test_output.txt
junit_rc=${{PIPESTATUS[0]}}

# Parse the JUnit Platform summary block. The console launcher emits lines
# like:
#     [         4 tests started      ]
#     [         0 tests failed       ]
#     [         0 containers failed  ]
# We grep for the LAST occurrence of each (in case the agent's code prints
# something that matches the regex earlier).
tests_started=$(grep -oE '\\[ *[0-9]+ tests started *\\]' /logs/verifier/test_output.txt \\
    | tail -1 | grep -oE '[0-9]+' | head -1)
tests_failed=$(grep -oE '\\[ *[0-9]+ tests failed *\\]' /logs/verifier/test_output.txt \\
    | tail -1 | grep -oE '[0-9]+' | head -1)
containers_failed=$(grep -oE '\\[ *[0-9]+ containers failed *\\]' /logs/verifier/test_output.txt \\
    | tail -1 | grep -oE '[0-9]+' | head -1)

tests_started=${{tests_started:-0}}
tests_failed=${{tests_failed:-0}}
containers_failed=${{containers_failed:-0}}

echo "v2 verifier: junit_rc=$junit_rc tests_started=$tests_started" \\
     "tests_failed=$tests_failed containers_failed=$containers_failed" \\
    | tee -a /logs/verifier/test_output.txt

if [ "$junit_rc" -eq 0 ] \\
        && [ "$tests_started" -ge 1 ] \\
        && [ "$tests_failed" -eq 0 ] \\
        && [ "$containers_failed" -eq 0 ]; then
    echo "ALL TESTS PASSED" | tee -a /logs/verifier/test_output.txt
    echo "1" > /logs/verifier/reward.txt
    exit 0
else
    echo "TESTS FAILED (junit_rc=$junit_rc tests_started=$tests_started" \\
         "tests_failed=$tests_failed containers_failed=$containers_failed)" \\
        | tee -a /logs/verifier/test_output.txt
    echo "0" > /logs/verifier/reward.txt
    if [ "$junit_rc" -ne 0 ]; then
        exit "$junit_rc"
    fi
    exit 1
fi
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _instruction_is_empty(inst_md: Path) -> bool:
    """Return True iff `inst_md` is missing or its contents are
    whitespace-only. We treat "no instruction" as the unsolvable case the
    v2 patcher drops."""
    if not inst_md.is_file():
        return True
    try:
        text = inst_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    return text.strip() == ""


def _patch_one_task(task_dir: Path, dry_run: bool) -> str:
    """Patch a single task dir. Returns one of:
        'dropped_empty_instruction'
        'patched'
        'already_patched'
        'no_test_sh'
        'unparseable'

    `task_dir` may be deleted entirely on the drop path.
    """
    marker = task_dir / _V2_MARKER_FILE
    if marker.exists():
        return "already_patched"

    inst_md = task_dir / "instruction.md"

    if _instruction_is_empty(inst_md):
        # Drop the task entirely. We can't synthesise an instruction from
        # the metadata (only has source/bug_id/project), and shipping a
        # blank-prompt task is what created the rubber-stamp pathology
        # in the first place.
        if not dry_run:
            shutil.rmtree(task_dir, ignore_errors=False)
        return "dropped_empty_instruction"

    test_sh = task_dir / "tests" / "test.sh"
    if not test_sh.is_file():
        # Unexpected layout — leave alone so the next pass can flag it.
        return "no_test_sh"

    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"

    if _V2_TESTSH_MARKER in existing:
        # Already patched at the file level even though the dir marker is
        # missing (partial patch from a previous crash). Still drop the
        # marker so future runs short-circuit cleanly.
        if not dry_run:
            marker.write_text(
                "laion v2 patch: no-fallback gate; marker repaired\n",
                encoding="utf-8",
            )
        return "already_patched"

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
        test_sh.chmod(0o755)
        marker.write_text(
            "laion v2 patch: dropped buggy initial fallback; gated reward\n",
            encoding="utf-8",
        )
    return "patched"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Path to extracted task corpus")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    # We don't filter on the presence of instruction.md here — the empty
    # case is exactly what we want to find and drop.
    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts: dict[str, int] = {}
    dropped_names: list[str] = []

    for i, td in enumerate(task_dirs, 1):
        result = _patch_one_task(td, dry_run=args.dry_run)
        counts[result] = counts.get(result, 0) + 1
        if result == "dropped_empty_instruction":
            dropped_names.append(td.name)

        if i % 100 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] "
                f"patched={counts.get('patched', 0)} "
                f"dropped={counts.get('dropped_empty_instruction', 0)} "
                f"already={counts.get('already_patched', 0)} "
                f"no_test_sh={counts.get('no_test_sh', 0)} "
                f"unparseable={counts.get('unparseable', 0)}",
                flush=True,
            )

    # Audit report at the corpus root. Always written (overwrites any
    # prior run's report) so the most recent state is visible.
    if not args.dry_run:
        report = root / _V2_REPORT_FILENAME
        with report.open("w", encoding="utf-8") as f:
            f.write("laion exp_rpt_defects4j-v3 -> v2 patch report\n")
            f.write(f"total_task_dirs_seen = {n_total}\n")
            for k in sorted(counts):
                f.write(f"{k} = {counts[k]}\n")
            f.write("\n# Dropped (empty-instruction) task names:\n")
            for name in dropped_names:
                f.write(name + "\n")

    print(
        f"\nDone. total={n_total} "
        f"patched={counts.get('patched', 0)} "
        f"dropped={counts.get('dropped_empty_instruction', 0)} "
        f"already_patched={counts.get('already_patched', 0)} "
        f"no_test_sh={counts.get('no_test_sh', 0)} "
        f"unparseable={counts.get('unparseable', 0)} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
