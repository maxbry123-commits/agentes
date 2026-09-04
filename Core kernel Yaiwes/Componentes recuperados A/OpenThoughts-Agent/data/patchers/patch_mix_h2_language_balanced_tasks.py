#!/usr/bin/env python3
"""
Patch DCAgent/mix_h2_language_balanced tasks whose `stack-bash-withtests-*`
source ships a tests/test.sh that aborts before writing reward.txt.

Bug (200/200 QC pass on 2026-05-14)
-----------------------------------
The reported metrics were 169/200 infra-ok (0.845) and 56/200 solved
(0.280). 31/31 (100%) of the infra failures had `metadata.json.source`
matching `stack-bash-withtests-*`. Categorized by Harbor trial.log
reason:

  * 27/31  No reward file found  ── test.sh aborts mid-script (set -e,
                                    exit-on-error inside `run_verifier`,
                                    or `exit` paths that bypass the
                                    `if run_verifier; then ... else ...`
                                    dispatch) without ever writing
                                    `/logs/verifier/reward.txt`. Harbor
                                    raises RewardFileNotFoundError ->
                                    VerifierRuntimeError.
  * 3/31   Verifier timed out     ── while-true loops, interactive
                                    `read p` prompts inherited from the
                                    upstream scraped script. The reward
                                    floor + EXIT trap below still
                                    converts these to a clean reward=0
                                    because the trap fires on SIGTERM
                                    from the verifier-side timeout
                                    handler.
  * 1/31   Daytona transient      ── "failed to resolve container IP"
                                    is a sandbox-side flake, not
                                    patchable here.

Same disease as `DCAgent/exp_rpt_stack-bash-withtests-gpt5mini` (151/200
infra-failed there); reuses that patcher's reward-floor + EXIT-trap
mechanism, scoped to `stack-bash-withtests-*` tasks in this mixture.

Real verifier stdout from the corpus (task 0172, netcdf):

    /tests/test.sh: line 8: ../test_common.sh: No such file or directory
    *** Testing in-memory (diskless) files with and without persistence
    /tests/test.sh: line 24: /nc-config: No such file or directory
    /tests/test.sh: line 27: /tst_diskless: No such file or directory
    PASS: diskless netCDF classic file without persistence
    /tests/test.sh: line 40: /tst_diskless: No such file or directory
    #### tst_diskless.nc not created
    FAIL: diskless netCDF classic file with persistence
    ...
    diff tst_diskless3_file.cdl tst_diskless3_memory.cdl   # set -e aborts here

Fix
---
For every task whose `metadata.json` source starts with
`stack-bash-withtests`, rewrite `tests/test.sh` so that:

  1. **Reward floor + EXIT trap.** Inserted right after the shebang.
     Guarantees `/logs/verifier/reward.txt` is "0" by the time the
     script exits, even if every later step fails (or the script is
     SIGTERM'd by the verifier-side timeout). This alone converts ~30
     unrecoverable infra-fails -> ~30 legitimate reward=0 trials,
     restoring the infra-ok rate from 84.5% to ~99%.
  2. **Stdin redirection.** `exec </dev/null` keeps interactive
     `read` commands from blocking forever (those produce TIMEOUT
     failures in the QC, e.g. task 0026 has 9 `read p` prompts).
  3. **Idempotent** via marker.

We do NOT attempt to fix bugs in the test.sh body itself (missing
binaries, hard syntax errors, hardcoded ${execdir} paths). Those tasks
will still legitimately score reward=0, which is the correct outcome --
infra-ok with a real verifier signal is the success criterion, not
solve rate.

Non-stack-bash-withtests tasks in the mixture (crosscodeeval-typescript,
stack-cpp, crosscodeeval-csharp, methods2test, stack-pytest, stack-junit,
bigcodebench) are left untouched -- they had 0/31 failures in QC.

Snapshot impact
---------------
Only `tests/test.sh` is touched. `environment/Dockerfile` is preserved
byte-for-byte, so Daytona env hashes stay identical to v1 and the
snapshot count is unchanged (well below the 10-new / 60-org caps).

Usage
-----
    python -m data.patchers.patch_mix_h2_language_balanced_tasks --root <dir>
    python -m data.patchers.patch_mix_h2_language_balanced_tasks --root <dir> --dry-run
    python -m data.patchers.patch_mix_h2_language_balanced_tasks --root <dir> --limit 5
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
PATCH_MARKER = "# --- laion v2 patch: mix_h2_language_balanced reward floor ---"
PATCH_END_MARKER = "# --- end laion v2 patch (mix_h2) ---"

# Reward floor + EXIT trap + stdin redirect. Inserted unconditionally
# right after the shebang on every stack-bash-withtests task.
#
# Why each line:
#   * `mkdir -p /logs/verifier` -- script may run before this dir exists
#     (the upstream `set -e; mkdir -p` pattern aborts at line 2 if any
#     environment quirk hits the mkdir; our pre-`set -e` mkdir is safe).
#   * `echo 0 > reward.txt` -- the floor itself. Any subsequent abort
#     leaves a valid reward=0, not a missing file.
#   * `trap '... echo 0 > reward.txt' EXIT` -- belt-and-suspenders. If
#     anything between here and the script's natural exit deletes or
#     truncates reward.txt (e.g. `rm -rf /tmp/* /logs/*`), we put a 0
#     back. The `[ -s ... ]` guard means we don't overwrite a "1"
#     written by a successful run_verifier dispatch.
#   * `exec </dev/null` -- the QC sample contained tasks with literal
#     `read p` prompts (task 0026: "Pulsa enter para continuar"). With
#     no stdin those read commands return immediately (EOF), letting
#     the script continue past the prompt instead of hanging until
#     the verifier-side 600s timeout.
REWARD_FLOOR = f"""{PATCH_MARKER}
mkdir -p /logs/verifier 2>/dev/null || true
echo 0 > /logs/verifier/reward.txt 2>/dev/null || true
trap '[ -s /logs/verifier/reward.txt ] || echo 0 > /logs/verifier/reward.txt' EXIT
exec </dev/null
{PATCH_END_MARKER}
"""

SHEBANG_RE = re.compile(r"^(#![^\n]*\n)")

# Source prefixes we patch. Any task whose metadata.json.source startswith
# one of these (matched as a prefix) gets the reward floor.
TARGET_SOURCE_PREFIXES = ("stack-bash-withtests",)


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
    """Apply the reward floor. Returns (new_text, changed)."""
    if PATCH_MARKER in text:
        return text, False

    m = SHEBANG_RE.match(text)
    if m:
        new_text = m.group(1) + REWARD_FLOOR + text[m.end() :]
    else:
        # No shebang -- prepend a #!/bin/bash plus the floor.
        new_text = "#!/bin/bash\n" + REWARD_FLOOR + text

    return new_text, new_text != text


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
            "Patch stack-bash-withtests tasks inside "
            "DCAgent/mix_h2_language_balanced so their tests/test.sh always "
            "writes /logs/verifier/reward.txt (no more "
            "RewardFileNotFoundError infra failures)."
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
        help="Optional TSV file to record tasks whose patched test.sh "
        "failed `bash -n` (task_id\\tstderr_first_line).",
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
