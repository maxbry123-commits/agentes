"""Replace the broken Stack-Pytest source in TaskTrove v3.7."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


TASKTROVE_REPO = "open-thoughts/TaskTrove"
SOURCE_REPO = "laion/exp_rpt_stack-pytest-large-v2"
OLD_SUBDIR = "DCAgent__exp_rpt_stack-pytest-large"
NEW_SUBDIR = "laion__exp_rpt_stack-pytest-large-v2"


def v3_7_readme(previous: str) -> str:
    """Prepend the v3.7 release note to the current TaskTrove card."""
    release = (
        "> **v3.7 (current)** — replacement: DCAgent/exp_rpt_stack-pytest-large "
        "(5,000 tasks) was removed because its verifier installed only pytest and "
        "omitted task dependencies, causing widespread collection failures and "
        "zero-reward RL rollouts. laion/exp_rpt_stack-pytest-large-v2 replaces "
        "it with 2,552 dependency-complete, deterministic-pytest tasks. It has one "
        "shared snapshot, a private-reference oracle rerun of 40/40 reward=1.0, "
        "and a public-form 200-task smoke with 0 exceptions and 62.2% positive "
        "rewards. Public artifacts contain no reference solutions. No other "
        "TaskTrove dataset changed.\n>\n"
    )
    marker = "> **v3.6 (current)**"
    if marker not in previous:
        raise ValueError(
            "TaskTrove README no longer has the expected v3.6 release marker"
        )
    return previous.replace(marker, release + "> **v3.6**", 1)


def stage_release(stage: Path) -> None:
    """Materialize the only two files to upload for the scoped replacement."""
    api = HfApi()
    if not api.file_exists(SOURCE_REPO, "tasks.parquet", repo_type="dataset"):
        raise ValueError(f"{SOURCE_REPO} does not contain tasks.parquet")
    if not api.file_exists(
        TASKTROVE_REPO, f"{OLD_SUBDIR}/tasks.parquet", repo_type="dataset"
    ):
        raise ValueError(
            f"{TASKTROVE_REPO} does not contain {OLD_SUBDIR}/tasks.parquet"
        )

    readme_path = Path(
        hf_hub_download(TASKTROVE_REPO, "README.md", repo_type="dataset")
    )
    target_tasks = Path(
        hf_hub_download(SOURCE_REPO, "tasks.parquet", repo_type="dataset")
    )
    (stage / NEW_SUBDIR).mkdir(parents=True)
    (stage / "README.md").write_text(
        v3_7_readme(readme_path.read_text()), encoding="utf-8"
    )
    shutil.copy2(target_tasks, stage / NEW_SUBDIR / "tasks.parquet")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.stage.exists():
        if any(args.stage.iterdir()):
            raise ValueError(f"stage must be empty: {args.stage}")
    else:
        args.stage.mkdir(parents=True)
    stage_release(args.stage)
    print(f"staged {NEW_SUBDIR}/tasks.parquet and README.md in {args.stage}")
    if not args.execute:
        return 0

    HfApi().upload_folder(
        repo_id=TASKTROVE_REPO,
        repo_type="dataset",
        folder_path=args.stage,
        delete_patterns=[f"{OLD_SUBDIR}/**"],
        commit_message="TaskTrove v3.7: replace broken Stack-Pytest tasks",
    )
    print("uploaded TaskTrove v3.7 replacement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
