#!/usr/bin/env python3
"""
Patch `DCAgent/mix_h7_dedup_diverse_1k` task dirs to restore the missing
``environment/solution.py`` for the ``bugsinpy_mf`` subset.

Background (QC pass 2026-05-14):
  The mix is 1909 tasks across 15 source datasets (stack-pytest-synthetic
  377, stack-selfdoc 218, swh 216, stack-pytest 204, codenet-python 188,
  bugsinpy_mf 170, ...). Every single ``bugsinpy_mf`` task (170/170) is
  missing ``environment/solution.py`` even though the per-task
  ``Dockerfile`` still references it::

      FROM python:3.10-slim
      WORKDIR /app
      RUN mkdir -p /output && chmod 777 /output
      RUN pip install --no-cache-dir pytest
      # Copy buggy starter code into /app
      COPY solution.py /app/solution.py

  Daytona's snapshot uploader walks the build context, hits the missing
  path, and raises::

      FileNotFoundError: Path does not exist:
          .../environment/solution.py
      daytona.common.errors.DaytonaError: Failed to create sandbox:
          Path does not exist: .../environment/solution.py

  All 18/18 infra failures observed in the 200-trial QC run came from
  this exact mode; 0 trials of the 18 bugsinpy_mf rows sampled survived
  environment setup.

Fix:
  For each task with ``metadata.source`` of the form
  ``bugsinpy_mf-<NNNN>``, look the upstream task up in
  ``DCAgent/exp_rpt_bugsinpy-mf`` (which still ships
  ``environment/solution.py``), extract that file's bytes, and write it
  into ``<task_dir>/environment/solution.py``.

  Other diffs between mix and upstream (``metadata.json``, ``task.toml``,
  ``tests/test.sh``) are intentional re-curations and are left untouched.

Idempotency:
  Skip when ``environment/solution.py`` already exists. We don't need a
  string marker — the file is the marker.

Caching:
  We load the upstream HF dataset once and build an in-memory index
  ``upstream_id -> solution_bytes`` so the per-task patch is O(1) and we
  don't re-extract from tar repeatedly.

Usage::

    python data/patchers/patch_mix_h7_dedup_diverse_1k_tasks.py \\
        --root /tmp/mix_h7_dedup_diverse_1k_src

    python data/patchers/patch_mix_h7_dedup_diverse_1k_tasks.py \\
        --root /tmp/mix_h7_dedup_diverse_1k_src --dry-run

    python data/patchers/patch_mix_h7_dedup_diverse_1k_tasks.py \\
        --root /tmp/mix_h7_dedup_diverse_1k_src --limit 5
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
from pathlib import Path

UPSTREAM_DATASET = "DCAgent/exp_rpt_bugsinpy-mf"
UPSTREAM_SPLIT = "train"
SOLUTION_INNER_PATH = "environment/solution.py"


def _build_upstream_index() -> dict[str, bytes]:
    """Load upstream bugsinpy_mf dataset and build {task_id -> solution.py bytes}.

    Each upstream row has ``path`` like ``bugsinpy_mf-0013`` and
    ``task_binary`` containing a gzip'd tarball with
    ``environment/solution.py`` inside.
    """
    from datasets import load_dataset  # local import: heavy dep

    print(
        f"[patcher] Loading upstream solutions from {UPSTREAM_DATASET} "
        f"(split={UPSTREAM_SPLIT})…"
    )
    ds = load_dataset(UPSTREAM_DATASET, split=UPSTREAM_SPLIT)
    index: dict[str, bytes] = {}
    missing_in_upstream: list[str] = []
    for row in ds:
        upstream_id = row["path"]
        blob = row["task_binary"]
        bio = io.BytesIO(blob)
        try:
            with tarfile.open(fileobj=bio, mode="r:gz") as tf:
                member = next(
                    (m for m in tf.getmembers() if m.name == SOLUTION_INNER_PATH),
                    None,
                )
                if member is None:
                    missing_in_upstream.append(upstream_id)
                    continue
                f = tf.extractfile(member)
                if f is None:
                    missing_in_upstream.append(upstream_id)
                    continue
                index[upstream_id] = f.read()
        except (tarfile.TarError, OSError) as exc:
            print(
                f"[patcher]   warn: cannot read upstream tar for {upstream_id}: {exc}",
                file=sys.stderr,
            )
            missing_in_upstream.append(upstream_id)

    print(
        f"[patcher] Indexed {len(index)} upstream solutions "
        f"(missing in upstream: {len(missing_in_upstream)})"
    )
    if missing_in_upstream[:5]:
        print(f"[patcher]   examples missing in upstream: {missing_in_upstream[:5]}")
    return index


def _read_metadata(task_dir: Path) -> dict | None:
    md_path = task_dir / "metadata.json"
    if not md_path.is_file():
        return None
    try:
        return json.loads(md_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def patch_task(
    task_dir: Path,
    upstream_index: dict[str, bytes],
    dry_run: bool,
) -> dict:
    """Patch a single task. Returns {'status': ..., 'reason': ...}."""
    env_dir = task_dir / "environment"
    if not env_dir.is_dir():
        return {"status": "skipped_no_environment", "reason": "no environment/ dir"}

    metadata = _read_metadata(task_dir)
    if metadata is None:
        return {
            "status": "skipped_no_metadata",
            "reason": "missing/unreadable metadata.json",
        }

    source = metadata.get("source", "")
    if not isinstance(source, str) or not source.startswith("bugsinpy_mf-"):
        return {"status": "skipped_non_bugsinpy_mf", "reason": f"source={source!r}"}

    sol_path = env_dir / "solution.py"
    if sol_path.exists():
        # Idempotency: file is the marker.
        return {"status": "skipped_already_patched", "reason": "solution.py present"}

    solution_bytes = upstream_index.get(source)
    if solution_bytes is None:
        return {
            "status": "skipped_no_upstream",
            "reason": f"upstream {source} not in index",
        }

    if dry_run:
        return {"status": "would_patch", "reason": f"dry-run; {len(solution_bytes)}B"}

    sol_path.write_bytes(solution_bytes)
    return {"status": "patched", "reason": f"wrote {len(solution_bytes)}B"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Restore environment/solution.py for bugsinpy_mf tasks in "
            "DCAgent/mix_h7_dedup_diverse_1k extracted task directories."
        ),
    )
    p.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory containing extracted mix-h7-dedup-diverse-* task subdirectories.",
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


def main() -> int:
    args = parse_args()
    root: Path = args.root
    if not root.is_dir():
        print(f"[patcher] --root not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(
        p for p in root.iterdir() if p.is_dir() and (p / "environment").is_dir()
    )
    if args.limit is not None:
        task_dirs = task_dirs[: args.limit]

    print(f"[patcher] Found {len(task_dirs)} task directories under {root}")
    if args.dry_run:
        print("[patcher] DRY RUN — no files will be written")

    upstream_index = _build_upstream_index()

    counters: dict[str, int] = {}
    examples: dict[str, str] = {}
    for td in task_dirs:
        result = patch_task(td, upstream_index, dry_run=args.dry_run)
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
