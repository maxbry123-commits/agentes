#!/usr/bin/env python3
"""
Patch arteemg/logsmith-500-patched tasks to seed their per-task data into
``/workspace/data/`` at container build time.

Background (from a 200/500 QC pass): every task ships its kv-token log files,
decoy noise files, and ``manifest.txt`` under ``setup_files/data/`` (~1.4 MB
per task). The original Dockerfile assumed Harbor would copy
``setup_files/data/`` into ``/workspace/data/`` at container start, but Harbor
only mounts ``/setup_files/`` inside the container — it does NOT auto-copy
the contents to ``/workspace``. At runtime every agent's ``ls -la /workspace``
returns ``total 0``, the solution pipeline reads non-existent files, and the
verifier reports either "missing output file", "missing input file:
data/decoys/noise_<TOKEN>", or "output is empty". 0/500 of the tasks solved.

This patcher adds a defensive ``COPY setup_files/data /workspace/data`` block
to every task's ``environment/Dockerfile``, with a chown to the ``agent`` user
when one exists. Since this is the same identical block appended to every
Dockerfile, the build-context hash continues to collide across tasks (or at
worst lands on the same hash for all 500) and the Daytona snapshot count
stays at 1.

Idempotency: each Dockerfile is scanned for the marker
``# --- laion v2 patch: logsmith data seeding ---`` and skipped if already
present.

Tasks without ``setup_files/data/`` are reported as ``skipped_no_seed_data``
and left untouched.

Usage::

    python -m data.patchers.patch_logsmith_tasks \
        --root /tmp/logsmith_src

    # Dry run (count only, write nothing)
    python -m data.patchers.patch_logsmith_tasks \
        --root /tmp/logsmith_src --dry-run

    # Process only the first 5 tasks (for smoke-testing)
    python -m data.patchers.patch_logsmith_tasks \
        --root /tmp/logsmith_src --limit 5
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Patch block
# ---------------------------------------------------------------------------

PATCH_MARKER = "# --- laion v2 patch: logsmith data seeding ---"

# The defensive seed-data block. We COPY into a staging directory and `cp -a`
# the contents into /workspace/data so the destination ends up at
# /workspace/data/decoys/... and /workspace/data/logs/... (matching what the
# verifier expects). The chown is conditional so the block is safe even on
# Dockerfiles that never created an `agent` user.
PATCH_BLOCK = dedent(
    f"""\
    {PATCH_MARKER}
    COPY setup_files/data /tmp/seed_data
    RUN mkdir -p /workspace/data \\
        && cp -a /tmp/seed_data/. /workspace/data/ \\
        && rm -rf /tmp/seed_data \\
        && (id -u agent >/dev/null 2>&1 && chown -R agent:agent /workspace/data || true)
    """
)


# Match a USER directive that switches away from root. Matches lines like
# ``USER agent``, ``USER 1000``, ``USER agent:agent``, etc., but not
# ``USER root`` (which is a no-op we don't need to step in front of).
_USER_LINE_RE = re.compile(r"^\s*USER\s+(?!root\b)(\S+)", re.MULTILINE)


def _patch_dockerfile_text(text: str) -> str | None:
    """Return the patched Dockerfile text, or ``None`` if already patched.

    The patch block is inserted *before* the first non-root ``USER`` line so
    the ``COPY``/``RUN`` execute as root. If no non-root USER line exists,
    the block is appended at the end.
    """
    if PATCH_MARKER in text:
        return None

    # Ensure trailing newline so our block lands on its own line.
    if not text.endswith("\n"):
        text = text + "\n"

    m = _USER_LINE_RE.search(text)
    if m is None:
        # No non-root USER directive — append at the end of the file.
        return text + "\n" + PATCH_BLOCK

    insert_at = m.start()
    return text[:insert_at] + PATCH_BLOCK + "\n" + text[insert_at:]


# ---------------------------------------------------------------------------
# Per-task driver
# ---------------------------------------------------------------------------


def patch_task(task_dir: Path, dry_run: bool = False) -> dict:
    """Patch a single task. Returns ``{"status": ..., "reason": ...}``."""
    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.exists():
        return {
            "status": "skipped_no_dockerfile",
            "reason": "no environment/Dockerfile",
        }

    seed_data = task_dir / "setup_files" / "data"
    if not seed_data.is_dir():
        return {"status": "skipped_no_seed_data", "reason": "no setup_files/data/"}

    original = dockerfile.read_text()
    patched = _patch_dockerfile_text(original)
    if patched is None:
        return {"status": "skipped_already_patched", "reason": "marker present"}

    if dry_run:
        return {"status": "would_patch", "reason": "dry-run"}

    dockerfile.write_text(patched)
    return {"status": "patched", "reason": "ok"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Patch logsmith-500-patched task Dockerfiles to seed /workspace/data/.",
    )
    p.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing extracted task_* directories.",
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
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")
    print(f"\n[patcher] Root: {root}")


if __name__ == "__main__":
    main()
