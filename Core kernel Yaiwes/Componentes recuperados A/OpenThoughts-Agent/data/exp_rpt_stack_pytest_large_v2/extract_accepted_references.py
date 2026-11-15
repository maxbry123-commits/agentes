#!/usr/bin/env python3
"""Materialize private task references accepted by a Harbor oracle job."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def accepted_task_names(job_root: Path) -> set[str]:
    """Return task IDs with a completed deterministic reward of exactly one."""
    accepted: set[str] = set()
    for result_path in job_root.rglob("result.json"):
        if result_path.parent == job_root:
            continue
        result = json.loads(result_path.read_text())
        reward = (result.get("verifier_result") or {}).get("rewards", {}).get("reward")
        if reward == 1 and not result.get("exception_info"):
            accepted.add(result_path.parent.name.split("__", 1)[0])
    return accepted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    accepted = accepted_task_names(args.job_root)
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise ValueError(f"output root must be empty: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    for name in sorted(accepted):
        source = args.source_root / name
        if not (source / "solution" / "solve.sh").is_file():
            raise ValueError(f"accepted reference missing from source: {name}")
        shutil.copytree(source, args.output_root / name)
    print(f"accepted={len(accepted)} output={args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
