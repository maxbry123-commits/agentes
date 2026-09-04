#!/usr/bin/env python3
"""Record private accepted references and stage a solution-free public dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def file_sha256(path: Path) -> str:
    """Return the stable digest of one accepted private reference script."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accepted_tasks(private_root: Path) -> list[Path]:
    """Return only task directories carrying a private verified reference."""
    tasks = []
    for task in sorted(private_root.iterdir()):
        solve = task / "solution" / "solve.sh"
        if (
            task.is_dir()
            and (task / "environment" / "Dockerfile").is_file()
            and solve.is_file()
        ):
            tasks.append(task)
    if not tasks:
        raise ValueError(f"no accepted private references under {private_root}")
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--harbor-job-path", type=Path, action="append", required=True)
    args = parser.parse_args()

    tasks = accepted_tasks(args.private_root)
    if args.public_root.exists() and any(args.public_root.iterdir()):
        raise ValueError(f"public root must be empty: {args.public_root}")
    args.public_root.mkdir(parents=True, exist_ok=True)
    entries = []
    for task in tasks:
        solve = task / "solution" / "solve.sh"
        destination = args.public_root / task.name
        shutil.copytree(task, destination)
        shutil.rmtree(destination / "solution")
        entries.append(
            {
                "task_id": task.name,
                "source_revision": args.source_revision,
                "reference_sha256": file_sha256(solve),
                "harbor_job_paths": [str(path) for path in args.harbor_job_path],
            }
        )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps({"accepted_references": entries}, indent=2) + "\n"
    )
    print(
        f"private_accepted={len(entries)} public_staged={len(entries)} manifest={args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
