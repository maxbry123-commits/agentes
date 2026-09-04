#!/usr/bin/env python3
"""
Patch laion/logsmith-500-patched-v2 tasks into v3.

Root cause of the v2 0% infra-ok regression
============================================

v2 added the following block to every task's ``environment/Dockerfile``:

    # --- laion v2 patch: logsmith data seeding ---
    COPY setup_files/data /tmp/seed_data
    RUN mkdir -p /workspace/data && cp -a /tmp/seed_data/. /workspace/data/ ...

The intent was to seed the kv-token logs / decoys / manifest from
``setup_files/data/`` into ``/workspace/data/`` so the verifier's input-hash
check would pass.

Why v2 was catastrophic:

  1. Daytona's ``Image.from_dockerfile()`` parses every ``COPY`` source and
     uploads it as part of the build context (``process_image_context``). The
     path it resolves is ``<dockerfile_dir>/<source>`` = ``environment/setup_files/data``.
     But in this dataset's layout ``setup_files/`` lives at the *task root*, NOT
     under ``environment/``. Result: every task fails sandbox build with
     ``FileNotFoundError: Path does not exist: .../task_NNN/environment/setup_files/data``.
     Confirmed in 200/200 traces of the v2 eval run.

  2. Even if we moved ``setup_files/data/`` into ``environment/`` so the COPY
     could find it, every task's environment-dir hash would diverge (each task
     has unique log content, ~1.4 MB unique per task), producing 500 distinct
     Daytona snapshots and instantly busting the 10/dataset and 60/org snapshot
     caps.

The v2 author's claim that "the same identical block appended to every
Dockerfile" would keep build-context hashes colliding was wrong; the hash
includes the COPY *source* content (the unique per-task data), not just the
Dockerfile text.

v3 fix
======

Drop the build-time COPY entirely. Replace it with an identical-across-tasks
build-time symlink:

    # --- laion v3 patch: workspace data symlink ---
    RUN ln -s /setup_files/data /workspace/data

Reasoning:
  - The symlink target (``/setup_files/data``) doesn't exist at image-build
    time; that's fine — Linux allows dangling symlinks. Harbor's runtime
    ``_upload_setup_files`` uploads ``setup_files/data/...`` into
    ``/setup_files/data/...`` BEFORE the agent runs (see
    ``harbor/src/harbor/trial/trial.py:996`` calling
    ``_upload_setup_files`` immediately after ``_setup_environment``), so by
    the time the agent reads ``/workspace/data/logs/foo.log`` the symlink
    resolves into the populated upload target.
  - The Dockerfile mutation is BYTE-FOR-BYTE identical across all 500 tasks
    (single ``RUN ln -s`` line, no per-task data). Combined with the fact
    that the unpatched Dockerfiles are also identical (verified: all 500
    SHA256-collide on the same content), the patched environment_dir is
    identical → exactly 1 Daytona snapshot for the whole dataset → stays
    safely under the 10/dataset + 60/org cap.
  - test.sh keeps ``ROOT=/workspace`` and reads ``$ROOT/data/decoys/...``;
    the bash test ``[[ -L "$full" ]]`` checks whether the full path is itself
    a symlink, not whether any intermediate component is. ``/workspace/data``
    is a symlink but ``/workspace/data/logs/foo.log`` is a regular file (the
    file lives in the resolved ``/setup_files/data/`` target), so the verifier's
    "input is a symlink" guard does not trip.
  - instruction.md unchanged — agent still sees the data under
    ``/workspace/data/`` via the transparent symlink, exactly as the prompt
    describes.

The patcher additionally STRIPS the broken v2 patch block from every
Dockerfile (idempotent — if v2 marker is absent, the strip is a no-op). Both
the strip and the symlink-add are gated by a v3 marker so re-runs no-op.

Tasks without ``setup_files/data/`` are reported as ``skipped_no_seed_data``
and left untouched.

Usage
=====
    python data/patchers/patch_logsmith_v3_tasks.py --root /tmp/logsmith_src
    python data/patchers/patch_logsmith_v3_tasks.py --root /tmp/logsmith_src --dry-run
    python data/patchers/patch_logsmith_v3_tasks.py --root /tmp/logsmith_src --limit 5
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

V2_PATCH_MARKER = "# --- laion v2 patch: logsmith data seeding ---"
V3_PATCH_MARKER = "# --- laion v3 patch: workspace data symlink ---"

# Identical-across-tasks block. NO COPY → no per-task build context → all
# 500 Dockerfiles SHA256-collide → 1 Daytona snapshot per dataset.
V3_PATCH_BLOCK = dedent(
    f"""\
    {V3_PATCH_MARKER}
    # Symlink /workspace/data -> /setup_files/data so Harbor's runtime upload
    # of setup_files/ populates the location the agent and verifier expect at
    # /workspace/data/. Created BEFORE the USER directive so the symlink is
    # owned by root; the target dir /setup_files is chmod 777 by the base
    # Dockerfile so the agent can read its contents.
    RUN ln -s /setup_files/data /workspace/data
    """
)

# Matches the entire v2 patch block (marker + COPY line + RUN ... multi-line
# continuation through the trailing chown). The original v2 block ends with
# the line containing ``chown -R agent:agent /workspace/data || true)`` and
# is followed by a blank line, then ``USER agent`` (or end of file).
#
# We anchor on the marker and consume up to and including the closing
# parenthesis on the chown line. The DOTALL flag lets ``.`` match newlines
# inside the RUN continuation.
_V2_BLOCK_RE = re.compile(
    re.escape(V2_PATCH_MARKER)
    + r".*?chown -R agent:agent /workspace/data \|\| true\)\s*\n",
    re.DOTALL,
)

# A non-root USER directive (we insert the v3 block *before* it so the symlink
# runs as root).
_USER_LINE_RE = re.compile(r"^\s*USER\s+(?!root\b)(\S+)", re.MULTILINE)


# ---------------------------------------------------------------------------
# Dockerfile transform
# ---------------------------------------------------------------------------


def _patch_dockerfile_text(text: str) -> tuple[str | None, dict[str, bool]]:
    """Return (patched_text, change_flags) or (None, _) if already v3-patched.

    change_flags = {"stripped_v2": bool, "added_v3": bool}
    """
    flags = {"stripped_v2": False, "added_v3": False}

    if V3_PATCH_MARKER in text:
        return None, flags

    # 1. Strip the v2 patch block if present.
    new_text, n_subs = _V2_BLOCK_RE.subn("", text)
    if n_subs:
        flags["stripped_v2"] = True
        # Collapse any double-blank-line that the strip might have produced
        # at the seam. Conservative: only collapse 3+ newlines down to 2.
        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    text = new_text

    # 2. Insert the v3 block before the first non-root USER directive.
    if not text.endswith("\n"):
        text = text + "\n"

    m = _USER_LINE_RE.search(text)
    if m is None:
        # No non-root USER — append at end of file.
        patched = text + "\n" + V3_PATCH_BLOCK
    else:
        insert_at = m.start()
        patched = text[:insert_at] + V3_PATCH_BLOCK + "\n" + text[insert_at:]

    flags["added_v3"] = True
    return patched, flags


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
    patched, flags = _patch_dockerfile_text(original)
    if patched is None:
        return {"status": "skipped_already_patched", "reason": "v3 marker present"}

    if dry_run:
        suffix = []
        if flags["stripped_v2"]:
            suffix.append("strip_v2")
        if flags["added_v3"]:
            suffix.append("add_v3")
        return {"status": "would_patch", "reason": "+".join(suffix) or "noop"}

    dockerfile.write_text(patched)
    return {
        "status": "patched",
        "reason": ("strip_v2+add_v3" if flags["stripped_v2"] else "add_v3"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Patch logsmith tasks to v3: strip broken v2 COPY, add /workspace/data -> /setup_files/data symlink.",
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
    reason_counts: dict[str, int] = {}
    examples: dict[str, str] = {}
    for td in task_dirs:
        result = patch_task(td, dry_run=args.dry_run)
        status = result["status"]
        counters[status] = counters.get(status, 0) + 1
        reason_counts[result["reason"]] = reason_counts.get(result["reason"], 0) + 1
        if status not in examples:
            examples[status] = td.name

    print("\n[patcher] Result summary:")
    for status, count in sorted(counters.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")

    print("\n[patcher] Reason summary:")
    for reason, count in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:6d}  {reason}")

    # Post-pass: report unique Dockerfile hashes (sanity check for snapshot
    # collision — should be 1 after a successful v3 patch).
    if not args.dry_run:
        import hashlib

        hashes: set[str] = set()
        for td in task_dirs:
            dfp = td / "environment" / "Dockerfile"
            if dfp.exists():
                hashes.add(hashlib.sha256(dfp.read_bytes()).hexdigest())
        print(
            f"\n[patcher] Unique Dockerfile hashes across {len(task_dirs)} tasks: {len(hashes)}"
        )
        if len(hashes) != 1:
            print(
                "[patcher] WARNING: more than one unique Dockerfile — snapshot cap may be at risk"
            )

    print(f"\n[patcher] Root: {root}")


if __name__ == "__main__":
    main()
