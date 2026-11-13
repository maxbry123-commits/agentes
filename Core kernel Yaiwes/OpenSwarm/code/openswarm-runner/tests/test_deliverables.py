"""What the run made, what comes home, and what is refused out loud instead of silently.

The caps are the point. A truncated file is worse than a refused one, and a file that
vanishes with no sentence attached is the failure the whole list exists to prevent.
"""

import os

import pytest

from runner.results.deliverables import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    collect,
    human_bytes,
)
from runner.results.report import deliver_files
from runner.run_spec import CallbackTarget


def write(root, relative: str, payload: bytes) -> str:
    path = os.path.join(str(root), relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(payload)
    return path


def test_a_missing_workspace_is_an_empty_harvest_not_a_crash(tmp_path) -> None:
    assert collect(str(tmp_path / "never-made")).files == []


def test_ordinary_files_are_collected_with_their_digest(tmp_path) -> None:
    write(tmp_path, "report.md", b"# Digest\n")
    write(tmp_path, "data/rows.csv", b"a,b\n1,2\n")

    # Walk order, and it is fixed: this directory's own files first, then subdirectories in name
    # order, so a run's file list does not shuffle between two identical runs.
    harvest = collect(str(tmp_path))
    assert [f.path for f in harvest.files] == ["report.md", "data/rows.csv"]
    assert harvest.files[0].size_bytes == len(b"# Digest\n")
    # A digest travels with every file, so a corrupted upload is detectable rather than assumed fine.
    assert len(harvest.files[0].sha256) == 64
    assert harvest.refused == []


def test_machinery_is_not_a_deliverable(tmp_path) -> None:
    write(tmp_path, "report.md", b"keep me")
    write(tmp_path, ".git/config", b"[core]")
    write(tmp_path, "node_modules/left-pad/index.js", b"module.exports=1")
    write(tmp_path, "__pycache__/x.pyc", b"\x00")
    write(tmp_path, ".claude/worktrees/probe/README", b"scratch")

    assert [f.path for f in collect(str(tmp_path)).files] == ["report.md"]


def test_an_empty_file_is_neither_delivered_nor_complained_about(tmp_path) -> None:
    write(tmp_path, "touched.txt", b"")
    harvest = collect(str(tmp_path))
    assert harvest.files == []
    assert harvest.refused == []


def test_a_file_over_the_cap_is_refused_whole_and_says_why(tmp_path) -> None:
    write(tmp_path, "render.mp4", b"x" * (MAX_FILE_BYTES + 1))
    write(tmp_path, "notes.md", b"still fine")

    harvest = collect(str(tmp_path))
    assert [f.path for f in harvest.files] == ["notes.md"]
    assert len(harvest.refused) == 1
    assert harvest.refused[0].path == "render.mp4"
    assert "cannot exceed" in harvest.refused[0].reason
    # Never a fragment: an over-sized file is absent, not shortened.
    assert all(f.path != "render.mp4" for f in harvest.files)


def test_the_run_total_stops_collecting_but_keeps_what_already_fit(tmp_path) -> None:
    chunk = b"x" * MAX_FILE_BYTES
    for index in range(MAX_TOTAL_BYTES // MAX_FILE_BYTES + 1):
        write(tmp_path, f"blob-{index}.bin", chunk)

    harvest = collect(str(tmp_path))
    assert harvest.total_bytes() <= MAX_TOTAL_BYTES
    assert len(harvest.files) >= 1
    assert harvest.refused, "the file that blew the budget must be named, not dropped"
    assert "limit is" in harvest.refused[0].reason


def test_too_many_files_refuses_the_extras_by_name(tmp_path) -> None:
    for index in range(MAX_FILES + 3):
        write(tmp_path, f"note-{index:03d}.txt", b"hi")

    harvest = collect(str(tmp_path))
    assert len(harvest.files) == MAX_FILES
    assert len(harvest.refused) == 3
    assert all("maximum of" in item.reason for item in harvest.refused)


def test_a_symlink_out_of_the_workspace_is_never_followed(tmp_path) -> None:
    secret = tmp_path / "outside" / "id_rsa"
    os.makedirs(secret.parent, exist_ok=True)
    secret.write_text("PRIVATE KEY")
    workspace = tmp_path / "ws"
    os.makedirs(workspace, exist_ok=True)
    os.symlink(str(secret), str(workspace / "borrowed.pem"))

    assert collect(str(workspace)).files == []


def test_with_nowhere_to_send_files_the_run_says_so_per_file(tmp_path) -> None:
    write(tmp_path, "report.md", b"the answer")
    reported = deliver_files(None, str(tmp_path), collect(str(tmp_path)))

    assert len(reported) == 1
    assert reported[0].delivered is False
    assert "nowhere to send files" in (reported[0].reason or "")


def test_a_control_plane_with_no_file_route_is_reported_not_guessed(tmp_path) -> None:
    write(tmp_path, "report.md", b"the answer")
    callback = CallbackTarget(url="https://cloud.test/report", token="two-party")
    assert callback.artifacts_url is None

    reported = deliver_files(callback, str(tmp_path), collect(str(tmp_path)))
    assert reported[0].delivered is False


def test_refusals_reach_the_report_even_when_nothing_was_delivered(tmp_path) -> None:
    write(tmp_path, "render.mp4", b"x" * (MAX_FILE_BYTES + 1))
    reported = deliver_files(None, str(tmp_path), collect(str(tmp_path)))

    assert len(reported) == 1
    assert reported[0].path == "render.mp4"
    assert reported[0].delivered is False
    assert "cannot exceed" in (reported[0].reason or "")


@pytest.mark.parametrize(
    "count,expected",
    [(512, "512 B"), (2048, "2 KB"), (5 * 1024 * 1024, "5.0 MB"), (3 * 1024**3, "3.0 GB")],
)
def test_sizes_are_written_the_way_a_person_reads_them(count: int, expected: str) -> None:
    assert human_bytes(count) == expected


def test_a_failed_run_still_hands_over_what_it_managed_to_make(tmp_path, monkeypatch) -> None:
    """A workflow that dies on step 3 may have written a perfectly good report on step 1."""
    from runner import main
    from runner.run_spec import RunSpec

    write(tmp_path, "partial-report.md", b"# What I got through\n")
    spec = RunSpec.model_validate({
        "run_id": "cr-fail",
        "workflow": {"id": "wf-1", "steps": [{"id": "s1", "text": "go"}]},
        "credentials": [{"provider": "anthropic", "auth_type": "api_key", "api_key": "sk-test"}],
    })

    sent: list = []
    monkeypatch.setattr(main, "send_report", lambda callback, report: sent.append(report) or True)
    code = main.p_fail(spec, "failure", "step 3 blew up", main.EXIT_WORKFLOW_FAILED, str(tmp_path))

    assert code == main.EXIT_WORKFLOW_FAILED
    assert [f.path for f in sent[0].files] == ["partial-report.md"]


def test_a_failure_with_no_workspace_reports_no_files_rather_than_guessing(monkeypatch) -> None:
    from runner import main

    sent: list = []
    monkeypatch.setattr(main, "send_report", lambda callback, report: sent.append(report) or True)
    main.p_fail(None, "failure", "bad spec", main.EXIT_BAD_SPEC)

    assert sent[0].files == []
