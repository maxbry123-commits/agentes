#!/usr/bin/env python3
"""
Patch DCAgent/mix_h10_reward_staged tasks whose `stack-pytest-*` source ships
a tests/test.sh that uses the bare `python` binary on an Ubuntu 24.04 image
which only ships `python3`.

Bug (200/200 QC pass on 2026-05-14)
-----------------------------------
Reported headline metrics: 200/200 infra-ok (100%, misleading -- staged
verifier still returns reward=0 on a clean stage-0 fail, so Harbor records
"no infra exception" even though the task can NEVER score) and 48/200
solved (24.0%).

Of the 152/200 reward=0 trials, the breakdown by source + verifier
stdout pattern was:

  source                 n_trials  solved  zero@stage0
  --------------------- --------- ------- ------------
  codenet-python              43       0           38   <- 1000 tasks total, no test files shipped (unfixable here)
  stack-pytest                28       0           28   <- 500 tasks total, ALL fail with `python: command not found`
  crosscodeeval-python        30       6           23   <- agent didn't write /app/solution.py (single-episode gpt-5-nano cap)
  pymethods2test              31      13           11
  e2egit                      22      14            8
  codereval-python            19       3            7
  exercism-python              6       0            6
  unitsyn-python              21      12            5

The only systematic, programmatically-fixable infra defect in this run
is the stack-pytest "bare python" bug. All 500 stack-pytest tasks ship
a byte-identical Dockerfile and a near-identical test.sh; every one of
the 28 stack-pytest tasks sampled fails with:

    /tests/test.sh: line 24: python: command not found
    Reached stage 0 / N (reward=0.0)

The Dockerfile is::

    FROM ubuntu:24.04
    WORKDIR /app
    RUN apt-get update && apt-get install -y python3 python3-pip python3-venv bsdutils ...

Ubuntu 24.04 deliberately does not install a `python` symlink (it ships
only `python3`). But the test.sh body executes::

    cd /app && python -m pytest /tests/ $TESTS --tb=short 2>&1 | ...

…which fails before pytest ever runs. The bash JSON parsing earlier in
the script already uses `python3 -c` correctly; only the pytest invocation
uses bare `python`.

Fix
---
For every task whose `metadata.json` source starts with `stack-pytest-`,
rewrite `tests/test.sh` so the pytest invocation uses `python3` instead
of `python`. We do a targeted substitution rather than a wholesale
rewrite so any per-task customization is preserved. Idempotent via
PATCH_MARKER (so re-runs are no-ops).

Snapshot impact
---------------
We touch only `tests/test.sh`. The `environment/Dockerfile` is preserved
byte-for-byte across all 500 stack-pytest tasks (single hash, single
Daytona snapshot). Daytona only hashes the Dockerfile build context for
snapshot identity; modifying test.sh does NOT churn snapshots. Snapshot
budget for this patch: 0 new snapshots.

What we do NOT fix
------------------
* `codenet-python` (1000 tasks, ~25.8% of the corpus): the staged-reward
  variant references pytest test names (`test_solution_file_exists`,
  `test_min_moves_basic_no_blocking`, ...) that are never shipped. The
  tar contains only `tests/test.sh`, no `tests/test_solution.py`. pytest
  collects 0 items -> "no tests ran" -> reward 0 forever. Upstream
  `DCAgent/exp_rpt_codenet-python` is input/output-judge style (text
  inputs + expected outputs, run `python3 solution.py < input`), not
  pytest -- so we cannot mechanically import test files from upstream.
  This source is fundamentally broken in mix_h10_reward_staged; the
  dataset producer needs to re-curate codenet-python with pytest tests
  before it can score any reward signal.

* `crosscodeeval-python` / `exercism-python` / `pymethods2test`
  `no_solution_module` failures: the agent literally never wrote
  `/app/solution.py`. This is an agent capability ceiling (gpt-5-nano +
  `max_episodes=1` + `reasoning_effort: medium` produces one response
  with bash commands that often never execute the file write). Not an
  infra defect.

* The "multiple `-k` flags" oddity in test.sh: `python3 -c "... '
  '.join(['-k '+t for t in d.get(...)]))` emits e.g.
  `-k test_a -k test_b -k test_c`. pytest only honours the LAST `-k`
  flag, so only `test_c` is run. This actually INFLATES rewards (you
  pass a multi-test stage as soon as the last test in the list passes),
  it doesn't cause reward=0 failures. Not addressed in v2.

Usage
-----
    python -m data.patchers.patch_mix_h10_reward_staged_tasks --root <dir>
    python -m data.patchers.patch_mix_h10_reward_staged_tasks --root <dir> --dry-run
    python -m data.patchers.patch_mix_h10_reward_staged_tasks --root <dir> --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# Idempotency marker. Different name from sibling patchers so `bash -n`
# failures show which patcher touched the file.
PATCH_MARKER = "# --- laion v2 patch: mix_h10 stack-pytest python3 ---"

# Source prefixes we patch. Any task whose metadata.json.source starts with
# one of these (matched as a prefix) gets the python -> python3 substitution.
TARGET_SOURCE_PREFIXES = ("stack-pytest-",)

# The specific bug we fix: the line that runs pytest uses bare `python`.
# Pattern is robust to whitespace and trailing flags; we only touch the
# `python -m pytest` token. We deliberately do NOT do a global
# `s/python/python3/` because the test.sh already contains correct
# `python3 -c "..."` invocations earlier in the file.
PYTEST_PYTHON_RE = re.compile(
    r"(?P<lead>\bcd\s+/app\s*&&\s*)python(?P<rest>\s+-m\s+pytest\b)"
)


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


def patch_test_sh_text(text: str) -> tuple[str, bool]:
    """Rewrite bare `python -m pytest` -> `python3 -m pytest` after `cd /app`.

    Returns (new_text, changed). Idempotent via PATCH_MARKER: if the marker
    is already present, returns (text, False) immediately.
    """
    if PATCH_MARKER in text:
        return text, False

    new_text, n = PYTEST_PYTHON_RE.subn(r"\g<lead>python3\g<rest>", text)
    if n == 0:
        # No bare `python -m pytest` after `cd /app` was found -- nothing
        # to patch. Don't insert a marker (so a future patcher can still
        # touch this file).
        return text, False

    # Insert marker right after the shebang so it's visible in `head`.
    shebang_re = re.compile(r"^(#![^\n]*\n)")
    m = shebang_re.match(new_text)
    if m:
        new_text = m.group(1) + PATCH_MARKER + "\n" + new_text[m.end() :]
    else:
        new_text = "#!/bin/bash\n" + PATCH_MARKER + "\n" + new_text

    return new_text, True


def syntax_check(path: Path) -> tuple[bool, str]:
    """Run `bash -n` on path. Returns (ok, stderr_first_line)."""
    try:
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return False, "bash -n timed out"
    except FileNotFoundError:
        return False, "bash not found"
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout).strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Patch stack-pytest tasks inside DCAgent/mix_h10_reward_staged "
            "so their tests/test.sh uses python3 instead of bare python "
            "(no more `python: command not found` infra failures on the "
            "Ubuntu 24.04 base image)."
        ),
    )
    p.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing extracted task subdirectories.",
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
        help="Report what would change; write nothing.",
    )
    p.add_argument(
        "--drop-log",
        type=str,
        default=None,
        help=(
            "Optional TSV file to record tasks whose patched test.sh "
            "failed `bash -n` (task_id\\tstderr_first_line)."
        ),
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
        print("[patcher] DRY RUN - no files will be written")

    counts = {
        "patched": 0,
        "already_patched": 0,
        "skipped_other_source": 0,
        "skipped_no_metadata": 0,
        "skipped_no_test_sh": 0,
        "skipped_no_pytest_line": 0,
        "dropped_bash_n_fail": 0,
    }
    drop_log_lines: list[str] = []
    dropped_examples: list[tuple[str, str]] = []

    for i, td in enumerate(task_dirs, 1):
        task_id = td.name
        source = _task_source(td)
        if source is None:
            counts["skipped_no_metadata"] += 1
            continue
        if not any(source.startswith(p) for p in TARGET_SOURCE_PREFIXES):
            counts["skipped_other_source"] += 1
            continue

        test_sh = td / "tests" / "test.sh"
        if not test_sh.is_file():
            counts["skipped_no_test_sh"] += 1
            continue

        original = test_sh.read_text(encoding="utf-8", errors="replace")
        if PATCH_MARKER in original:
            counts["already_patched"] += 1
            continue

        patched, changed = patch_test_sh_text(original)
        if not changed:
            counts["skipped_no_pytest_line"] += 1
            continue

        if args.dry_run:
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tf:
                tf.write(patched)
                tmp_path = Path(tf.name)
            try:
                ok, stderr = syntax_check(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            test_sh.write_text(patched, encoding="utf-8")
            ok, stderr = syntax_check(test_sh)

        if not ok:
            first_line = stderr.splitlines()[0] if stderr else "(no stderr)"
            drop_log_lines.append(f"{task_id}\t{first_line}")
            if len(dropped_examples) < 5:
                dropped_examples.append((task_id, first_line))
            counts["dropped_bash_n_fail"] += 1
            # Remove the whole task dir so it's excluded from the v2
            # upload -- if our patched test.sh can't even bash-parse,
            # the task was already unrecoverable.
            if not args.dry_run:
                shutil.rmtree(td, ignore_errors=True)
            continue

        counts["patched"] += 1

        if i % 500 == 0 or i == len(task_dirs):
            print(
                f"[{i}/{len(task_dirs)}] patched={counts['patched']} "
                f"already={counts['already_patched']} "
                f"dropped={counts['dropped_bash_n_fail']} "
                f"skipped_other={counts['skipped_other_source']}",
                flush=True,
            )

    print("\n[patcher] Result summary:")
    for k in (
        "patched",
        "already_patched",
        "skipped_other_source",
        "skipped_no_metadata",
        "skipped_no_test_sh",
        "skipped_no_pytest_line",
        "dropped_bash_n_fail",
    ):
        print(f"  {counts[k]:6d}  {k}")
    print(f"[patcher] Root:    {root}")
    print(f"[patcher] Dry run: {args.dry_run}")

    if dropped_examples:
        print("\n[patcher] First dropped tasks (id, bash -n stderr):")
        for tid, msg in dropped_examples:
            print(f"  {tid}: {msg}")

    if args.drop_log and drop_log_lines:
        Path(args.drop_log).write_text("\n".join(drop_log_lines) + "\n")
        print(f"\n[patcher] Drop log written to: {args.drop_log}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
