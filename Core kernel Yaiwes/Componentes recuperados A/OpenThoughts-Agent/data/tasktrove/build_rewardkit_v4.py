#!/usr/bin/env python3
"""Build and validate the TaskTrove v4 RewardKit migration.

The builder downloads and processes one source Parquet at a time. It never
materializes task archives on disk and caps Arrow batches at 32 rows.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import tarfile
import tomllib
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from harbor.models.task.config import TaskConfig
from huggingface_hub import hf_hub_download

from data.tasktrove.rewardkit_migration import (
    DATASET_VERSION_MAP,
    REWARDKIT_PACKAGE,
    classify_judge,
    migrate_task_binary,
)

REPO_ID = "open-thoughts/TaskTrove"
BATCH_SIZE = 32
EXPECTED_SCHEMA = pa.schema(
    [pa.field("path", pa.string()), pa.field("task_binary", pa.binary())]
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_files(task_binary: bytes) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(task_binary), mode="r:*") as archive:
        for member in archive.getmembers():
            if member.name.startswith("/") or ".." in member.name.split("/"):
                raise ValueError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"archive link is not allowed: {member.name}")
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"could not read {member.name}")
            files[member.name] = extracted.read()
    return files


def validate_migrated_archive(task_binary: bytes) -> None:
    files = archive_files(task_binary)
    test_script = files["tests/test.sh"].decode()
    dockerfile = files["environment/Dockerfile"].decode()
    task_config = files["task.toml"].decode()
    if classify_judge(files) is not None:
        raise ValueError("legacy LLM judge remains after migration")
    if "|| true" in test_script or "> /logs/verifier/reward.txt" in test_script:
        raise ValueError("test script masks a verifier failure")
    if REWARDKIT_PACKAGE not in dockerfile:
        raise ValueError("RewardKit is not installed in the task image")
    tomllib.loads(task_config)
    TaskConfig.model_validate_toml(task_config)
    judge = files.get("tests/judge.toml")
    gate = files.get("tests/deterministic_gate")
    if judge is None and gate is None:
        raise ValueError("migrated task has neither a judge nor a deterministic gate")
    if judge is not None:
        parsed = tomllib.loads(judge.decode())
        if parsed.get("judge", {}).get("files") != ["/app/response.txt"]:
            raise ValueError("RewardKit judge does not evaluate response.txt")
    if gate is not None:
        compile(gate.decode(), "deterministic_gate", "exec")


def build_dataset(source: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    parquet = pq.ParquetFile(source)
    if parquet.schema_arrow != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected schema for {source}: {parquet.schema_arrow}")

    families: Counter[str] = Counter()
    paths: set[str] = set()
    rows = 0
    migrated_rows = 0
    writer = pq.ParquetWriter(output, EXPECTED_SCHEMA, compression="zstd")
    try:
        for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
            output_paths: list[str] = []
            output_tasks: list[bytes] = []
            for path, task_binary in zip(
                batch.column(0).to_pylist(),
                batch.column(1).to_pylist(),
                strict=True,
            ):
                if path in paths:
                    raise ValueError(f"duplicate path in {source}: {path}")
                paths.add(path)
                migrated, migration = migrate_task_binary(task_binary)
                if migration is not None:
                    validate_migrated_archive(migrated)
                    families[migration.family] += 1
                    migrated_rows += 1
                output_paths.append(path)
                output_tasks.append(migrated)
                rows += 1
            writer.write_batch(
                pa.record_batch(
                    [pa.array(output_paths), pa.array(output_tasks)],
                    schema=EXPECTED_SCHEMA,
                )
            )
    finally:
        writer.close()

    if rows < 300:
        raise ValueError(f"standing-order minimum violated: {source} has {rows} rows")
    if migrated_rows == 0:
        raise ValueError(f"no LLM judges found in declared source {source}")
    return {
        "rows": rows,
        "migrated_rows": migrated_rows,
        "unchanged_rows": rows - migrated_rows,
        "families": dict(sorted(families.items())),
        "source_sha256": file_sha256(source),
        "output_sha256": file_sha256(output),
    }


def validate_dataset(output: Path, expected: dict[str, object]) -> None:
    parquet = pq.ParquetFile(output)
    if parquet.schema_arrow != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected output schema: {output}")
    paths: set[str] = set()
    migrated = 0
    rows = 0
    for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
        for path, task_binary in zip(
            batch.column(0).to_pylist(),
            batch.column(1).to_pylist(),
            strict=True,
        ):
            if path in paths:
                raise ValueError(f"duplicate output path: {path}")
            paths.add(path)
            files = archive_files(task_binary)
            if "tests/judge.toml" in files or "tests/deterministic_gate" in files:
                validate_migrated_archive(task_binary)
                migrated += 1
            rows += 1
    if rows != expected["rows"] or migrated != expected["migrated_rows"]:
        raise ValueError(
            f"validation mismatch for {output}: rows={rows}, migrated={migrated}"
        )
    if file_sha256(output) != expected["output_sha256"]:
        raise ValueError(f"output hash changed during validation: {output}")


def build(stage: Path, revision: str, *, validate_only: bool) -> dict[str, object]:
    source_dir = stage / "sources"
    output_dir = stage / "datasets"
    manifest_path = stage / "manifest.json"
    stage.mkdir(parents=True, exist_ok=True)

    if validate_only:
        manifest = json.loads(manifest_path.read_text())
        for dataset in manifest["datasets"]:
            validate_dataset(stage / dataset["output"], dataset)
        return manifest

    datasets = []
    for source_name, output_name in DATASET_VERSION_MAP.items():
        source_path = Path(
            hf_hub_download(
                REPO_ID,
                f"{source_name}/tasks.parquet",
                repo_type="dataset",
                revision=revision,
                local_dir=source_dir,
            )
        )
        output_path = output_dir / output_name / "tasks.parquet"
        result = build_dataset(source_path, output_path)
        result.update(
            {
                "source": str(source_path.relative_to(stage)),
                "source_dataset": source_name,
                "output": str(output_path.relative_to(stage)),
                "output_dataset": output_name,
            }
        )
        datasets.append(result)

    manifest = {
        "source_repo": REPO_ID,
        "source_revision": revision,
        "target_version": "4.0",
        "datasets": datasets,
        "total_rows": sum(int(dataset["rows"]) for dataset in datasets),
        "total_migrated_rows": sum(
            int(dataset["migrated_rows"]) for dataset in datasets
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for dataset in datasets:
        validate_dataset(stage / dataset["output"], dataset)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--clear-source-cache", action="store_true")
    args = parser.parse_args()

    manifest = build(args.stage, args.revision, validate_only=args.validate_only)
    if args.clear_source_cache and not args.validate_only:
        shutil.rmtree(args.stage / "sources")
    print(
        json.dumps({key: value for key, value in manifest.items() if key != "datasets"})
    )


if __name__ == "__main__":
    main()
