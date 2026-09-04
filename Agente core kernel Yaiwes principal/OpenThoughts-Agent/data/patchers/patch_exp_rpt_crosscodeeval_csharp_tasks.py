#!/usr/bin/env python3
"""
exp_rpt_crosscodeeval-csharp v2 patcher.

Bug (v1 -> v2): the upstream `DCAgent/exp_rpt_crosscodeeval-csharp` corpus is a
*structural-mismatch* corpus -- the task harness was templated as Python but
the actual code under test is C#. Concretely, in every one of the 200 task
dirs we observe:

  - `environment/Dockerfile` -> `FROM python:3.10-slim` + pytest install.
  - `tests/test.sh` -> runs `pytest /tests/test_solution.py`.
  - `tests/test_solution.py` -> does `import solution` then asserts non-empty.
  - `solution/solution.py` (the GOLD completion) contains raw C# code
     (e.g. `Thread> Threads => GetThreads();`).
  - `metadata.json` -> `"language": "python"` (wrong; should be `"csharp"`).
  - `instruction.md` -> ```python ``` code fence wrapping C# source, and
     the prompt instructs the agent to write to `/app/solution.py`.

QC evidence (10/10 inspected trial dirs in the v1 traces export):
  - All 10 trials died at infra setup with `DaytonaError: Failed to create
    sandbox: Cannot connect to host app.daytona.io:443` (DNS resolution
    failure on the QC RUNNER machine, not a per-task issue). So the
    0/200 infra-ok report partly reflects a runner-side network outage at
    the time of QC, not the dataset itself.
  - HOWEVER, the structural mismatch above means that EVEN WITH WORKING
    INFRA, every single trial would have failed at the verifier stage:
       1. `import solution` raises SyntaxError because solution.py is C#.
       2. Even if it loaded, the `len(inspect.getmembers(solution)) > 0`
          assertion is a trivial floor, not a correctness check.
       3. `solution.py` (gold) is a 1-3 line fragment, not a Python module.

So this patcher addresses the structural defect that makes the task corpus
unsuitable for *any* run, infra outage aside. Fixing this gives QC a real
signal on the next pass: trials that complete will produce a reward that
actually correlates with the agent's C# completion quality.

Fix (v2): convert each task from a broken-Python-shell into a working
text-completion task whose verifier is a deterministic exact-match diff:

  1. `metadata.json`: set `language` -> `"csharp"`. Other fields untouched.
  2. `instruction.md`:
       - Replace the opening ```python``` fence with ```csharp``` (cosmetic
         but reduces model confusion).
       - Replace "Place your complete solution in `/app/solution.py`" with
         "Place your complete solution in `/app/solution.txt`". The agent's
         output is a code FRAGMENT (not a compilable unit), so we deliberately
         use a `.txt` extension to avoid baiting C#/Python parsers.
  3. `solution/solution.py` -> `solution/solution.txt` (rename; keep contents).
     This is the gold completion the verifier compares against.
  4. `tests/test.sh`: rewrite to compare `/app/solution.txt` (agent output)
     against `/tests/solution.txt` (gold) byte-for-byte after both have been
     stripped of leading/trailing whitespace and CR/LF normalised. Reward = 1
     iff the comparison succeeds.
       - The container drops the gold into `/tests/solution.txt` via the
         task's `tests/` fixture mount (Harbor mounts `tests/` at `/tests/`).
         We therefore COPY the gold into `tests/solution.txt` at patch time
         so it lives alongside `test.sh` and gets mounted automatically.
  5. `tests/test_solution.py`: delete. The Python-pytest verifier is replaced
     by the shell-based diff in test.sh. Keeping it would just confuse the
     trial.log on failures.
  6. `environment/Dockerfile`: left UNTOUCHED. `python:3.10-slim` is already
     overkill for `bash`+`diff`+`sed` (the only tools test.sh needs); pulling
     a .NET SDK image would 50x the snapshot size for zero correctness gain
     given the text-match verifier. Identical Dockerfile across all 200
     tasks => 1 Daytona snapshot total (well under 10/60 caps).
  7. Idempotency: a `.laion_v2_patched` marker file is dropped at the task
     root. Re-runs skip tasks where this exists.

Constraints (per upload spec):
  - Do not touch `task.toml` or `environment/Dockerfile`.
  - All 200 task dirs survive (no drops); only mechanical rewrites.
  - The patcher is deterministic and idempotent.

Usage:
  python data/patchers/patch_exp_rpt_crosscodeeval_csharp_tasks.py \
      --root /path/to/exp_rpt_crosscodeeval-csharp [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Markers (idempotency)
# --------------------------------------------------------------------------- #

_V2_MARKER_FILE = ".laion_v2_patched"
_V2_TESTSH_MARKER = "# --- laion v2 patch: text-diff verifier ---"

# --------------------------------------------------------------------------- #
# New test.sh: deterministic exact-match diff verifier.
#
# Behaviour:
#   - Reward floor 0 (set first; only upgraded after match).
#   - Read agent's /app/solution.txt and the gold /tests/solution.txt.
#   - Strip CR (DOS line endings) and trailing whitespace per line.
#   - Strip leading + trailing blank lines.
#   - Compare via plain `diff`. Any difference -> reward stays 0.
#   - If /app/solution.txt is missing -> reward 0 (agent didn't write the
#     expected file).
#   - If /tests/solution.txt is missing -> reward 0 (impossible: we copy it
#     into the tests/ dir at patch time; but guard anyway).
#
# We deliberately do NOT do "semantic" C# parsing here -- the agent output
# is a code FRAGMENT (cross-file completion), not a compilable unit. Exact
# match (EM) is the canonical CrossCodeEval metric.
# --------------------------------------------------------------------------- #
NEW_TEST_SH = f"""#!/bin/bash
{_V2_TESTSH_MARKER}
# v2 verifier: exact-match diff between agent's /app/solution.txt and
# the gold /tests/solution.txt (after whitespace normalisation).

