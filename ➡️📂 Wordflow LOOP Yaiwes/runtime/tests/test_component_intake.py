from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from runtime.src.core.component_intake import (
    CANONICAL_MOTORS,
    ComponentRequest,
    IntakeError,
    build_queue,
    persist_queue,
    prepare_motor,
    validate_request,
    verify_readback,
)


PINNED = "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_download_is_pinned_locked_and_not_auto_authorized():
    request = ComponentRequest(
        "R1",
        "DOWNLOAD_EXTRACT",
        "https://github.com/octocat/Hello-World",
        "➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/intake/out",
        expected_ref=PINNED,
    )
    invocation = validate_request(request)
    assert invocation.motor_path == CANONICAL_MOTORS["DOWNLOAD_EXTRACT"]["path"]
    assert invocation.execution_authorized is False
    assert "VERIFY_PINNED_SOURCE_OR_ARCHIVE_SHA256" in invocation.required_checks


def test_invalid_ref_and_outside_paths_fail_closed():
    with pytest.raises(IntakeError, match="PINNED_SOURCE_REF_REQUIRED"):
        validate_request(
            ComponentRequest(
                "R2",
                "DOWNLOAD_EXTRACT",
                "https://github.com/example/project",
                "➡️📂 Wordflow LOOP Yaiwes/out",
                expected_ref="HEAD",
            )
        )
    with pytest.raises(IntakeError, match="DESTINATION_OUTSIDE_AUTHORIZED_ROOT"):
        validate_request(ComponentRequest("R3", "COPY", "➡️📂 Wordflow LOOP Yaiwes/source", "elsewhere/out"))


def test_duplicate_queue_request_fails_closed():
    request = ComponentRequest(
        "R4", "MOVE", "➡️📂 Wordflow LOOP Yaiwes/source", "➡️📂 Wordflow LOOP Yaiwes/dest"
    )
    with pytest.raises(IntakeError, match="DUPLICATE_REQUEST_ID"):
        build_queue((request, request))


def test_extract_adapter_runs_canonical_motor_and_verifies_readback(tmp_path: Path):
    root = repo_root()
    authorized = tmp_path / "➡️📂 Wordflow LOOP Yaiwes"
    authorized.mkdir()
    archive = authorized / "input.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("nested/payload.txt", "yaiwes-g012\n")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    request = ComponentRequest(
        "R5",
        "EXTRACT",
        "➡️📂 Wordflow LOOP Yaiwes/input.zip",
        "➡️📂 Wordflow LOOP Yaiwes/output",
        expected_sha256=digest,
    )
    prepared = prepare_motor(request, repo_root=root, authorized_root=authorized)
    proc = subprocess.run(
        [sys.executable, str(prepared.motor_file)],
        env=prepared.env(),
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    verified = verify_readback(prepared, result, destination=authorized / "output")
    assert verified["verdict"] == "VERIFIED_CLOSED"
    payload = authorized / "output/nested/payload.txt"
    assert payload.read_text() == "yaiwes-g012\n"
    payload.write_text("tampered", encoding="utf-8")
    with pytest.raises(IntakeError, match="DESTINATION_TREE_HASH_MISMATCH"):
        verify_readback(prepared, result, destination=authorized / "output")


def test_download_queue_persistence_requires_authorization_and_readback(tmp_path: Path):
    root = repo_root()
    authorized = tmp_path / "➡️📂 Wordflow LOOP Yaiwes"
    authorized.mkdir()
    request = ComponentRequest(
        "R6",
        "DOWNLOAD_EXTRACT",
        "https://github.com/octocat/Hello-World",
        "➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/intake/out",
        expected_ref=PINNED,
    )
    prepared = prepare_motor(request, repo_root=root, authorized_root=authorized)
    with pytest.raises(PermissionError, match="MUTATION_NOT_AUTHORIZED"):
        persist_queue(prepared, mutation_authorized=False)
    queue_path = persist_queue(prepared, mutation_authorized=True)
    payload = json.loads(queue_path.read_text())
    assert payload["queue"][0]["source_ref"] == PINNED
    assert payload["queue"][0]["publish"] is False


def test_symlink_destination_and_archive_hash_mismatch_fail_closed(tmp_path: Path):
    root = repo_root()
    authorized = tmp_path / "➡️📂 Wordflow LOOP Yaiwes"
    outside = tmp_path / "outside"
    authorized.mkdir()
    outside.mkdir()
    (authorized / "escape").symlink_to(outside, target_is_directory=True)
    archive = authorized / "input.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("payload.txt", "data")
    escaped = ComponentRequest(
        "R7",
        "EXTRACT",
        "➡️📂 Wordflow LOOP Yaiwes/input.zip",
        "➡️📂 Wordflow LOOP Yaiwes/escape/out",
        expected_sha256="0" * 64,
    )
    with pytest.raises(IntakeError, match="DESTINATION_OUTSIDE_AUTHORIZED_ROOT"):
        prepare_motor(escaped, repo_root=root, authorized_root=authorized)

    mismatched = ComponentRequest(
        "R8",
        "EXTRACT",
        "➡️📂 Wordflow LOOP Yaiwes/input.zip",
        "➡️📂 Wordflow LOOP Yaiwes/out",
        expected_sha256="0" * 64,
    )
    with pytest.raises(IntakeError, match="ARCHIVE_SHA256_MISMATCH"):
        prepare_motor(mismatched, repo_root=root, authorized_root=authorized)
