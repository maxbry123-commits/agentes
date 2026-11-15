#!/usr/bin/env python3
"""
DCAgent/mix_baseline_uniform -> laion/mix_baseline_uniform-v2 patcher.

Bug (found in 200-trial QC, 2026-05-14):
    The mix_baseline_uniform dataset is a 3718-task mixture sampled from
    many source datasets. In the QC pass, 15/200 trials failed at infra
    setup (`Path does not exist: .../environment/solution.py`) — Daytona
    declarative build aborted because the Dockerfile contained

        COPY solution.py /app/solution.py

    but `environment/solution.py` was missing. All 15 failures were
    sourced from `bugsinpy_mf-*` (a multi-fault bug-fixing dataset
    distilled from the original BugsInPy benchmark). In the full
    parent dataset, all 333 bugsinpy_mf-* tasks have the same defect:
    Dockerfile references a missing solution.py file.

    The upstream source dataset (`DCAgent/exp_rpt_bugsinpy-mf-large`)
    DOES ship the per-task solution.py under `environment/solution.py`;
    it was simply not carried into mix_baseline_uniform during the
    mixture step. We re-attach it here.

Fix:
    Put each task's solution.py into `setup_files/solution.py` (so Harbor
    uploads it to `/setup_files/solution.py` at trial start, AFTER env
    build) rather than into `environment/`. This is critical for the
    Daytona snapshot budget: Daytona auto-snapshots are keyed on a hash
    of the full environment/ dir (Dockerfile + every fixture file). If
    we wrote 333 unique solution.py files into `environment/`, we would
    create 333 unique snapshots and immediately bust both the
    max_new_snapshots=10 and max_org_snapshots=60 caps. By keeping
    `environment/` byte-identical across all 333 bugsinpy_mf tasks (and
    rewriting the Dockerfile to remove the broken COPY line), they all
    share a single shared snapshot.

    For non-bugsinpy_mf tasks the patcher is a no-op. The Dockerfile
    rewrite drops the COPY line; the runtime layout (solution.py at
    /app/solution.py) is restored by `tests/test.sh`'s existing
    fallback (lines 21-25):

        if [ ! -f /app/solution.py ]; then
            for f in /app/*.py; do
                [ -f "$f" ] && cp "$f" /app/solution.py && break
            done
        fi

    However that fallback only fires if the agent left a candidate .py
    in /app. To make the buggy file unambiguously available before the
    agent runs, we additionally rewrite `instruction.md`'s opening
    section to point the agent at `/setup_files/solution.py` and ask
    it to copy it into `/app/solution.py` and fix the bugs there.
    test.sh keeps its existing fallback as belt-and-suspenders.

Idempotency:
    A marker file `.laion_v2_bugsinpy_patched` is written into each
    patched task dir; re-runs skip dirs that already contain it.

Usage:
    python -m data.patchers.patch_mix_baseline_uniform_tasks \
        --root /tmp/mix_baseline_uniform_src

    # Dry run
    python -m data.patchers.patch_mix_baseline_uniform_tasks \
        --root /tmp/mix_baseline_uniform_src --dry-run

    # Limit to first N task dirs
    python -m data.patchers.patch_mix_baseline_uniform_tasks \
        --root /tmp/mix_baseline_uniform_src --limit 50
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tarfile
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download


SOURCE_DATASET = "DCAgent/exp_rpt_bugsinpy-mf-large"
MARKER_FILE = ".laion_v2_bugsinpy_patched"

INSTRUCTION_PREAMBLE = (
    "**Note from the dataset maintainer (laion v2 patch):** the buggy "
    "starter code for this task lives at `/setup_files/solution.py`, "
    "NOT at `/app/solution.py`. Before you start, copy it into place:\n\n"
    "```bash\ncp /setup_files/solution.py /app/solution.py\n```\n\n"
    "Then locate and fix the bugs in `/app/solution.py`. The verifier "
    "expects the fixed file at `/app/solution.py`.\n\n---\n\n"
)


# Dockerfile lines that fail to build because solution.py is absent from
# the environment directory in the mix dataset. We drop them entirely;
# the agent (and as a fallback, tests/test.sh's existing recovery block)
# is responsible for placing solution.py at /app/solution.py.
_BAD_COPY_RE = re.compile(
    r"^\s*COPY\s+solution\.py\s+/app/solution\.py\s*\r?\n",
    re.MULTILINE,
)
_BAD_COMMENT_RE = re.compile(
    r"^\s*#\s*Copy buggy starter code into /app\s*\r?\n",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Source-of-truth solution.py lookup
# ---------------------------------------------------------------------------


def _load_solutions(verbose: bool = True) -> dict[str, bytes]:
    """Download exp_rpt_bugsinpy-mf-large once and build a {path: solution_bytes} map."""
    if verbose:
        print(
            f"[patcher] Loading solution.py lookup from {SOURCE_DATASET}...",
            file=sys.stderr,
        )
    parquet_path = hf_hub_download(SOURCE_DATASET, "tasks.parquet", repo_type="dataset")
    df = pd.read_parquet(parquet_path)
    solutions: dict[str, bytes] = {}
    for idx in range(len(df)):
        row = df.iloc[idx]
        with tarfile.open(fileobj=io.BytesIO(row.task_binary), mode="r:gz") as tar:
            try:
                fobj = tar.extractfile("environment/solution.py")
                if fobj is None:
                    continue
                solutions[row.path] = fobj.read()
            except KeyError:
                continue
    if verbose:
        print(
            f"[patcher] Loaded {len(solutions)} solution.py files from {SOURCE_DATASET}",
            file=sys.stderr,
        )
    return solutions


# ---------------------------------------------------------------------------
# Per-task driver
# ---------------------------------------------------------------------------


def _read_source(task_dir: Path) -> str | None:
    """Return the source string from metadata.json, or None if missing/unreadable."""
    md_path = task_dir / "metadata.json"
    if not md_path.is_file():
        return None
    try:
        return json.loads(md_path.read_text()).get("source")
    except (json.JSONDecodeError, OSError):
        return None


def _patch_dockerfile(text: str) -> str:
    """Strip the broken `COPY solution.py` (+ its comment) from Dockerfile text."""
    text = _BAD_COPY_RE.sub("", text)
    text = _BAD_COMMENT_RE.sub("", text)
    return text


def _patch_instruction(text: str) -> str:
    """Prepend the laion v2 preamble so the agent knows where to find the buggy file."""
    return INSTRUCTION_PREAMBLE + text


def patch_task(
    task_dir: Path,
    solutions: dict[str, bytes],
    dry_run: bool = False,
) -> dict:
    """Patch a single task. Returns ``{"status": ..., "reason": ...}``."""
    if (task_dir / MARKER_FILE).exists():
        return {"status": "skipped_already_patched", "reason": "marker present"}

    source = _read_source(task_dir)
    if source is None:
        return {"status": "skipped_no_metadata", "reason": "missing metadata.json"}

    if not source.startswith("bugsinpy_mf-"):
        return {"status": "skipped_other_source", "reason": f"source={source}"}

    sol_bytes = solutions.get(source)
    if sol_bytes is None:
        return {
            "status": "skipped_no_solution_match",
            "reason": f"no solution.py for {source}",
        }

    dockerfile = task_dir / "environment" / "Dockerfile"
    if not dockerfile.is_file():
        return {
            "status": "skipped_no_dockerfile",
            "reason": "no environment/Dockerfile",
        }

    instr_path = task_dir / "instruction.md"
    if not instr_path.is_file():
        return {"status": "skipped_no_instruction", "reason": "no instruction.md"}

    new_dockerfile = _patch_dockerfile(dockerfile.read_text())
    new_instruction = _patch_instruction(instr_path.read_text())

    if dry_run:
        return {"status": "would_patch", "reason": f"source={source}"}

    # Write solution.py to setup_files/ (NOT environment/; see module docstring).
    setup_files_dir = task_dir / "setup_files"
    setup_files_dir.mkdir(exist_ok=True)
    (setup_files_dir / "solution.py").write_bytes(sol_bytes)

    dockerfile.write_text(new_dockerfile)
    instr_path.write_text(new_instruction)
    (task_dir / MARKER_FILE).write_text("v2 bugsinpy_mf solution.py reattachment\n")

    return {"status": "patched", "reason": f"source={source}"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Reattach the missing solution.py to bugsinpy_mf-* tasks in a "
            "mix_baseline_uniform extracted task dir."
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
        p for p in root.iterdir() if p.is_dir() and (p / "instruction.md").exists()
    )
    if args.limit is not None:
        task_dirs = task_dirs[: args.limit]

    print(f"[patcher] Found {len(task_dirs)} task directories under {root}")
    if args.dry_run:
        print("[patcher] DRY RUN — no files will be written")

    solutions = _load_solutions()

    counters: dict[str, int] = {}
    examples: dict[str, str] = {}
    for td in task_dirs:
        result = patch_task(td, solutions, dry_run=args.dry_run)
        status = result["status"]
        counters[status] = counters.get(status, 0) + 1
        examples.setdefault(status, td.name)

    print("\n[patcher] Result summary:")
    for status, count in sorted(counters.items(), key=lambda kv: -kv[1]):
        ex = examples.get(status, "")
        print(f"  {count:6d}  {status:30s}  (e.g. {ex})")
    print(f"\n[patcher] Root: {root}")


if __name__ == "__main__":
    main()