mkdir -p /logs/verifier
# Reward floor: 0 unless the comparison succeeds.
echo "0" > /logs/verifier/reward.txt

AGENT_OUT=/app/solution.txt
GOLD_OUT=/tests/solution.txt

if [ ! -f "$AGENT_OUT" ]; then
    echo "FAIL: agent did not write $AGENT_OUT" \\
        | tee /logs/verifier/test_output.txt
    exit 1
fi
if [ ! -f "$GOLD_OUT" ]; then
    echo "FAIL: gold $GOLD_OUT missing from task tests/ fixture" \\
        | tee /logs/verifier/test_output.txt
    exit 1
fi

# Normalise both: strip CR, strip trailing whitespace, strip leading/trailing
# blank lines. We keep the comparison strict on internal whitespace -- only
# fragile EOL/EOF differences are normalised.
normalise() {{
    sed -e 's/\\r$//' -e 's/[ \\t]*$//' "$1" \\
        | awk 'BEGIN{{p=0}} /[^ \\t]/{{p=1}} p{{print}}' \\
        | tac \\
        | awk 'BEGIN{{p=0}} /[^ \\t]/{{p=1}} p{{print}}' \\
        | tac
}}

A=$(mktemp); B=$(mktemp)
normalise "$AGENT_OUT" > "$A"
normalise "$GOLD_OUT"  > "$B"

if diff -q "$A" "$B" > /dev/null 2>&1; then
    echo "PASS: agent output matches gold completion." \\
        | tee /logs/verifier/test_output.txt
    echo "1" > /logs/verifier/reward.txt
    rm -f "$A" "$B"
    exit 0
else
    {{
        echo "FAIL: agent output differs from gold completion."
        echo "--- gold ---"
        cat "$B"
        echo "--- agent ---"
        cat "$A"
        echo "--- diff ---"
        diff "$B" "$A" || true
    }} | tee /logs/verifier/test_output.txt
    rm -f "$A" "$B"
    exit 1
fi
"""


# --------------------------------------------------------------------------- #
# Per-task patch
# --------------------------------------------------------------------------- #


def patch_instruction_md(text: str) -> str:
    """Rewrite the prompt to (a) use a csharp code fence and (b) point at
    `/app/solution.txt` instead of `/app/solution.py`.

    Idempotent: re-runs that find the fence already swapped just return the
    input unchanged.
    """
    # (a) Swap the ```python ... ``` opener that wraps the C# context. We
    # only rewrite the FIRST occurrence (the prompt template uses one). If
    # the document has no ```python fence (already patched, or unexpected
    # template), leave the text alone for that part.
    if "```python" in text:
        text = text.replace("```python", "```csharp", 1)

    # (b) Swap the output-path instruction. We accept either a backtick or
    # bare-text variant.
    text = text.replace("`/app/solution.py`", "`/app/solution.txt`")
    text = re.sub(
        r"(?<!`)/app/solution\.py(?!`)",
        "/app/solution.txt",
        text,
    )
    return text


def patch_metadata_json(raw: str) -> str:
    """Set `language` -> `csharp` in the metadata blob.

    Preserves field order and other keys verbatim. Returns the new text
    (with a trailing newline if the input had one).
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Defensive: leave malformed metadata alone.
        return raw

    data["language"] = "csharp"

    # Pretty-print with 2-space indent (matches the source-of-truth shape we
    # saw in QC inspection: single-line compact dict). Use compact form to
    # match upstream's emission.
    new = json.dumps(data, separators=(", ", ": "))
    if raw.endswith("\n"):
        new += "\n"
    return new


