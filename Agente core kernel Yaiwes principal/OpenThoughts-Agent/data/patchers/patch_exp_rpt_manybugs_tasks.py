#!/usr/bin/env python3
"""
Patch every DCAgent/exp_rpt_manybugs task tree so the agent can actually edit
the buggy C file *and* the instruction tells the agent the correct filename
and location.

The bugs (164/164 QC pass: 142 infra-ok, 0 solved)
--------------------------------------------------

Two distinct authoring bugs accounted for 100% of the 0/164 solves on the
unpatched corpus:

1. **Workspace not seeded (164/164 = 100%)** — every task's
   ``environment/Dockerfile`` ends with ``RUN mkdir -p /logs/verifier /tests``
   and never seeds the buggy C source into ``/workspace/src/<file>.c``. When
   the agent starts, ``ls -la /workspace`` is ``total 0`` and any attempt to
   edit ``/workspace/src/<file>.c`` fails with ``No such file or directory``.
   The verifier (``tests/test.sh``) has a defensive fallback that copies
   ``/tests/initial/<file>.c`` into ``/workspace/src/<file>.c`` if it is
   missing — so the file present at verify time is identical to the buggy
   version, and the very first verifier check (``diff -q ... /tests/buggy/``)
   prints ``FAIL: File is identical to the buggy version - no fix applied``.
   Every infra-OK trial in QC hits exactly this stdout.

2. **Filename mismatch in instruction.md (61/164 ≈ 37%)** — instruction.md
   tells the agent to edit ``/workspace/src/<wrong>.c`` while the verifier
   actually checks ``/workspace/src/<right>.c`` (the file under
   ``tests/initial/``, which is the canonical name). Even if the agent does
   edit the file named in the instruction, the verifier looks at a different
   path and reports no fix applied.

Per-task patches
----------------

We deliberately do NOT modify ``environment/Dockerfile`` or stage the buggy
source under ``environment/``. Harbor's Daytona auto-snapshot hashes
``environment_dir/**``, so adding per-task content to ``environment/`` would
explode the 7-snapshot baseline into 160+ unique snapshots (over the hard
``max_org_snapshots=60`` cap). Instead we use Harbor's runtime fixture
mechanism: ``setup_files/`` is uploaded to ``/setup_files`` inside the
container *after* environment build but *before* the agent runs. It does NOT
contribute to the snapshot hash.

A) **setup_files/src/<file>.c**: copy the buggy initial source from
   ``tests/initial/<file>.c`` into ``setup_files/src/<file>.c`` so it appears
   at ``/setup_files/src/<file>.c`` inside the container before the agent
   starts. Snapshot impact: 0 (setup_files is not part of the build context).

B) **instruction.md**: replace the body with an explicit two-step
   instruction that

     1. tells the agent the buggy file is staged at
        ``/setup_files/src/<canonical>.c``, and
     2. instructs them to copy it to ``/workspace/src/<canonical>.c`` and fix
        the bug in place there (since the verifier reads
        ``/workspace/src/<canonical>.c``).

   The instruction preserves the original task summary, symptoms text, and
   "minimal change" guidance, but corrects the filename references AND adds
   the staging hint at the top, behind the marker
   ``<!-- laion v2 patch: manybugs setup_files instruction -->``.

Idempotency
-----------
- ``setup_files/src/<file>.c``: skipped if it already exists with identical
  bytes to ``tests/initial/<file>.c``.
- ``instruction.md``: skipped if the
  ``<!-- laion v2 patch: manybugs setup_files instruction -->`` marker is
  present.

Counters
--------
- ``patched`` — both setup_files seeded AND instruction rewritten.
- ``skipped_already_patched`` — marker present AND setup_files in sync.
- ``skipped_no_initial`` — ``tests/initial/<file>.c`` is missing (drop).
- ``skipped_no_dockerfile`` — no environment/Dockerfile (drop).

Snapshot impact
---------------
0 new snapshots. ``setup_files/`` is uploaded at runtime and not hashed into
the snapshot identity. The unpatched dataset produces 7 snapshots (one per
program family — gmp, libtiff, python, php, lighttpd, wireshark, etc.); the
patched dataset also produces 7.

Usage::

    python -m data.patchers.patch_exp_rpt_manybugs_tasks \
        --root /tmp/manybugs_extracted

    # Dry run (count only, write nothing)
    python -m data.patchers.patch_exp_rpt_manybugs_tasks \
        --root /tmp/manybugs_extracted --dry-run

    # Process only the first 5 tasks (for smoke-testing)
    python -m data.patchers.patch_exp_rpt_manybugs_tasks \
        --root /tmp/manybugs_extracted --limit 5
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Patch markers
# ---------------------------------------------------------------------------

INSTRUCTION_MARKER = "<!-- laion v2 patch: manybugs setup_files instruction -->"


# Match a filename reference in the original instruction.md so we can preserve
# the program description while substituting the canonical filename.
_INSTR_PATH_RE = re.compile(r"/workspace/src/([A-Za-z0-9_.\-]+\.c)")
_INSTR_BARE_RE = re.compile(r"`([A-Za-z0-9_.\-]+\.c)`")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _canonical_source_name(task_dir: Path) -> str | None:
    """Return the filename under ``tests/initial/`` (the canonical name).

    The unpatched dataset has exactly one .c file in tests/initial/ per task.
    We prefer the lexicographically first one for determinism in the unlikely
    event of multiple .c files.
    """
    initial_dir = task_dir / "tests" / "initial"
    if not initial_dir.is_dir():
        return None
    candidates = [p for p in initial_dir.iterdir() if p.is_file() and p.suffix == ".c"]
    if not candidates:
        return None
    return sorted(p.name for p in candidates)[0]


def _build_instruction(original_text: str, canonical: str) -> str:
    """Build a patched instruction.md body.

    Strategy: prepend a fixed preamble that names the canonical file path and
    explains the setup_files staging convention; then keep the original
    instruction body with any filename references rewritten to ``canonical``.

    The preamble is the load-bearing part — it tells the agent (a) the file
    is staged at ``/setup_files/src/<canonical>``, (b) they must copy it into
    ``/workspace/src/<canonical>`` first, and (c) the verifier reads from
    ``/workspace/src/<canonical>``. The original text below the preamble is
    preserved (with filename references corrected) so the agent still gets
    the symptom description and line-number hint.
    """
    preamble = dedent(
        f"""\
        # Setup

        The buggy source file is staged inside the container at
        ``/setup_files/src/{canonical}``. Before you start editing, copy it
        into the workspace where the verifier will read it:

        ```bash
        mkdir -p /workspace/src
        cp /setup_files/src/{canonical} /workspace/src/{canonical}
        ```

        After fixing the bug, the verifier compares ``/workspace/src/{canonical}``
        against the known-buggy and known-fixed reference files. Make sure
        your fix lives at ``/workspace/src/{canonical}``.

        ---

        """
    )

    body = original_text
    body = _INSTR_PATH_RE.sub(f"/workspace/src/{canonical}", body)
    body = _INSTR_BARE_RE.sub(f"`{canonical}`", body)

    text = preamble + body
    if not text.endswith("\n"):
        text = text + "\n"
    text = text + INSTRUCTION_MARKER + "\n"
    return text


# ---------------------------------------------------------------------------
# Per-task driver
# ---------------------------------------------------------------------------


def patch_task(task_dir: Path, dry_run: bool = False) -> dict:
    """Patch a single task. Returns ``{"status": ..., "reason": ..., ...}``."""
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.exists():
        return {
            "status": "skipped_no_dockerfile",
            "reason": "no environment/Dockerfile",
        }

    canonical = _canonical_source_name(task_dir)
    if canonical is None:
        return {"status": "skipped_no_initial", "reason": "no tests/initial/*.c"}

    initial_path = task_dir / "tests" / "initial" / canonical
    if not initial_path.is_file():
        return {
            "status": "skipped_no_initial",
            "reason": "tests/initial/<file>.c not a file",
        }

    initial_bytes = initial_path.read_bytes()

    setup_files_dir = task_dir / "setup_files" / "src"
    setup_path = setup_files_dir / canonical
    seed_in_sync = setup_path.exists() and setup_path.read_bytes() == initial_bytes

    instr_path = task_dir / "instruction.md"
    instr_already_patched = False
    new_instr = None
    if instr_path.exists():
        instr_text = instr_path.read_text()
        if INSTRUCTION_MARKER in instr_text:
            instr_already_patched = True
        else:
            new_instr = _build_instruction(instr_text, canonical)

    if seed_in_sync and instr_already_patched:
        return {
            "status": "skipped_already_patched",
            "reason": "marker present + seed in sync",
        }

    if dry_run:
        return {
            "status": "would_patch",
            "reason": "dry-run",
            "seed_changed": not seed_in_sync,
            "instruction_changed": new_instr is not None,
        }

    if not seed_in_sync:
        setup_files_dir.mkdir(parents=True, exist_ok=True)
        setup_path.write_bytes(initial_bytes)

    if new_instr is not None:
        instr_path.write_text(new_instr)

    return {"status": "patched", "reason": "ok"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Patch DCAgent/exp_rpt_manybugs tasks so the buggy C file is "
            "staged in setup_files/ and the instruction.md tells the agent "
            "the correct filename and where to copy it from."
        ),
    )
    p.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing extracted manybugs-* task directories.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after processing N tasks (default: all).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change; write nothing.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        raise SystemExit(f"[patcher] --root not a directory: {root}")

    task_dirs = sorted(
        p for p in root.iterdir() if p.is_dir() and (p / "environment").exists()
    )
    if args.limit is not None:
        task_dirs = task_dirs[: args.limit]

    print(f"[patcher] Found {len(task_dirs)} task directories under {root}")
    if args.dry_run:
        print("[patcher] DRY RUN - no files will be written")

    counters: dict[str, int] = {}
    examples: dict[str, str] = {}
    for td in task_dirs:
        result = patch_task(td, dry_run=args.dry_run)
        status = result["status"]
        counters[status] = counters.get(status, 0) + 1
        if status not in examples:
            examples[status] = td.name

    print("\n[patcher] Result summary:")
    for status, count in sorted(counters.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:32s}  (e.g. {ex})")
    print(f"\n[patcher] Root: {root}")


if __name__ == "__main__":
    main()
