#!/usr/bin/env python3
"""Publish and verify the TaskTrove v4.1 data-quality release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from huggingface_hub import (
    CommitOperationAdd,
    CommitOperationDelete,
    HfApi,
    hf_hub_download,
)

REPO_ID = "open-thoughts/TaskTrove"
SOURCE_REVISION = "81820c33ba26d705b9ea7ebac2d090d70fac93f4"
TAG = "v4.1"
UPLOAD_THREADS = 1


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_label(name: str) -> str:
    return name.replace("__", "/", 1)


def updated_readme(source: str, manifest: dict[str, object]) -> str:
    datasets = manifest["datasets"]
    removals = manifest["removals"]
    quarantines = manifest["quarantines"]
    replacement_rows = sum(int(dataset["output_rows"]) for dataset in datasets)
    replacement_lines = "\n".join(
        f"> - `{dataset_label(str(dataset['source_dataset']))}` → "
        f"`{dataset_label(str(dataset['output_dataset']))}` "
        f"({int(dataset['source_rows']):,} → {int(dataset['output_rows']):,} tasks)"
        for dataset in datasets
    )
    removal_lines = "\n".join(
        f"> - `{dataset_label(str(dataset['dataset']))}`: {dataset['reason']}"
        for dataset in removals
    )
    quarantine_lines = "\n".join(
        f"> - `{dataset_label(str(dataset['dataset']))}`: {dataset['reason']}"
        for dataset in quarantines
    )
    note = (
        f"> **v4.1 (current)** — data-quality survey remediation — validates 3,400 "
        f"traces across 34 statistically flagged v3.42 sources. This release "
        f"publishes {len(datasets)} fail-closed or semantic-verifier replacements "
        f"covering {replacement_rows:,} retained tasks. Verifier code, data, runtime, "
        "dependency, collection, and result-parsing failures now leave no reward for "
        "Harbor to classify as infrastructure; ordinary wrong or missing agent answers "
        "remain scoreable zeroes. Every replacement remains above the 300-task floor.\n"
        ">\n"
        "> Replacements:\n"
        f"{replacement_lines}\n"
        ">\n"
        "> Removed mixed sources:\n"
        f"{removal_lines}\n"
        ">\n"
        "> Retained pure-source quarantines (exclude their current rewards):\n"
        f"{quarantine_lines}\n"
        ">\n"
        "> Standalone repositories for superseded, removed, or quarantined broken "
        "versions are retired "
        "only after the main-repository commit and tag are verified. Any nonidentical "
        "standalone Parquet is preserved under `deprecated/` first.\n>\n"
    )
    marker = "> **v4.0 (current)**"
    if marker not in source:
        raise ValueError("README does not identify v4.0 as current")
    return source.replace(marker, note + "> **v4.0**", 1)


def repo_files(api: HfApi, repo: str, revision: str) -> dict[str, object]:
    return {
        item.path: item
        for item in api.list_repo_tree(
            repo,
            repo_type="dataset",
            revision=revision,
            recursive=True,
            expand=True,
        )
        if hasattr(item, "blob_id")
    }


def file_identity(item: object) -> tuple[str, int]:
    lfs = getattr(item, "lfs", None)
    digest = lfs.sha256 if lfs is not None else str(getattr(item, "blob_id"))
    return digest, int(getattr(item, "size"))


def standalone_parquet(api: HfApi, repo: str) -> object | None:
    if not api.repo_exists(repo, repo_type="dataset"):
        return None
    files = repo_files(api, repo, revision="main")
    return files.get("tasks.parquet")


def prepare_deprecated(
    api: HfApi,
    stage: Path,
    manifest: dict[str, object],
) -> tuple[dict[str, Path], list[str]]:
    source_hashes = {
        str(dataset["source_dataset"]): str(dataset["source_sha256"])
        for dataset in manifest["datasets"]
    }
    source_hashes.update(
        {
            str(dataset["dataset"]): str(dataset["sha256"])
            for dataset in manifest["removals"]
        }
    )
    source_hashes.update(
        {
            str(dataset["dataset"]): str(dataset["sha256"])
            for dataset in manifest["unchanged_standalone_retirements"]
        }
    )
    deprecated: dict[str, Path] = {}
    existing: list[str] = []
    for dataset, source_hash in sorted(source_hashes.items()):
        repo = dataset_label(dataset)
        remote = standalone_parquet(api, repo)
        if remote is None:
            continue
        existing.append(repo)
        lfs = getattr(remote, "lfs", None)
        remote_hash = lfs.sha256 if lfs is not None else None
        if remote_hash == source_hash:
            continue
        path = Path(
            hf_hub_download(
                repo,
                "tasks.parquet",
                repo_type="dataset",
                token=api.token,
                local_dir=stage / "standalone-provenance" / dataset,
            )
        )
        if file_sha256(path) == source_hash:
            raise ValueError(f"standalone metadata mismatch for {repo}")
        deprecated[dataset] = path
    return deprecated, existing


def stage_readme(stage: Path, manifest: dict[str, object]) -> Path:
    source = Path(
        hf_hub_download(
            REPO_ID,
            "README.md",
            repo_type="dataset",
            revision=SOURCE_REVISION,
        )
    ).read_text()
    path = stage / "README-v4.1.md"
    path.write_text(updated_readme(source, manifest))
    return path


def deleted_prefixes(manifest: dict[str, object]) -> tuple[str, ...]:
    datasets = [str(dataset["source_dataset"]) for dataset in manifest["datasets"]]
    datasets.extend(str(dataset["dataset"]) for dataset in manifest["removals"])
    return tuple(f"{dataset}/" for dataset in datasets)


def publish(stage: Path) -> str:
    manifest = json.loads((stage / "manifest.json").read_text())
    if manifest["source_revision"] != SOURCE_REVISION:
        raise ValueError("release manifest has the wrong source revision")
    api = HfApi(token=os.environ["HF_TOKEN"])
    if api.repo_info(REPO_ID, repo_type="dataset").sha != SOURCE_REVISION:
        raise ValueError("TaskTrove changed after the v4.1 build")
    if any(
        tag.name == TAG for tag in api.list_repo_refs(REPO_ID, repo_type="dataset").tags
    ):
        raise ValueError(f"tag already exists: {TAG}")

    current = repo_files(api, REPO_ID, SOURCE_REVISION)
    for dataset in manifest["datasets"]:
        source_path = f"{dataset['source_dataset']}/tasks.parquet"
        output_path = f"{dataset['output_dataset']}/tasks.parquet"
        if source_path not in current:
            raise ValueError(f"missing source dataset: {source_path}")
        if file_identity(current[source_path])[0] != dataset["source_sha256"]:
            raise ValueError(f"source hash mismatch: {source_path}")
        if output_path in current:
            raise ValueError(f"target dataset already exists: {output_path}")
    for dataset in manifest["removals"]:
        source_path = f"{dataset['dataset']}/tasks.parquet"
        if source_path not in current:
            raise ValueError(f"missing removal target: {source_path}")
        if file_identity(current[source_path])[0] != dataset["sha256"]:
            raise ValueError(f"removal target hash mismatch: {source_path}")
    for dataset in manifest["unchanged_standalone_retirements"]:
        source_path = f"{dataset['dataset']}/tasks.parquet"
        if source_path not in current:
            raise ValueError(f"missing quarantined source: {source_path}")
        if file_identity(current[source_path])[0] != dataset["sha256"]:
            raise ValueError(f"quarantined source hash mismatch: {source_path}")

    readme = stage_readme(stage, manifest)
    deprecated, standalone_repos = prepare_deprecated(api, stage, manifest)
    manifest["standalone_repositories"] = standalone_repos
    manifest["deprecated_standalones"] = {
        dataset: {
            "output": f"deprecated/{dataset}/tasks.parquet",
            "sha256": file_sha256(path),
        }
        for dataset, path in deprecated.items()
    }
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    operations: list[CommitOperationAdd | CommitOperationDelete] = [
        CommitOperationAdd("README.md", readme)
    ]
    for dataset in manifest["datasets"]:
        operations.append(CommitOperationDelete(str(dataset["source_dataset"])))
        operations.append(
            CommitOperationAdd(
                f"{dataset['output_dataset']}/tasks.parquet",
                stage / str(dataset["output"]),
            )
        )
    for dataset in manifest["removals"]:
        operations.append(CommitOperationDelete(str(dataset["dataset"])))
    for dataset, path in deprecated.items():
        operations.append(
            CommitOperationAdd(f"deprecated/{dataset}/tasks.parquet", path)
        )

    commit = api.create_commit(
        REPO_ID,
        repo_type="dataset",
        operations=operations,
        commit_message="TaskTrove v4.1: remediate data-quality survey findings",
        parent_commit=SOURCE_REVISION,
        num_threads=UPLOAD_THREADS,
    )
    return commit.oid


def verify_and_retire(stage: Path, commit: str) -> None:
    manifest = json.loads((stage / "manifest.json").read_text())
    api = HfApi(token=os.environ["HF_TOKEN"])
    before = repo_files(api, REPO_ID, SOURCE_REVISION)
    after = repo_files(api, REPO_ID, commit)
    prefixes = deleted_prefixes(manifest)

    expected_paths = {
        path for path in before if path != "README.md" and not path.startswith(prefixes)
    }
    expected_paths.add("README.md")
    expected_paths.update(
        f"{dataset['output_dataset']}/tasks.parquet" for dataset in manifest["datasets"]
    )
    expected_paths.update(
        data["output"] for data in manifest["deprecated_standalones"].values()
    )
    if set(after) != expected_paths:
        missing = sorted(expected_paths - set(after))
        extra = sorted(set(after) - expected_paths)
        raise ValueError(f"unexpected remote tree: missing={missing}, extra={extra}")

    for path, item in before.items():
        if path == "README.md" or path.startswith(prefixes):
            continue
        if file_identity(after[path]) != file_identity(item):
            raise ValueError(f"untouched file changed: {path}")
    for dataset in manifest["datasets"]:
        path = f"{dataset['output_dataset']}/tasks.parquet"
        if file_identity(after[path])[0] != dataset["output_sha256"]:
            raise ValueError(f"remote output hash mismatch: {path}")
    for dataset in manifest["removals"]:
        if any(path.startswith(f"{dataset['dataset']}/") for path in after):
            raise ValueError(f"removed dataset remains: {dataset['dataset']}")
    for dataset, data in manifest["deprecated_standalones"].items():
        if file_identity(after[data["output"]])[0] != data["sha256"]:
            raise ValueError(f"deprecated provenance hash mismatch: {dataset}")

    readme = Path(
        hf_hub_download(
            REPO_ID,
            "README.md",
            repo_type="dataset",
            revision=commit,
        )
    ).read_text()
    if not re.search(r"^> \*\*v4\.1 \(current\)\*\*", readme, re.MULTILINE):
        raise ValueError("remote README does not identify v4.1")

    api.create_tag(REPO_ID, tag=TAG, repo_type="dataset", revision=commit)
    for repo in manifest["standalone_repositories"]:
        if api.repo_exists(repo, repo_type="dataset"):
            api.delete_repo(repo, repo_type="dataset")
        if api.repo_exists(repo, repo_type="dataset"):
            raise ValueError(f"standalone repository remains: {repo}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--commit")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--verify-and-retire", action="store_true")
    args = parser.parse_args()

    commit = args.commit
    if args.publish:
        commit = publish(args.stage)
        print(commit)
    if args.verify_and_retire:
        if commit is None:
            raise ValueError("--commit is required without --publish")
        verify_and_retire(args.stage, commit)
        print(f"verified {commit}, tagged {TAG}, and retired standalone repositories")


if __name__ == "__main__":
    main()
