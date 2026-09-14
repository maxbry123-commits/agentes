"""Where a cloud run's files land on the machine the user sits at, and what they are told.

A deliverable the user cannot find has not been delivered, so the two things worth pinning
are the folder (Downloads, because that is where people look) and the honesty of the list:
a file that was refused must still appear, with its reason, and must never be fetched.
"""

import os

import pytest

from backend.apps.workflows.cloud.client import CloudRun, CloudRunFile
from backend.apps.workflows.cloud.run_files import (
    described,
    downloads_root,
    fetch_missing,
    local_path_for,
    safe_component,
    run_folder,
)
from backend.apps.workflows.models import Workflow


def p_run(**overrides) -> CloudRun:
    body = {
        "id": "run-abcdef123456",
        "status": "succeeded",
        "finished_at": 1_785_000_000_000,
        "files": [],
    }
    body.update(overrides)
    return CloudRun.model_validate(body)


def test_files_land_in_downloads_because_that_is_where_people_look() -> None:
    root = downloads_root()
    assert root.endswith(os.path.join("OpenSwarm"))
    assert os.path.expanduser("~") in root


def test_a_run_gets_its_own_folder_named_so_a_list_of_them_reads_as_history() -> None:
    workflow = Workflow(title="Weekly numbers")
    folder = run_folder(workflow, p_run())
    assert "Weekly numbers" in folder
    # The run id's head disambiguates two runs in the same minute without being a wall of hex.
    assert "run-abcd" in folder


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Weekly numbers", "Weekly numbers"),
        ("bad/name", "bad-name"),
        ("../escape", "-escape"),
        ("with:colon", "with-colon"),
        ("", "untitled"),
        ("...", "untitled"),
    ],
)
def test_a_title_is_made_safe_without_becoming_unrecognisable(raw: str, expected: str) -> None:
    assert safe_component(raw) == expected


def test_a_nested_run_path_stays_nested_locally() -> None:
    target = local_path_for("/tmp/folder", CloudRunFile(id="f1", path="notes/method.txt", size_bytes=5))
    assert target == os.path.join("/tmp/folder", "notes", "method.txt")


def test_a_path_that_tries_to_climb_out_cannot(tmp_path) -> None:
    target = local_path_for(str(tmp_path), CloudRunFile(id="f1", path="../../etc/passwd", size_bytes=1))
    assert os.path.abspath(target).startswith(str(tmp_path))


def test_a_file_not_yet_downloaded_reports_no_local_path_rather_than_a_broken_one(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.downloads_root", lambda: str(tmp_path))
    run = p_run(files=[{"id": "f1", "path": "summary.md", "size_bytes": 42}])
    described_files = described(Workflow(title="W"), run)

    assert len(described_files) == 1
    assert described_files[0].local_path is None


def test_a_file_already_on_disk_is_reported_at_its_real_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.downloads_root", lambda: str(tmp_path))
    workflow = Workflow(title="W")
    run = p_run(files=[{"id": "f1", "path": "summary.md", "size_bytes": 5}])
    target = local_path_for(run_folder(workflow, run), run.files[0])
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(b"hello")

    assert described(workflow, run)[0].local_path == target


def test_a_refused_file_is_listed_with_its_reason_and_never_fetched(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.downloads_root", lambda: str(tmp_path))
    workflow = Workflow(title="W")
    run = p_run(files=[
        {"id": "f1", "path": "render.mp4", "size_bytes": 999, "refusal": "it is 512.0 MB and the limit is 20.0 MB"},
    ])

    listed = described(workflow, run)
    assert listed[0].refusal is not None
    assert listed[0].local_path is None

    asked: list = []

    async def p_never(*args, **kwargs):
        asked.append(args)
        return b""

    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.cloud.download_run_file", p_never)
    import asyncio

    asyncio.run(fetch_missing("hosted-1", workflow, [run]))
    assert asked == [], "a file that exists nowhere must never be requested"


def test_a_download_that_fails_leaves_the_history_readable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.downloads_root", lambda: str(tmp_path))
    workflow = Workflow(title="W")
    run = p_run(files=[{"id": "f1", "path": "summary.md", "size_bytes": 5}])

    async def p_boom(*args, **kwargs):
        from backend.apps.workflows.cloud.client import CloudUnreachable

        raise CloudUnreachable("offline")

    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.cloud.download_run_file", p_boom)
    import asyncio

    asyncio.run(fetch_missing("hosted-1", workflow, [run]))
    assert described(workflow, run)[0].local_path is None


def test_a_downloaded_file_is_written_whole_or_not_at_all(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.downloads_root", lambda: str(tmp_path))
    workflow = Workflow(title="W")
    run = p_run(files=[{"id": "f1", "path": "notes/summary.md", "size_bytes": 5}])

    async def p_ok(*args, **kwargs):
        return b"hello"

    monkeypatch.setattr("backend.apps.workflows.cloud.run_files.cloud.download_run_file", p_ok)
    import asyncio

    asyncio.run(fetch_missing("hosted-1", workflow, [run]))
    target = local_path_for(run_folder(workflow, run), run.files[0])
    with open(target, "rb") as handle:
        assert handle.read() == b"hello"
    # The .part file is the whole point of the atomic rename: no half file is ever visible.
    assert not os.path.exists(f"{target}.part")
