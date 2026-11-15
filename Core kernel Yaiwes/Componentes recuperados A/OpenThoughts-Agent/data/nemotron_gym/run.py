"""Run a registered converter against a HF dataset → Harbor parquet.

Usage:
    python -m data.nemotron_gym.run \
        --dataset nvidia/Nemotron-RL-coding-competitive_coding \
        --output data/nemotron_gym/output/competitive_coding.parquet \
        [--split train] [--limit N] [--smoke]

Output: a parquet file with columns:
  path        : str       (deterministic "<task_id>.tar.gz")
  task_binary : bytes     (gzipped tar)

If --smoke is set, also extracts the first 3 tasks to a temp dir and prints a
manifest of files inside each tarball.
"""

from __future__ import annotations

import argparse
import io
import sys
import tarfile
import time
from collections import Counter
from pathlib import Path


def _ensure_converters_loaded() -> None:
    """Import every converter module so @register decorators fire."""
    from .converters import (  # noqa: F401
        adversarial,
        agent_calendar,
        agent_workplace,
        agentic_conversational_tool_use_pivot,
        agentic_function_calling_pivot,
        agentic_indirect_prompt_injection,
        agentic_swe_pivot,
        arc_agi,
        cfbench,
        citation_formatting,
        competitive_coding,
        identity_following,
        instruction_following,
        instruction_following_freeform,
        inverse_ifeval,
        knowledge_mcqa,
        knowledge_openqa,
        litmus_bench,
        math_boxed,
        multichallenge,
        multiturn_chat,
        qa_abstention,
        reasoning_gym,
        safety,
        science,
        structured_outputs,
        structured_outputs_v2,
        sysbench,
    )


def _load_dataset(
    hf_path: str, split: str, limit: int | None, config: str | None = None
):
    """Load rows. Tries materialized load first; on ujson big-int failures
    (`ValueError: Value is too big!`), falls back to pyarrow-backed streaming.

    `config` selects a named dataset configuration (required for multi-config
    datasets like nvidia/Nemotron-RL-ARC-AGI-v1, which has transductive +
    python_inductive configs).
    """
    from datasets import load_dataset
    from datasets.exceptions import DatasetGenerationError

    name_args = (config,) if config else ()
    try:
        ds = load_dataset(hf_path, *name_args, split=split)
    except DatasetGenerationError as e:
        cause = e.__cause__
        msg = str(cause) if cause else str(e)
        print(
            f"  load_dataset failed: {type(cause).__name__ if cause else 'DatasetGenerationError'}: "
            f"{msg[:160]!r}; trying streaming"
        )
        try:
            ds = load_dataset(hf_path, *name_args, split=split, streaming=True)
            rows: list[dict] = []
            for i, row in enumerate(ds):
                if limit is not None and i >= limit:
                    break
                rows.append(row)
            return rows
        except (DatasetGenerationError, ValueError, TypeError) as e2:
            # TypeError covers pyarrow's "Couldn't cast array of type ..." raised
            # when JSONL rows have inconsistent struct fields (e.g. SysBench's
            # llm_judge entries where some carry an extra `frequency` key) — the
            # raw stdlib-json loader handles these uniformly.
            print(
                f"  streaming also failed: {type(e2).__name__}: {str(e2)[:160]!r}; trying raw file download"
            )
            return _load_raw_jsonl(hf_path, split, limit)
    if limit is not None:
        ds = ds.select(range(min(limit, len(ds))))
    return ds


def _load_raw_jsonl(hf_path: str, split: str, limit: int | None) -> list[dict]:
    """Last-resort loader: download raw JSONL via huggingface_hub and parse with
    stdlib `json` (handles arbitrary-precision ints, unlike the ujson parser
    that `datasets` uses internally).
    """
    import json
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    files = api.list_repo_files(hf_path, repo_type="dataset")
    # Match split=train -> train.jsonl, train.json, train-*.jsonl, etc.
    candidates = [
        f
        for f in files
        if (f.endswith(".jsonl") or f.endswith(".json")) and split in f.lower()
    ]
    if not candidates:
        raise RuntimeError(
            f"raw fallback: no .jsonl/.json file matching split={split!r} "
            f"in {hf_path}; available: {files[:5]}..."
        )
    print(f"  raw fallback: downloading {len(candidates)} file(s): {candidates[:3]}")
    rows: list[dict] = []
    for rel_path in sorted(candidates):
        local = hf_hub_download(repo_id=hf_path, filename=rel_path, repo_type="dataset")
        with open(local, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"    skipping malformed line in {rel_path}: {e}")
                    continue
                if not isinstance(row, dict):
                    continue
                rows.append(row)
                if limit is not None and len(rows) >= limit:
                    return rows
    return rows


def _write_parquet(records: list[dict], output: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    output.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "path": [r["path"] for r in records],
            "task_binary": [r["task_binary"] for r in records],
        }
    )
    # Match project default (scripts/harbor/tasks_parquet_converter.py uses
    # pyarrow's default snappy compression for task parquets).
    pq.write_table(table, output, compression="snappy")


def _smoke_inspect(records: list[dict], n: int = 3) -> None:
    print(f"\n--- smoke inspection (first {min(n, len(records))} tasks) ---")
    for r in records[:n]:
        print(f"\n{r['path']}: {len(r['task_binary'])} bytes")
        with tarfile.open(fileobj=io.BytesIO(r["task_binary"]), mode="r:gz") as tar:
            for info in tar:
                print(f"  {info.name}  ({info.size} bytes)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="HuggingFace dataset path")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--split", default="train")
    ap.add_argument(
        "--config",
        default=None,
        help="named dataset config (for multi-config datasets)",
    )
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    _ensure_converters_loaded()
    from .converters import get as get_converter

    convert = get_converter(args.dataset)
    t0 = time.time()
    ds = _load_dataset(args.dataset, args.split, args.limit, args.config)
    print(
        f"loaded {len(ds)} rows from {args.dataset} "
        f"(split={args.split}{', config=' + args.config if args.config else ''})"
    )
    records: list[dict] = []
    skipped: Counter = Counter()
    seen_ids: set[str] = set()
    for i, row in enumerate(ds):
        try:
            task = convert(row, i)
        except Exception as e:
            skipped[f"convert_error:{type(e).__name__}"] += 1
            if skipped[f"convert_error:{type(e).__name__}"] <= 3:
                print(f"  row {i}: convert error: {e}", file=sys.stderr)
            continue
        if task is None:
            skipped["returned_None"] += 1
            continue
        if task.task_id in seen_ids:
            skipped["duplicate_task_id"] += 1
            continue
        seen_ids.add(task.task_id)
        try:
            blob = task.to_tarball()
        except Exception as e:
            skipped[f"tarball_error:{type(e).__name__}"] += 1
            print(f"  row {i} ({task.task_id}): tarball error: {e}", file=sys.stderr)
            continue
        records.append({"path": f"{task.task_id}.tar.gz", "task_binary": blob})
    elapsed = time.time() - t0
    print(
        f"\nconverted: {len(records)}  skipped: {sum(skipped.values())}  "
        f"({elapsed:.1f}s)"
    )
    for reason, count in sorted(skipped.items(), key=lambda kv: -kv[1]):
        print(f"  skip[{reason}] = {count}")
    if not records:
        print("no records produced; nothing written", file=sys.stderr)
        return 1
    _write_parquet(records, args.output)
    print(f"wrote {args.output} ({args.output.stat().st_size:,} bytes)")
    if args.smoke:
        _smoke_inspect(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
