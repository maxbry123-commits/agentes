#!/usr/bin/env python3
"""
exp_rpt_defects4j v3-v3 -> v3-v4 patcher (uploaded as
`laion/exp_rpt_defects4j-v3-v4`).

Bug (found in QC 2026-05-16):
  v3-v3 solve rate is 1/200 (0.5%) on `gpt-5-nano + terminus-2 +
  max_episodes=1`. The v3-v3 patch correctly pre-staged
  `/app/Solution.java`, kept the v2 anti-rubber-stamp protection,
  and produced valid prompts. But v3-v3 reveals TWO compounding
  defects that together cap solves at ~0.5%:

  Defect 1 (broken test fixtures — unsolvable at any agent skill):
    82 of 298 (27.5%) tasks ship with a `tests/TestSolution.java`
    that physically cannot compile inside the Dockerfile's
    classpath (`/app:/tests:/junit/...`, eclipse-temurin:17-jdk-jammy
    with ONLY the JUnit 5 jar installed):

      - 53 tasks: TestSolution.java uses a JDK class like
        `BigDecimal`, `ArrayList`, `Set`, `Field`, `BufferedReader`,
        `Matcher` etc. **without an `import` statement**. javac
        cannot resolve the symbol -> Gate B always fails.

      - 31 tasks: TestSolution.java imports a third-party package
        (`org.joda.time`, `org.jsoup`, `com.fasterxml.jackson.*`,
        `org.apache.commons.cli`, `com.google.gson`, etc.). The
        Dockerfile installs none of these -> javac fails.

    For these 82 tasks the verifier ALWAYS reports "COMPILATION
    FAILED" in TestSolution.java, regardless of what the agent
    writes to `/app/Solution.java`. They are not a model-capability
    problem; they are a task-data problem.

    Verified by static analysis of the parquet
    (see triage step 1 in this PR's transcript). Cross-referenced
    against the 38 Gate-B failures observed in the 200-trial QC:
    24 of those 38 were in this set; 14 were genuine
    agent-introduced compile bugs.

    v3-v4 DROPS these 82 tasks.

  Defect 2 (the prompt does not match the harness's actual cadence):
    The instruction text says only:

        "Your assignment is to address the issue found in the buggy
         function located at `/app/Solution.java`. Please do not
         reveal the fix."

    Combined with `max_episodes=1`, this leaves the agent to discover
    on its own that a single turn must contain ALL of {read, edit,
    compile}. In the v3-v3 QC, 156 of 200 trials (78%) used their
    one turn on a multi-step exploration plan (ls / grep / sed -n /
    nl / cat) and never emitted an actual file edit. The agent's
    default behavior under reasoning_effort=medium is to plan a
    multi-step diagnosis pass first, then *defer* the patch to a
    later turn that never comes.

    The one v3-v3 solve (defects4j-0439) and the 38 Gate-B compile
    attempts share a single behavioral pattern: they used a
    `cat > /app/Solution.java <<'EOF' ... EOF\n` heredoc as part of
    the SAME response that did the `ls` and `sed`, and they marked
    `task_complete: true`. That's the behavior we need to elicit.

    v3-v4 rewrites instruction.md to make this explicit, while still
    keeping the prompt task-specific:

      - States "ONE shell-command batch — read, edit, AND compile".
      - States where TestSolution.java lives so the agent can read
        what's being tested *within the same batch* (very few v3-v3
        traces ever read the test).
      - Gives a concrete cat-heredoc + javac command shape.
      - Keeps the original bug description verbatim. Per-task
        semantic context is preserved.

  Two additional defects considered but NOT addressed in v4:
    (a) The Dockerfile installs no third-party JARs. If we shipped
        commons-lang3 / jsoup / jackson / guava / joda-time as base
        layer JARs the 31 external-import tasks could compile, but
        their TestSolution.java semantics rely on *specific*
        versions and class behaviors we'd be guessing at. Dropping
        is safer than guessing.
    (b) `max_episodes=1` itself is the dominant solve-rate ceiling.
        That's a runner config knob, not a dataset knob. v4 does not
        try to compensate for it beyond the instruction tweak above.

Fix (uploaded as v3-v4):
  1. DROP 82 tasks whose `tests/TestSolution.java` references a
     symbol the Dockerfile classpath can't resolve. The exact list
     is computed deterministically from the union of:
       - "test imports a third-party package" (31 tasks)
       - "test uses a JDK class without import" (53 tasks)
       - intersection between the two: 2 tasks
     -> total 82 unique. Listed in _UNSOLVABLE_BY_TEST_HARNESS below.

  2. REWRITE instruction.md to prepend a "one-shot" framing block
     that tells the agent: ONE batch, read+edit+compile, use heredoc,
     read TestSolution.java to know expected behavior. The original
     bug description (verbatim) is preserved underneath.

  3. The v3 Dockerfile (pre-stage /app/Solution.java) and v3
     test.sh (sha-diff Gate A + compile/junit gates) are UNCHANGED.
     They are working correctly: the failure is NOT in the verifier
     and NOT in the staging; it's in the task fixtures and the
     prompt.

  4. Idempotency: drop a `.laion_v4_patched` marker file at each
     surviving task root; write `_LAION_V4_PATCH_REPORT.txt` at
     --root with the dropped-task list. Re-runs that find the
     marker skip the task. Prior v2 and v3 markers are preserved.

  5. Tasks already marked `.laion_v4_patched` are left alone; tasks
     whose dir matches the unsolvable list AND that still exist on
     disk are removed.

Constraints (per upload spec):
  - `task.toml`, `metadata.json`, `solution/*`, `tests/initial/*`,
    `tests/TestSolution.java`, `tests/test.sh`, and
    `environment/Dockerfile` (with v3 patch applied) are NOT touched
    on surviving tasks. Only `instruction.md` is rewritten, and a
    marker file is added. Dropped tasks have their entire task dir
    removed.
  - Idempotent and deterministic.

Usage:
  python data/patchers/patch_exp_rpt_defects4j_v3_v3_tasks.py \\
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

_V4_MARKER_FILE = ".laion_v4_patched"
_V4_INSTRUCTION_MARKER = "<!-- laion v4 patch: one-shot framing -->"
_V4_REPORT_FILENAME = "_LAION_V4_PATCH_REPORT.txt"

# --------------------------------------------------------------------------- #
# Unsolvable tasks: TestSolution.java cannot compile in the Dockerfile's
# classpath. Computed deterministically from the v3-v3 parquet by static
# analysis (see top-of-file docstring, Defect 1). 82 entries total.
#
# Algorithm used to produce this list:
#   For each task in laion/exp_rpt_defects4j-v3-v3:
#     - Parse `tests/TestSolution.java`.
#     - bad_external = any import that starts with a non-java./non-javax./
#       non-org.junit./non-org.opentest4j. prefix.
#     - bad_unimported = (set of CamelCase tokens that look like common JDK
#       classes — BigDecimal, ArrayList, Set, etc. — see _COMMON_JDK_PROBES
#       in the analysis) ∩ used \ imported \ declared-in-file.
#     - Drop if bad_external OR bad_unimported is non-empty.
# --------------------------------------------------------------------------- #
_UNSOLVABLE_BY_TEST_HARNESS = frozenset(
    {
        # The full 82-entry drop list, computed offline by static analysis
        # of laion/exp_rpt_defects4j-v3-v3 (the algorithm is documented in
        # this file's top docstring). Reproducible: re-run the same
        # imports / unimported-JDK scan against the v3-v3 parquet and you
        # should get exactly this set back. Hermetic: no live HF query at
        # patch-apply time.
        "defects4j-0004",
        "defects4j-0007",
        "defects4j-0008",
        "defects4j-0010",
        "defects4j-0017",
        "defects4j-0019",
        "defects4j-0021",
        "defects4j-0025",
        "defects4j-0026",
        "defects4j-0034",
        "defects4j-0041",
        "defects4j-0043",
        "defects4j-0045",
        "defects4j-0049",
        "defects4j-0051",
        "defects4j-0053",
        "defects4j-0058",
        "defects4j-0071",
        "defects4j-0077",
        "defects4j-0086",
        "defects4j-0088",
        "defects4j-0091",
        "defects4j-0100",
        "defects4j-0104",
        "defects4j-0110",
        "defects4j-0112",
        "defects4j-0122",
        "defects4j-0137",
        "defects4j-0139",
        "defects4j-0142",
        "defects4j-0143",
        "defects4j-0147",
        "defects4j-0150",
        "defects4j-0154",
        "defects4j-0162",
        "defects4j-0163",
        "defects4j-0167",
        "defects4j-0168",
        "defects4j-0173",
        "defects4j-0174",
        "defects4j-0176",
        "defects4j-0183",
        "defects4j-0184",
        "defects4j-0185",
        "defects4j-0187",
        "defects4j-0200",
        "defects4j-0204",
        "defects4j-0213",
        "defects4j-0219",
        "defects4j-0226",
        "defects4j-0228",
        "defects4j-0244",
        "defects4j-0250",
        "defects4j-0252",
        "defects4j-0267",
        "defects4j-0273",
        "defects4j-0289",
        "defects4j-0291",
        "defects4j-0292",
        "defects4j-0298",
        "defects4j-0304",
        "defects4j-0314",
        "defects4j-0317",
        "defects4j-0318",
        "defects4j-0322",
        "defects4j-0331",
        "defects4j-0333",
        "defects4j-0335",
        "defects4j-0340",
        "defects4j-0354",
        "defects4j-0364",
        "defects4j-0367",
        "defects4j-0372",
        "defects4j-0385",
        "defects4j-0387",
        "defects4j-0396",
        "defects4j-0398",
        "defects4j-0401",
        "defects4j-0405",
        "defects4j-0407",
        "defects4j-0420",
        "defects4j-0454",
    }
)


# --------------------------------------------------------------------------- #
# Instruction prefix appended ABOVE the original bug description.
#
# Why this shape:
#   - "ONE shell-command batch": agents under reasoning_effort=medium
#     default to multi-turn diagnose-then-patch plans. State the
#     constraint plainly.
#   - "read /app/Solution.java AND /tests/TestSolution.java": agents
#     in v3-v3 nearly always read /app/Solution.java first but rarely
#     read the test. Reading the test is cheaper than diagnosing the
#     bug from the description and frequently uniquely-determines the
#     fix.
#   - `cat > ... <<'EOF' ... EOF` shape: this is exactly the heredoc
#     idiom the one v3-v3 solve used. Showing it explicitly lifts the
#     prior on attempting it.
#   - `javac /app/Solution.java`: invites the agent to compile-check
#     within its single turn. Won't be required for Gate B (the
#     verifier runs its own javac), but compiling locally lets a
#     well-tuned agent recover from typos within the same batch.
# --------------------------------------------------------------------------- #
_V4_INSTRUCTION_PREFIX = """{marker}

