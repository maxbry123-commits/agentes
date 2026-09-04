#!/usr/bin/env python3
"""
Patch DCAgent/mix_h1_struggle_zone tasks whose `bugsinpy_mf-*` source ships
a Dockerfile that fails the image build.

Bug (200/200 QC pass on 2026-05-14)
-----------------------------------
The reported headline metrics were 194/200 infra-ok (0.970) and 52/200
solved (0.260). All 6 infra failures come from the same source dataset:
`bugsinpy_mf-*` (a multi-fault Python debugging family with 100 tasks
total in the mixture). Every bugsinpy_mf task ships this Dockerfile::

    FROM python:3.10-slim
    WORKDIR /app
    RUN mkdir -p /output && chmod 777 /output
    RUN pip install --no-cache-dir pytest

    # Copy buggy starter code into /app
    COPY solution.py /app/solution.py

…but the task tarball does NOT contain a `solution.py` (or
`environment/solution.py`). Docker build fails with
`COPY failed: file not found in build context`. Only 6 of the 100
bugsinpy_mf tasks were sampled by the 200-task validation run; all 6
failed. The full 3116-task mixture is contaminated with 100 broken
bugsinpy_mf tasks that can NEVER complete infra.

The test.sh already has the right fallback behaviour ("if the agent
didn't create solution.py, copy the first .py in /app to it") and the
instruction.md tells the agent: "fix all bugs in /app/solution.py …
tests will automatically verify your fixes through `from solution
import *`". For the multi-fault family the agent is expected to write
the solution from scratch (the buggy code is described in prose in
instruction.md — no source file is shipped). The only thing the
Dockerfile needs to do is succeed at build time so the trial container
boots; the test.sh fallback handles the rest at runtime.

Fix
---
For every task whose `metadata.json` source starts with `bugsinpy_mf-`,
rewrite `environment/Dockerfile` to drop the `COPY solution.py …` line
and replace it with `RUN touch /app/solution.py` so the build succeeds
and a (zero-byte) `/app/solution.py` exists for the import fallback to
reference. Idempotent via marker.

Snapshot impact
---------------
All 100 bugsinpy_mf tasks share a byte-identical Dockerfile. Patching
them with the same identical replacement keeps the environment hash
collision, so Daytona snapshot count for this family stays at 1 (vs the
pre-patch 1). Total unique env hashes for the whole 3116-task mixture
stays at 6 — well below the 10 / 60 caps.

Usage
-----
    python -m data.patchers.patch_mix_h1_struggle_zone_tasks --root <dir>
    python -m data.patchers.patch_mix_h1_struggle_zone_tasks --root <dir> --dry-run
    python -m data.patchers.patch_mix_h1_struggle_zone_tasks --root <dir> --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent


PATCH_MARKER = "# --- laion v2 patch: bugsinpy_mf solution stub ---"


NEW_DOCKERFILE = dedent(
    f"""\
    FROM python:3.10-slim
    WORKDIR /app
    RUN mkdir -p /output && chmod 777 /output
    RUN pip install --no-cache-dir pytest

    {PATCH_MARKER}
    # Original Dockerfile did `COPY solution.py /app/solution.py` but the
    # task tarball doesn't ship one, breaking the build. The test.sh has
    # a runtime fallback that copies the first /app/*.py to solution.py
    # if the agent didn't create one; we just need a non-failing build
    # plus a placeholder file so `from solution import *` doesn't crash
    # before the fallback runs.
    RUN touch /app/solution.py
    """
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


def patch_task(task_dir: Path, dry_run: bool = False) -> dict:
    """Patch a single task. Returns {'status': ..., 'reason': ...}."""
    source = _task_source(task_dir)
    if source is None:
        return {"status": "skipped_no_metadata", "reason": "no metadata.json"}
    if not source.startswith("bugsinpy_mf"):
        return {"status": "skipped_other_source", "reason": f"source={source}"}

    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.is_file():
        return {
            "status": "skipped_no_dockerfile",
            "reason": "no environment/Dockerfile",
        }

    existing = dockerfile.read_text(encoding="utf-8", errors="replace")
    if PATCH_MARKER in existing:
        return {"status": "skipped_already_patched", "reason": "marker present"}

    # Sanity check: confirm the broken `COPY solution.py` line is what we
    # expect. We still rewrite if it isn't (the replacement is a
    # self-contained, correct Dockerfile for this task family), but flag
    # it so unusual variants are visible in the summary.
    is_expected = "COPY solution.py" in existing

    if not dry_run:
        dockerfile.write_text(NEW_DOCKERFILE, encoding="utf-8")
    return {
        "status": "patched" if is_expected else "patched_unusual",
        "reason": "ok" if is_expected else "no COPY solution.py line in original",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Patch bugsinpy_mf tasks in DCAgent/mix_h1_struggle_zone so their "
            "environment/Dockerfile builds (the original `COPY solution.py` "
            "line references a file that isn't in the tarball)."
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
        help="Stop after processing N task directories (default: all).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change; write nothing.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"[patcher] --root not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(p for p in root.iterdir() if p.is_dir())
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
        examples.setdefault(status, td.name)

    print("\n[patcher] Result summary:")
    for status, count in sorted(counters.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")
    print(f"\n[patcher] Root: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
