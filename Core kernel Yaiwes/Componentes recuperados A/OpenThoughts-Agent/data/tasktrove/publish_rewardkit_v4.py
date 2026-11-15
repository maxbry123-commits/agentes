#!/usr/bin/env python3
"""Publish a validated RewardKit migration as TaskTrove v4.0."""

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

from data.tasktrove.rewardkit_migration import DATASET_VERSION_MAP

REPO_ID = "open-thoughts/TaskTrove"
NONIDENTICAL_STANDALONES = {
    "laion__glaive-code-assistant-sandboxes-verified",
    "laion__stackexchange-codereview-sandboxes-verified",
    "laion__stackexchange-overflow-sandboxes-verified",
    "laion__stackexchange-superuser-sandboxes-verified",
    "laion__stackexchange-tezos-sandboxes-verified",
    "laion__stackexchange-unix-sandboxes-verified",
}


def v4_readme(source: str, manifest: dict[str, object]) -> str:
    note = (
        "> **v4.0 (current)** — RewardKit LLM-judge migration — replaces all 22 "
        "TaskTrove dataset versions that embed hand-written LiteLLM/OpenAI judges. "
        f"The full migration covers {manifest['total_migrated_rows']:,} judge-backed "
        f"tasks across {manifest['total_rows']:,} rows. Judgeable tasks now use Harbor "
        "RewardKit with root-level TOML rubrics and structured outputs. Missing or empty "
        "`/app/response.txt` and `/app/answer.txt` remains a scoreable zero; otherwise the "
        "verifier does not prewrite a reward, does not use `|| true`, and lets judge "
        "authentication, quota, rate-limit, timeout, transport, and server errors "
        "propagate without `reward.json`, so Harbor classifies them as infrastructure "
        "failures and retries them. CFBench and SysBench retain their deterministic gates "
        "and invoke RewardKit only after those gates pass. Every replacement preserves "
        "its source row count, remains above the 300-task floor, and is hosted only inside "
        "TaskTrove. Fifteen affected standalone repositories are retired after publication: "
        "nine were byte-identical to TaskTrove, while six nonidentical Glaive/StackExchange "
        "snapshots are preserved under the `deprecated` config before deletion. All rewards "
        "from the superseded judge implementations are excluded.\n>\n"
    )
    current = "> **v3.42 (current)**"
    if current not in source:
        raise ValueError("README does not identify v3.42 as current")
    return source.replace(current, note + "> **v3.42**", 1)


def standalone_repo(dataset_name: str) -> str:
    return dataset_name.replace("__", "/", 1)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_readme(stage: Path, revision: str, manifest: dict[str, object]) -> Path:
    source = Path(
        hf_hub_download(
            REPO_ID,
            "README.md",
            repo_type="dataset",
            revision=revision,
        )
    ).read_text()
    output = stage / "README-v4.md"
    output.write_text(v4_readme(source, manifest))
    return output


def stage_deprecated(stage: Path) -> dict[str, Path]:
    outputs = {}
    for dataset_name in sorted(NONIDENTICAL_STANDALONES):
        outputs[dataset_name] = Path(
            hf_hub_download(
                standalone_repo(dataset_name),
                "tasks.parquet",
                repo_type="dataset",
                local_dir=stage / "standalone-provenance" / dataset_name,
            )
        )
    return outputs


def publish(stage: Path, revision: str) -> str:
    manifest = json.loads((stage / "manifest.json").read_text())
    if manifest["source_revision"] != revision:
        raise ValueError("manifest revision does not match requested revision")
    api = HfApi(token=os.environ["HF_TOKEN"])
    if api.repo_info(REPO_ID, repo_type="dataset").sha != revision:
        raise ValueError("TaskTrove changed after the migration build")

    readme = stage_readme(stage, revision, manifest)
    deprecated = stage_deprecated(stage)
    operations: list[CommitOperationAdd | CommitOperationDelete] = [
        CommitOperationAdd("README.md", readme)
    ]
    for dataset in manifest["datasets"]:
        operations.extend(
            [
                CommitOperationDelete(dataset["source_dataset"]),
                CommitOperationAdd(
                    f"{dataset['output_dataset']}/tasks.parquet",
                    stage / dataset["output"],
                ),
            ]
        )
    for dataset_name, path in deprecated.items():
        operations.append(
            CommitOperationAdd(
                f"deprecated/{dataset_name}/tasks.parquet",
                path,
            )
        )

    commit = api.create_commit(
        REPO_ID,
        repo_type="dataset",
        operations=operations,
        commit_message="TaskTrove v4.0: migrate LLM judges to RewardKit",
        parent_commit=revision,
        num_threads=2,
    )
    return commit.oid


def verify_and_retire(stage: Path, commit: str) -> None:
    manifest = json.loads((stage / "manifest.json").read_text())
    api = HfApi(token=os.environ["HF_TOKEN"])
    tree = {
        item.path: item
        for item in api.list_repo_tree(
            REPO_ID,
            repo_type="dataset",
            revision=commit,
            recursive=True,
            expand=True,
        )
    }
    for dataset in manifest["datasets"]:
        target = f"{dataset['output_dataset']}/tasks.parquet"
        item = tree[target]
        if item.lfs is None or item.lfs.sha256 != dataset["output_sha256"]:
            raise ValueError(f"remote hash mismatch: {target}")
        if f"{dataset['source_dataset']}/tasks.parquet" in tree:
            raise ValueError(f"superseded source remains: {dataset['source_dataset']}")
    readme = Path(
        hf_hub_download(
            REPO_ID,
            "README.md",
            repo_type="dataset",
            revision=commit,
        )
    ).read_text()
    if not re.search(r"^> \*\*v4\.0 \(current\)\*\*", readme, re.MULTILINE):
        raise ValueError("remote README does not identify v4.0")
    for dataset_name in NONIDENTICAL_STANDALONES:
        remote_path = f"deprecated/{dataset_name}/tasks.parquet"
        if remote_path not in tree:
            raise ValueError(f"missing deprecated provenance: {dataset_name}")
        local_path = stage / "standalone-provenance" / dataset_name / "tasks.parquet"
        item = tree[remote_path]
        if item.lfs is None or item.lfs.sha256 != file_sha256(local_path):
            raise ValueError(f"deprecated provenance hash mismatch: {dataset_name}")

    api.create_tag(REPO_ID, tag="v4.0", repo_type="dataset", revision=commit)
    for dataset_name in DATASET_VERSION_MAP:
        repo = standalone_repo(dataset_name)
        if api.repo_exists(repo, repo_type="dataset"):
            api.delete_repo(repo, repo_type="dataset")
        if api.repo_exists(repo, repo_type="dataset"):
            raise ValueError(
                f"standalone repository still exists after deletion: {repo}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--verify-and-retire", action="store_true")
    args = parser.parse_args()

    commit = args.commit
    if args.publish:
        commit = publish(args.stage, args.revision)
        print(commit)
    if args.verify_and_retire:
        if commit is None:
            raise ValueError(
                "--commit is required when publication is not in this process"
            )
        verify_and_retire(args.stage, commit)
        print(f"verified {commit}, tagged v4.0, and retired standalone repositories")


if __name__ == "__main__":
    main()