# Java Bug Repair Task — Single-Turn Format

You have ONE turn to fix this bug. Your single response must contain
all of: reading the buggy file, optionally reading the test file, AND
writing the corrected `/app/Solution.java`. Do not plan a multi-step
fix — there is no "next turn".

## Layout
- Buggy code:     `/app/Solution.java`     (already present; you must edit it)
- JUnit test:     `/tests/TestSolution.java`  (read-only; this is what will
  be run against your fix)
- Reference jars: `/junit/junit-platform-console-standalone.jar`
- The classpath at compile/run time is `/app:/tests:/junit/*`. Nothing
  else (no Maven, no third-party libraries).

## Recommended one-turn sequence
Put all of these into the `commands` array of your ONE response:

1. `sed -n '1,200p' /app/Solution.java`           (read the buggy file)
2. `sed -n '1,200p' /tests/TestSolution.java`     (read what's being tested)
3. `cat > /app/Solution.java <<'EOF'` ... your full corrected file ...
   `EOF`                                          (write the fix)
4. `javac -cp /junit/junit-platform-console-standalone.jar /app/Solution.java`
   (sanity-check the syntax — optional but recommended)
5. Set `"task_complete": true` in your response.

You will NOT get a second turn to apply edits, so a successful response
MUST include the `cat > /app/Solution.java <<'EOF' ... EOF` step. The
verifier checks: (a) you edited /app/Solution.java, (b) it compiles
together with the test, (c) all JUnit tests pass.

---

"""


def _build_v4_instruction(original: str) -> str:
    """Prepend the v4 one-shot framing block to the original instruction."""
    prefix = _V4_INSTRUCTION_PREFIX.format(marker=_V4_INSTRUCTION_MARKER)
    return prefix + original.lstrip()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _patch_one_task(task_dir: Path, dry_run: bool) -> str:
    """Patch a single task dir. Returns one of:
        'dropped_unsolvable_test_harness'
        'patched'
        'already_patched'
        'no_instruction'
    `task_dir` may be deleted entirely on the drop path.
    """
    name = task_dir.name
    marker = task_dir / _V4_MARKER_FILE

    if marker.exists():
        return "already_patched"

    if name in _UNSOLVABLE_BY_TEST_HARNESS:
        if not dry_run:
            shutil.rmtree(task_dir, ignore_errors=False)
        return "dropped_unsolvable_test_harness"

    instruction = task_dir / "instruction.md"
    if not instruction.is_file():
        return "no_instruction"

    text = instruction.read_text(encoding="utf-8", errors="replace")
    if _V4_INSTRUCTION_MARKER in text:
        if not dry_run:
            marker.write_text(
                "laion v4 patch: one-shot framing + drop broken test fixtures\n",
                encoding="utf-8",
            )
        return "already_patched"

    new_text = _build_v4_instruction(text)
    if not dry_run:
        instruction.write_text(new_text, encoding="utf-8")
        marker.write_text(
            "laion v4 patch: one-shot framing + drop broken test fixtures\n",
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

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts: dict[str, int] = {}
    dropped_names: list[str] = []

    for i, td in enumerate(task_dirs, 1):
        result = _patch_one_task(td, dry_run=args.dry_run)
        counts[result] = counts.get(result, 0) + 1
        if result == "dropped_unsolvable_test_harness":
            dropped_names.append(td.name)

        if i % 100 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] "
                f"patched={counts.get('patched', 0)} "
                f"dropped={counts.get('dropped_unsolvable_test_harness', 0)} "
                f"already={counts.get('already_patched', 0)} "
                f"no_instruction={counts.get('no_instruction', 0)}",
                flush=True,
            )

    if not args.dry_run:
        report = root / _V4_REPORT_FILENAME
        with report.open("w", encoding="utf-8") as f:
            f.write("laion exp_rpt_defects4j-v3-v3 -> v3-v4 patch report\n")
            f.write(f"total_task_dirs_seen = {n_total}\n")
            for k in sorted(counts):
                f.write(f"{k} = {counts[k]}\n")
            f.write(
                "\n# Dropped (TestSolution.java doesn't compile in /app:/tests:/junit/* classpath):\n"
            )
            for name in dropped_names:
                f.write(name + "\n")

    print(
        f"\nDone. total={n_total} "
        f"patched={counts.get('patched', 0)} "
        f"dropped={counts.get('dropped_unsolvable_test_harness', 0)} "
        f"already_patched={counts.get('already_patched', 0)} "
        f"no_instruction={counts.get('no_instruction', 0)} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
