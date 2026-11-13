#!/usr/bin/env python3
"""Build the versioned, dependency-complete Stack-Pytest large replacement."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SOURCE_REPO = "DCAgent/exp_rpt_stack-pytest-large"
TARGET_REPO = "laion/exp_rpt_stack-pytest-large-v2"
REPO_ROOT = Path(__file__).resolve().parents[2]
PATCHER = REPO_ROOT / "data/patchers/patch_exp_rpt_stack_pytest_large_v2_tasks.py"
EXTRACTOR = REPO_ROOT / "scripts/datagen/extract_tasks_from_parquet.py"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    tasks_dir = args.output_dir / "tasks"
    if not tasks_dir.exists():
        run(
            [
                sys.executable,
                str(EXTRACTOR),
                "--parquet",
                SOURCE_REPO,
                "--output_dir",
                str(tasks_dir),
            ]
        )
    patch_command = [
        sys.executable,
        str(PATCHER),
        "--root",
        str(tasks_dir),
        "--drop-log",
        str(args.output_dir / "dropped.tsv"),
    ]
    if args.dry_run:
        patch_command.append("--dry-run")
    run(patch_command)
    if args.upload:
        if args.dry_run:
            raise ValueError("--upload cannot be combined with --dry-run")
        sys.path.insert(0, str(REPO_ROOT))
        from data.commons import upload_tasks_to_hf

        upload_tasks_to_hf(str(tasks_dir), TARGET_REPO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
