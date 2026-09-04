from pathlib import Path

from hpc.hf_utils import resolve_dataset_path
from hpc.launch_utils import convert_parquet_to_tasks
from scripts.harbor.tasks_parquet_converter import find_tasks, to_parquet


def _write_source_tasks(root: Path, count: int) -> Path:
    tasks_dir = root / "source_tasks"
    for index in range(count):
        task = tasks_dir / f"task-{index:03d}"
        task.mkdir(parents=True)
        (task / "instruction.md").write_text(f"task {index}\n")
    return tasks_dir


def test_resolve_dataset_selector_downloads_only_pinned_subdirectory(
    tmp_path, monkeypatch
):
    snapshot = tmp_path / "snapshot"
    selected = snapshot / "org__dataset"
    selected.mkdir(parents=True)
    calls = []

    def fake_snapshot_download(**kwargs):
        calls.append(kwargs)
        return str(snapshot)

    monkeypatch.setattr("huggingface_hub.snapshot_download", fake_snapshot_download)

    resolved = resolve_dataset_path(
        "open-thoughts/TaskTrove@abc123::org__dataset", verbose=False
    )

    assert resolved == str(selected)
    assert calls == [
        {
            "repo_id": "open-thoughts/TaskTrove",
            "repo_type": "dataset",
            "revision": "abc123",
            "allow_patterns": ["org__dataset/**"],
        }
    ]


def test_convert_parquet_to_tasks_caps_large_dataset_at_exact_cohort_size(tmp_path):
    source = _write_source_tasks(tmp_path, 5)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    to_parquet(source, snapshot / "tasks.parquet", find_tasks(source), compression="gz")

    cohort = Path(
        convert_parquet_to_tasks(
            str(snapshot),
            "org/dataset",
            datasets_dir=str(tmp_path / "datasets"),
            cohort_size=3,
        )
    )

    tasks = find_tasks(cohort, recursive=True)
    assert [task.name for task in tasks] == ["task-000", "task-001", "task-002"]


def test_convert_parquet_to_tasks_repeats_small_dataset_to_exact_cohort_size(tmp_path):
    source = _write_source_tasks(tmp_path, 2)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    to_parquet(source, snapshot / "tasks.parquet", find_tasks(source), compression="gz")

    cohort = Path(
        convert_parquet_to_tasks(
            str(snapshot),
            "org/dataset",
            datasets_dir=str(tmp_path / "datasets"),
            cohort_size=5,
        )
    )

    tasks = find_tasks(cohort, recursive=True)
    instructions = sorted((task / "instruction.md").read_text() for task in tasks)
    assert len(tasks) == 5
    assert instructions == ["task 0\n", "task 0\n", "task 0\n", "task 1\n", "task 1\n"]
