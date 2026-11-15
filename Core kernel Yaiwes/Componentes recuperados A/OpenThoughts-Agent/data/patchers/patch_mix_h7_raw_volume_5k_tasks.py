#!/usr/bin/env python3
"""
Patch ``DCAgent/mix_h7_raw_volume_5k`` tasks for the missing ``solution.py``
bug that affects every ``bugsinpy_mf-*`` source task in the mixture.

Background (QC pass, 200 trials → 23 infra failures, 0.885 infra-ok):
  All 23 infra failures are bugsinpy_mf tasks. Each bugsinpy_mf task ships an
  ``environment/Dockerfile`` that ends with:

      COPY solution.py /app/solution.py

  ...but the per-task ``environment/solution.py`` file (which holds the buggy
  code the agent is meant to debug) is **missing from the mix dataset**.
  The upstream source ``DCAgent/exp_rpt_bugsinpy-mf-large`` has it, but the
  mixture step dropped it. Daytona refuses to build the image because the
  COPY source doesn't exist, producing:

      Failed to create sandbox: Path does not exist:
      .../mix-h7-raw-volume-*/environment/solution.py

Fix:
  1. Re-fetch ``environment/solution.py`` from
     ``DCAgent/exp_rpt_bugsinpy-mf-large`` (indexed by metadata.json's
     ``source`` field, e.g. ``bugsinpy_mf-0094``).
  2. Write it to ``setup_files/solution.py`` (NOT back into ``environment/``)
     — Harbor mounts ``setup_files/`` at ``/setup_files`` in the container
     before the agent runs, and files there do NOT contribute to the
     environment-hash → snapshot identity stays uniform across all 333
     bugsinpy_mf tasks.
  3. Strip ``COPY solution.py /app/solution.py`` from the Dockerfile so
     the build no longer requires the file. The Dockerfile becomes
     byte-identical across all bugsinpy_mf tasks → 1 snapshot, not 333.
  4. Prepend ``tests/test.sh`` with a copy-from-setup-files fallback so the
     verifier runs against the right code even if the agent left
     ``/app/solution.py`` missing.
  5. Append a pointer to ``/setup_files/solution.py`` to ``instruction.md``
     so the agent knows where the buggy code lives.

Snapshot accounting (Daytona caps: max_new_snapshots=10, max_org_snapshots=60):
  After the patch, all 333 bugsinpy_mf tasks share the same Dockerfile and
  byte-identical (empty) environment/ fixtures → exactly 1 snapshot for the
  whole bugsinpy_mf slice. The other source slices in the mix (codereval,
  stack, pymethods2test, ...) are unaffected. We do not increase the total
  snapshot count, and we don't add any per-task fixture files to
  ``environment/``.

Idempotency:
  Each Dockerfile carries the marker
  ``# --- laion v2 patch: mix_h7 bugsinpy_mf solution-relocation ---``
  near the top. Tasks that already have the marker are skipped.

Tasks whose ``metadata.json`` does NOT have a ``bugsinpy_mf-*`` source are
reported as ``skipped_not_bugsinpy_mf`` and left untouched.

Tasks whose source ID is missing from the upstream source dataset are
reported as ``skipped_no_source_solution``.

Usage::

    python -m data.patchers.patch_mix_h7_raw_volume_5k_tasks \\
        --root /tmp/mix_h7_src

    # Dry run (count only, write nothing)
    python -m data.patchers.patch_mix_h7_raw_volume_5k_tasks \\
        --root /tmp/mix_h7_src --dry-run

    # Process only the first 5 tasks (for smoke-testing)
    python -m data.patchers.patch_mix_h7_raw_volume_5k_tasks \\
        --root /tmp/mix_h7_src --limit 5
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tarfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Marker / constants
# ---------------------------------------------------------------------------

PATCH_MARKER = "# --- laion v2 patch: mix_h7 bugsinpy_mf solution-relocation ---"

# The upstream dataset that still contains environment/solution.py for every
# bugsinpy_mf-* task. Loaded once on first use.
SOURCE_DATASET = "DCAgent/exp_rpt_bugsinpy-mf-large"

# Regex that matches the COPY line we want to remove. Whitespace tolerant.
_COPY_SOLUTION_RE = re.compile(
    r"^\s*COPY\s+solution\.py\s+/app/solution\.py\s*$",
    re.MULTILINE,
)

# What we prepend to test.sh (kept short so it's diff-friendly).
TEST_SH_SHIM = (
    "# --- laion v2 patch: pull solution.py from /setup_files if /app/solution.py missing ---\n"
    "if [ ! -f /app/solution.py ] && [ -f /setup_files/solution.py ]; then\n"
    "    cp /setup_files/solution.py /app/solution.py\n"
    "fi\n"
)

# Appended to instruction.md to tell the agent where the buggy code is.
INSTRUCTION_NOTE = (
    "\n\n---\n"
    "**Note (env layout):** The buggy starter code is at "
    "`/setup_files/solution.py`. The verifier and tests run against "
    "`/app/solution.py`. Read `/setup_files/solution.py`, fix the bugs, and "
    "write the corrected version to `/app/solution.py`.\n"
)


# ---------------------------------------------------------------------------
# Source-dataset lookup (lazy)
# ---------------------------------------------------------------------------

_SOURCE_INDEX: dict[str, bytes] | None = None


def _load_source_index() -> dict[str, bytes]:
    """Return a dict mapping ``bugsinpy_mf-NNNN`` → ``solution.py`` bytes.

    Loads the upstream dataset on first call, extracts the
    ``environment/solution.py`` blob out of each task's tar archive, and
    caches the result in module state.
    """
    global _SOURCE_INDEX
    if _SOURCE_INDEX is not None:
        return _SOURCE_INDEX

    try:
        from datasets import load_dataset
    except ImportError as e:
        raise SystemExit(
            "[patcher] `datasets` library required to fetch upstream solution.py"
        ) from e

    print(f"[patcher] Loading source dataset {SOURCE_DATASET} ...", flush=True)
    ds = load_dataset(SOURCE_DATASET, split="train")
    index: dict[str, bytes] = {}
    for row in ds:
        path = row.get("path", "")
        tb = row.get("task_binary")
        if not path or tb is None:
            continue
        try:
            buf = io.BytesIO(tb)
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                m = None
                for member in tar.getmembers():
                    if member.name == "environment/solution.py":
                        m = member
                        break
                if m is None:
                    continue
                f = tar.extractfile(m)
                if f is None:
                    continue
                index[path] = f.read()
        except Exception as exc:
            print(f"[patcher]   warn: could not extract {path}: {exc}", file=sys.stderr)

    print(
        f"[patcher] Source index built: {len(index)} bugsinpy_mf solutions", flush=True
    )
    _SOURCE_INDEX = index
    return index


# ---------------------------------------------------------------------------
# Per-task driver
# ---------------------------------------------------------------------------


def _read_metadata_source(task_dir: Path) -> str | None:
    md_path = task_dir / "metadata.json"
    if not md_path.exists():
        return None
    try:
        md = json.loads(md_path.read_text())
    except Exception:
        return None
    src = md.get("source", "")
    if isinstance(src, str) and src.startswith("bugsinpy_mf-"):
        return src
    return None


def patch_task(
    task_dir: Path, source_index: dict[str, bytes], dry_run: bool = False
) -> dict:
    """Patch a single task. Returns ``{"status": ..., "reason": ...}``."""
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.exists():
        return {
            "status": "skipped_no_dockerfile",
            "reason": "no environment/Dockerfile",
        }

    # Idempotency check first — cheap and lets us short-circuit re-runs.
    dockerfile_text = dockerfile.read_text()
    if PATCH_MARKER in dockerfile_text:
        return {"status": "skipped_already_patched", "reason": "marker present"}

    source_id = _read_metadata_source(task_dir)
    if source_id is None:
        return {
            "status": "skipped_not_bugsinpy_mf",
            "reason": "source not bugsinpy_mf-*",
        }

    solution_bytes = source_index.get(source_id)
    if solution_bytes is None:
        return {
            "status": "skipped_no_source_solution",
            "reason": f"{source_id} not in upstream source dataset",
        }

    test_sh = task_dir / "tests" / "test.sh"
    instruction = task_dir / "instruction.md"
    setup_files_dir = task_dir / "setup_files"
    setup_files_solution = setup_files_dir / "solution.py"

    # ---- compute the new Dockerfile text (strip COPY + add marker) ----
    # Strip the offending COPY line.
    new_dockerfile = _COPY_SOLUTION_RE.sub("", dockerfile_text)
    # Collapse double-blank-lines the strip may have left behind.
    new_dockerfile = re.sub(r"\n{3,}", "\n\n", new_dockerfile)
    # Prepend marker as a comment so we can detect re-runs.
    if not new_dockerfile.endswith("\n"):
        new_dockerfile += "\n"
    new_dockerfile = f"{PATCH_MARKER}\n{new_dockerfile}"

    # ---- compute the new test.sh text (prepend shim) ----
    new_test_sh: str | None = None
    if test_sh.exists():
        original_test_sh = test_sh.read_text()
        if (
            PATCH_MARKER not in original_test_sh
            and TEST_SH_SHIM not in original_test_sh
        ):
            # Try to insert after the shebang so `set -e` etc. still come early.
            lines = original_test_sh.splitlines(keepends=True)
            if lines and lines[0].startswith("#!"):
                new_test_sh = lines[0] + TEST_SH_SHIM + "".join(lines[1:])
            else:
                new_test_sh = TEST_SH_SHIM + original_test_sh

    # ---- compute the new instruction.md text (append pointer) ----
    new_instruction: str | None = None
    if instruction.exists():
        original_instruction = instruction.read_text()
        if "/setup_files/solution.py" not in original_instruction:
            new_instruction = original_instruction.rstrip() + INSTRUCTION_NOTE

    if dry_run:
        return {"status": "would_patch", "reason": f"source={source_id}"}

    # ---- write everything ----
    setup_files_dir.mkdir(exist_ok=True)
    setup_files_solution.write_bytes(solution_bytes)
    dockerfile.write_text(new_dockerfile)
    if new_test_sh is not None:
        test_sh.write_text(new_test_sh)
    if new_instruction is not None:
        instruction.write_text(new_instruction)

    return {"status": "patched", "reason": f"source={source_id}"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Patch DCAgent/mix_h7_raw_volume_5k task dirs to restore the missing "
            "bugsinpy_mf solution.py via setup_files/ (preserves snapshot identity)."
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
        print("[patcher] DRY RUN — no files will be written")

    # Cheap pre-scan: skip the (expensive) source dataset load if there's no
    # bugsinpy_mf task in this batch.
    needs_source = any(_read_metadata_source(td) is not None for td in task_dirs)
    if needs_source:
        source_index = _load_source_index()
    else:
        source_index = {}
        print("[patcher] No bugsinpy_mf tasks in batch; skipping source dataset load.")

    counters: dict[str, int] = {}
    examples: dict[str, str] = {}
    for td in task_dirs:
        result = patch_task(td, source_index, dry_run=args.dry_run)
        status = result["status"]
        counters[status] = counters.get(status, 0) + 1
        if status not in examples:
            examples[status] = f"{td.name} ({result['reason']})"

    print("\n[patcher] Result summary:")
    for status, count in sorted(counters.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")
    print(f"\n[patcher] Root: {root}")


if __name__ == "__main__":
    main()