def patch_one_task(task_dir: Path, dry_run: bool) -> tuple[bool, str]:
    """Apply the v2 patch to a single task dir.

    Returns (changed, reason). `changed` is False iff the task was already
    patched (marker present) or could not be patched (missing files).
    """
    marker = task_dir / _V2_MARKER_FILE
    if marker.exists():
        return False, "already_patched"

    inst_md = task_dir / "instruction.md"
    meta_json = task_dir / "metadata.json"
    sol_py = task_dir / "solution" / "solution.py"
    sol_txt = task_dir / "solution" / "solution.txt"
    test_sh = task_dir / "tests" / "test.sh"
    test_solution_py = task_dir / "tests" / "test_solution.py"
    test_gold_txt = task_dir / "tests" / "solution.txt"

    if not inst_md.is_file():
        return False, "no_instruction_md"
    if not meta_json.is_file():
        return False, "no_metadata_json"

    # ----------------------------------------------------------------- #
    # Stage 1: read everything we need before any writes.
    # ----------------------------------------------------------------- #
    inst_text = inst_md.read_text(encoding="utf-8", errors="replace")
    meta_text = meta_json.read_text(encoding="utf-8", errors="replace")

    gold_text = None
    if sol_py.is_file():
        gold_text = sol_py.read_text(encoding="utf-8", errors="replace")
    elif sol_txt.is_file():
        # Already-renamed case: someone partially patched. Pick up where we
        # left off.
        gold_text = sol_txt.read_text(encoding="utf-8", errors="replace")
    else:
        return False, "no_gold_solution"

    # ----------------------------------------------------------------- #
    # Stage 2: compute new contents.
    # ----------------------------------------------------------------- #
    new_inst = patch_instruction_md(inst_text)
    new_meta = patch_metadata_json(meta_text)
    new_test_sh = NEW_TEST_SH

    # ----------------------------------------------------------------- #
    # Stage 3: dry-run short-circuit.
    # ----------------------------------------------------------------- #
    if dry_run:
        return True, "would_patch"

    # ----------------------------------------------------------------- #
    # Stage 4: write everything. Order matters: write files first, then
    # delete the obsolete pytest stub and rename the gold, then drop the
    # marker LAST so a crash mid-patch leaves the task un-marked and the
    # next run can pick up cleanly (idempotent retries).
    # ----------------------------------------------------------------- #
    inst_md.write_text(new_inst, encoding="utf-8")
    meta_json.write_text(new_meta, encoding="utf-8")
    test_sh.write_text(new_test_sh, encoding="utf-8")
    test_sh.chmod(0o755)

    # Drop the gold into BOTH solution/solution.txt (canonical home for the
    # gold answer in the task layout) AND tests/solution.txt (so Harbor's
    # tests/ fixture mount makes it available at /tests/solution.txt inside
    # the container, where test.sh reads it).
    test_gold_txt.write_text(gold_text, encoding="utf-8")

    if sol_py.is_file():
        sol_txt.write_text(gold_text, encoding="utf-8")
        sol_py.unlink()
    # (If sol_txt already exists from a prior partial patch, leave it.)

    if test_solution_py.is_file():
        test_solution_py.unlink()

    marker.write_text(
        "laion v2 patch applied: text-diff verifier; csharp language metadata\n",
        encoding="utf-8",
    )

    return True, "patched"


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

    task_dirs = sorted(
        d for d in root.iterdir() if d.is_dir() and (d / "instruction.md").exists()
    )
    if not task_dirs:
        print(f"No task dirs (with instruction.md) under {root}", file=sys.stderr)
        return 2

    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    n_patched = 0
    n_already = 0
    n_skipped = 0
    reasons: dict[str, int] = {}

    for i, d in enumerate(task_dirs, 1):
        changed, reason = patch_one_task(d, args.dry_run)
        reasons[reason] = reasons.get(reason, 0) + 1
        if reason == "already_patched":
            n_already += 1
        elif changed:
            n_patched += 1
        else:
            n_skipped += 1

        if i % 200 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] patched={n_patched} "
                f"already={n_already} skipped={n_skipped}",
                flush=True,
            )

    print(
        f"\nDone. {n_patched}/{n_total} task dirs patched "
        f"(dry_run={args.dry_run}).\n"
        f"  already_patched = {n_already}\n"
        f"  skipped         = {n_skipped}\n"
    )
    print("Reason breakdown:")
    for reason, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5}  {reason}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
