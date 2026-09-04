#!/usr/bin/env python3
"""Assemble independently certified TaskTrove v4.1 repair outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

TASK_SCHEMA = pa.schema(
    [pa.field("path", pa.string()), pa.field("task_binary", pa.binary())]
)
MAX_ROW_GROUP_ROWS = 32
MCQA_MAX_ROW_GROUP_ROWS = 8192
MIN_TASKS = 300

REMOVALS = (
    {
        "dataset": "laion__mix_baseline_uniform-v2",
        "rows": 3718,
        "sha256": "8c59a1022aef25922e887751c93a809a8aefa4ea56ad189b7334316e564d9810",
        "reason": "empty verifier suites in 5/100 audited traces",
    },
    {
        "dataset": "laion__mix_h1_struggle_zone-v2",
        "rows": 3116,
        "sha256": "d00d88537c514b83cfdff052e07bd6cf18694116570eaa53bda2181f55ed915a",
        "reason": "empty verifier suites in 14/100 audited traces",
    },
)

QUARANTINES = (
    {
        "dataset": "laion__exp_rpt_methods2test-large-v4",
        "reason": "0/32 attempted repaired oracles passed the exact Java image",
    },
    {
        "dataset": "laion__exp_rpt_stack-jest-v4",
        "reason": "project context and a trustworthy oracle are not recoverable",
    },
    {
        "dataset": "laion__exp_rpt_stack-rspec-v3",
        "reason": "candidate repairs still passed with an empty workspace",
    },
    {
        "dataset": "laion__nemotron-gym-agentic-indirect-prompt-injection-v2",
        "reason": "the package lacks an authoritative legitimate action",
    },
    {
        "dataset": "laion__toolscale-v3",
        "reason": "a sound repair requires an agent-isolated tool service",
    },
    {
        "dataset": "laion__nemotron-gym-agentic-swe-pivot-v3",
        "reason": "single-reference matching does not prove semantic completion",
    },
    {
        "dataset": "laion__nemotron-gym-instruction-following-freeform-v2",
        "reason": "regex-only checking validates format rather than content",
    },
)

UNCHANGED_STANDALONE_RETIREMENTS = (
    {
        "dataset": "laion__exp_rpt_methods2test-large-v4",
        "sha256": "9cbed6ac4f91271144221575e5ff0ab45e66c15d067bdf6816b14b658849cfcf",
    },
    {
        "dataset": "laion__exp_rpt_stack-jest-v4",
        "sha256": "da431eabfc7cdfd5b439969b0bd1ede99af5a61fcb5f5ed6a131ec52f0e5aedc",
    },
    {
        "dataset": "laion__exp_rpt_stack-rspec-v3",
        "sha256": "65225c1488bcc917ca72d03e94e22f31f80733c8ab3aa4a024f7fd68b816cf13",
    },
    {
        "dataset": "laion__nemotron-gym-agentic-indirect-prompt-injection-v2",
        "sha256": "d4dc394485f9458bd11d350ed85acc12155ee80955945b898c37204e24ec17ce",
    },
    {
        "dataset": "laion__toolscale-v3",
        "sha256": "6536b87dbb18615a983a98402231e82cd8932735587bb9f96da93789950b986b",
    },
)

TULU_SOURCE = {
    "source_dataset": "laion__tulu3-sft-personas-math-sandboxes-verified-v2",
    "source_rows": 9998,
    "source_sha256": "2428edeb232b2cd8dc19d06efb16e18310be6491aa19b708092f4fdd600d7929",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_parquet(
    path: Path,
    expected_rows: int,
    expected_sha256: str,
    max_row_group_rows: int,
) -> None:
    if file_sha256(path) != expected_sha256:
        raise ValueError(f"Parquet hash mismatch: {path}")
    parquet = pq.ParquetFile(path)
    if parquet.schema_arrow != TASK_SCHEMA:
        raise ValueError(f"unexpected Parquet schema: {path}")
    if parquet.metadata.num_rows != expected_rows:
        raise ValueError(f"unexpected Parquet row count: {path}")
    for index in range(parquet.metadata.num_row_groups):
        if parquet.metadata.row_group(index).num_rows > max_row_group_rows:
            raise ValueError(f"oversized Parquet row group: {path}")
    if expected_rows < MIN_TASKS:
        raise ValueError(f"dataset violates the {MIN_TASKS}-task floor: {path}")


def copy_dataset(
    stage: Path,
    source_path: Path,
    entry: dict[str, object],
) -> dict[str, object]:
    output_dataset = str(entry["output_dataset"])
    output_rows = int(entry["output_rows"])
    output_sha256 = str(entry["output_sha256"])
    max_row_group_rows = (
        MCQA_MAX_ROW_GROUP_ROWS
        if output_dataset == "laion__nemotron-gym-knowledge-mcqa-v2"
        else MAX_ROW_GROUP_ROWS
    )
    validate_parquet(source_path, output_rows, output_sha256, max_row_group_rows)
    relative = Path("datasets") / output_dataset / "tasks.parquet"
    destination = stage / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    return {
        **entry,
        "max_row_group_rows": max_row_group_rows,
        "output": str(relative),
    }


def a1_entry(report_path: Path) -> tuple[dict[str, object], Path]:
    report = json.loads(report_path.read_text())
    if report.get("status") == "blocked":
        raise ValueError(f"blocked A1 report cannot be released: {report_path}")
    output_dataset = str(report["output_repo_path"]).removesuffix("/tasks.parquet")
    entry = {
        "source_dataset": str(report["source_repo_path"]).removesuffix(
            "/tasks.parquet"
        ),
        "source_rows": int(report["source_rows"]),
        "source_sha256": str(report["source_sha256"]),
        "output_dataset": output_dataset,
        "output_rows": int(report["retained_rows"]),
        "output_sha256": str(report["output_sha256"]),
    }
    return entry, report_path.parent / output_dataset / "tasks.parquet"


def manifest_entries(
    manifest_path: Path,
) -> list[tuple[dict[str, object], Path]]:
    manifest = json.loads(manifest_path.read_text())
    results = []
    for dataset in manifest["datasets"]:
        if "output_rows" in dataset:
            output_rows = dataset["output_rows"]
        elif "kept_rows" in dataset:
            output_rows = dataset["kept_rows"]
        else:
            output_rows = dataset["rows"]
        source_rows = (
            dataset["source_rows"] if "source_rows" in dataset else dataset["rows"]
        )
        entry = {
            "source_dataset": dataset["source_dataset"],
            "source_rows": int(source_rows),
            "source_sha256": dataset["source_sha256"],
            "output_dataset": dataset["output_dataset"],
            "output_rows": int(output_rows),
            "output_sha256": dataset["output_sha256"],
        }
        candidates = (
            manifest_path.parent
            / "datasets"
            / str(entry["output_dataset"])
            / "tasks.parquet",
            manifest_path.parent / str(entry["output_dataset"]) / "tasks.parquet",
        )
        path = next(
            (candidate for candidate in candidates if candidate.is_file()), None
        )
        if path is None:
            raise FileNotFoundError(f"missing output for {entry['output_dataset']}")
        results.append((entry, path))
    return results


def tulu_entry(manifest_path: Path) -> tuple[dict[str, object], Path]:
    manifest = json.loads(manifest_path.read_text())
    output_dataset, result = next(iter(manifest["outputs"].items()))
    entry = {
        **TULU_SOURCE,
        "output_dataset": output_dataset,
        "output_rows": int(result["rows"]),
        "output_sha256": result["sha256"],
    }
    return entry, manifest_path.parent / output_dataset / "tasks.parquet"


def assemble(args: argparse.Namespace) -> None:
    stage: Path = args.stage
    if stage.exists() and any(stage.iterdir()):
        raise ValueError(f"stage must be absent or empty: {stage}")
    stage.mkdir(parents=True, exist_ok=True)

    candidates = [
        a1_entry(args.calendar_report),
        *manifest_entries(args.a2_manifest),
        *manifest_entries(args.batch_b_manifest),
        tulu_entry(args.tulu_manifest),
    ]
    entries = [copy_dataset(stage, path, entry) for entry, path in candidates]
    source_names = [str(entry["source_dataset"]) for entry in entries]
    output_names = [str(entry["output_dataset"]) for entry in entries]
    if len(source_names) != len(set(source_names)):
        raise ValueError("duplicate source dataset")
    if len(output_names) != len(set(output_names)):
        raise ValueError("duplicate output dataset")

    manifest = {
        "source_repo": "open-thoughts/TaskTrove",
        "source_revision": "81820c33ba26d705b9ea7ebac2d090d70fac93f4",
        "source_version": "4.0",
        "target_version": "4.1",
        "survey_revision": "3e96fe6464ce5ab6209e98801caab29b4a1fe87a",
        "datasets": entries,
        "removals": list(REMOVALS),
        "quarantines": list(QUARANTINES),
        "unchanged_standalone_retirements": list(UNCHANGED_STANDALONE_RETIREMENTS),
    }
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"assembled {len(entries)} replacements and {len(REMOVALS)} removals "
        f"under {stage}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--calendar-report", type=Path, required=True)
    parser.add_argument("--a2-manifest", type=Path, required=True)
    parser.add_argument("--batch-b-manifest", type=Path, required=True)
    parser.add_argument("--tulu-manifest", type=Path, required=True)
    assemble(parser.parse_args())


if __name__ == "__main__":
    main()
