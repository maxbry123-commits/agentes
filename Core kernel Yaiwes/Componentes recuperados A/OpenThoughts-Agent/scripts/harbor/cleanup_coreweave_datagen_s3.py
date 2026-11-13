"""Publish completed CoreWeave datagen traces from durable S3 output.

Run this inside an Iris CoreWeave task. The task receives the object-store
credentials through ``iris-task-env`` and an HF token through the launcher's
secret environment. Source bundles are copied to worker-local temporary disk,
then removed only after a verified Hub upload.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import boto3
from botocore.config import Config
from datasets import load_dataset
from datasets.exceptions import DatasetNotFoundError, FileNotFoundDatasetsError
from huggingface_hub import HfApi
from huggingface_hub.errors import RepositoryNotFoundError


MIN_REAL_AVERAGE_TURNS = 1.1
DOWNLOAD_WORKERS = 32


@dataclass(frozen=True)
class CleanupTarget:
    """One completed datagen bundle and its public trace dataset."""

    job_name: str
    source_prefixes: tuple[str, ...]
    repo_id: str


def parse_target(value: str) -> CleanupTarget:
    """Parse ``job_name|s3_prefix[,s3_prefix...]|repo_id`` from the CLI."""
    fields = value.split("|", maxsplit=2)
    if len(fields) != 3 or any(not field for field in fields):
        raise argparse.ArgumentTypeError(
            "--target must be job_name|s3://bucket/prefix[,s3://bucket/prefix...]|penfever/repo"
        )
    job_name, prefixes_field, repo_id = fields
    source_prefixes = tuple(prefix for prefix in prefixes_field.split(",") if prefix)
    if not source_prefixes:
        raise argparse.ArgumentTypeError("--target must include at least one S3 prefix")
    for source_prefix in source_prefixes:
        try:
            parse_s3_uri(source_prefix)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc
    return CleanupTarget(job_name, source_prefixes, repo_id)


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Return bucket and normalized object prefix for an S3 URI."""
    if not uri.startswith("s3://"):
        raise ValueError(f"Expected an S3 URI, got {uri!r}")
    bucket, separator, prefix = uri[5:].partition("/")
    if not bucket or not separator or not prefix:
        raise ValueError(f"Expected s3://bucket/prefix, got {uri!r}")
    return bucket, f"{prefix.rstrip('/')}/"


def coreweave_s3_client():
    """Build an S3 client compatible with CoreWeave's virtual-hosted endpoint."""
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        config=Config(
            max_pool_connections=DOWNLOAD_WORKERS,
            retries={"max_attempts": 10, "mode": "adaptive"},
            s3={"addressing_style": "virtual"},
        ),
    )


def local_object_path(destination: Path, relative_key: str) -> Path:
    """Map an S3 object key below a destination without permitting traversal."""
    relative_path = PurePosixPath(relative_key)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe relative S3 object key: {relative_key!r}")
    return destination.joinpath(*relative_path.parts)


def download_prefix(target: CleanupTarget, destination: Path) -> int:
    """Copy every object in a durable source prefix to temporary worker disk."""
    if len(target.source_prefixes) != 1:
        raise ValueError("download_prefix accepts exactly one source prefix")
    source_prefix = target.source_prefixes[0]
    bucket, prefix = parse_s3_uri(source_prefix)
    client = coreweave_s3_client()
    objects = []
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix
    ):
        for item in page.get("Contents", []):
            key = item["Key"]
            relative = key.removeprefix(prefix)
            if not relative:
                continue
            objects.append((key, relative))
    if not objects:
        raise RuntimeError(f"No source objects found under {source_prefix}")

    def download_object(item: tuple[str, str]) -> None:
        key, relative = item
        local_path = local_object_path(destination, relative)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(local_path))

    print(
        f"[cleanup] {target.job_name}: downloading {len(objects)} S3 objects",
        flush=True,
    )
    copied = 0
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        futures = [executor.submit(download_object, item) for item in objects]
        for future in as_completed(futures):
            future.result()
            copied += 1
            if copied % 500 == 0 or copied == len(objects):
                print(
                    f"[cleanup] {target.job_name}: downloaded {copied}/{len(objects)} objects",
                    flush=True,
                )
    return copied


def merge_trial_directories(source_job_dirs: list[Path], destination: Path) -> Path:
    """Move retry run directories below one root without losing duplicate trial names.

    The exporter recursively finds trial directories and resolves run metadata from
    each trial's ancestors. Keeping every source run as its own child therefore
    preserves its config while making all independently generated retries export
    into one dataset.
    """
    if not source_job_dirs:
        raise ValueError("Expected at least one Harbor run directory to merge")
    destination.mkdir(parents=True, exist_ok=False)
    for index, source_job_dir in enumerate(source_job_dirs):
        target_dir = destination / f"run-{index:02d}-{source_job_dir.name}"
        shutil.move(str(source_job_dir), str(target_dir))
    return destination


def materialize_target_trials(
    target: CleanupTarget, temporary_root: Path
) -> tuple[Path, int]:
    """Download all retry prefixes and combine their Harbor runs for one export."""
    source_job_dirs = []
    copied = 0
    for index, source_prefix in enumerate(target.source_prefixes):
        source_root = temporary_root / f"source-{index:02d}"
        source_target = CleanupTarget(target.job_name, (source_prefix,), target.repo_id)
        copied += download_prefix(source_target, source_root)
        source_job_dirs.append(direct_trial_directory(source_root))
    return (
        merge_trial_directories(source_job_dirs, temporary_root / "merged-trace-jobs"),
        copied,
    )


def direct_trial_directory(bundle_root: Path) -> Path:
    """Locate the single directory directly containing Harbor trial directories.

    Canonical durable jobs use ``<job>/trace_jobs/<run>/<trial>/result.json``.
    Runs launched before the Iris datagen path fix instead use the malformed
    ``<job>/<run>/<trial>/result.json`` layout. Inferring the run directory
    from actual results lets cleanup rescue both while keeping the canonical
    writer layout explicit.
    """
    trial_results = [
        result_path
        for result_path in bundle_root.rglob("result.json")
        if (result_path.parent / "agent" / "trajectory.json").is_file()
    ]
    candidates = sorted({result_path.parent.parent for result_path in trial_results})
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected results from exactly one Harbor run under {bundle_root}; found {candidates}"
        )
    return candidates[0]


def realness_summary(job_dir: Path) -> tuple[int, float, int]:
    """Return trial count, mean agent-step count, and exception count."""
    result_paths = sorted(
        result_path
        for result_path in job_dir.rglob("result.json")
        if (result_path.parent / "agent" / "trajectory.json").is_file()
    )
    turns: list[int] = []
    exceptions = 0
    for result_path in result_paths:
        result = json.loads(result_path.read_text())
        exception = result.get("exception_info") or {}
        if exception.get("exception_type"):
            exceptions += 1
        trajectory_path = result_path.parent / "agent" / "trajectory.json"
        trajectory = json.loads(trajectory_path.read_text())
        steps = (
            trajectory.get("steps", []) if isinstance(trajectory, dict) else trajectory
        )
        if isinstance(steps, list):
            turns.append(len(steps))
    if not turns:
        raise RuntimeError(f"No readable trajectories under {job_dir}")
    return len(result_paths), statistics.fmean(turns), exceptions


def hub_row_count(repo_id: str) -> int:
    """Load the published train split and return its exact row count, or zero."""
    try:
        HfApi().dataset_info(repo_id)
    except RepositoryNotFoundError:
        return 0
    try:
        return len(load_dataset(repo_id, split="train"))
    except (DatasetNotFoundError, FileNotFoundDatasetsError):
        return 0


def publish_target(target: CleanupTarget) -> None:
    """Publish a target unless its Hub dataset is already verified nonempty."""
    existing_rows = hub_row_count(target.repo_id)
    if existing_rows:
        print(
            f"[cleanup] {target.job_name}: {target.repo_id} already verified ({existing_rows} rows); skip"
        )
        return

    temporary_root = Path(tempfile.mkdtemp(prefix=f"{target.job_name}-"))
    try:
        job_dir, copied = materialize_target_trials(target, temporary_root)
        trial_count, average_turns, exceptions = realness_summary(job_dir)
        print(
            f"[cleanup] {target.job_name}: copied={copied} trials={trial_count} "
            f"avg_turns={average_turns:.3f} exceptions={exceptions}",
            flush=True,
        )
        if average_turns <= MIN_REAL_AVERAGE_TURNS:
            raise RuntimeError(
                f"{target.job_name} failed realness gate: avg_turns={average_turns:.3f}"
            )

        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.harbor.make_and_upload_trace_dataset",
                "--job_dir",
                str(job_dir),
                "--repo_id",
                target.repo_id,
                "--episodes",
                "last",
                "--no_literal_tokens",
                "--single_commit",
                "--skip_register",
            ],
            check=True,
        )
        rows = hub_row_count(target.repo_id)
        if rows == 0:
            raise RuntimeError(
                f"{target.repo_id} uploaded but did not reload with any rows"
            )
        print(
            f"[cleanup] {target.job_name}: verified {target.repo_id} ({rows} rows)",
            flush=True,
        )
    finally:
        shutil.rmtree(temporary_root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        action="append",
        required=True,
        type=parse_target,
        help="job_name|s3://bucket/prefix[,s3://bucket/prefix...]|penfever/repo; repeatable",
    )
    args = parser.parse_args()
    for target in args.target:
        publish_target(target)


if __name__ == "__main__":
    main()
