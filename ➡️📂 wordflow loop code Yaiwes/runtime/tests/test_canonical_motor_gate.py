from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runtime.src.core.canonical_motor_gate import build_motor_env, verify_motor


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_motor(motor_path: Path, env_update: dict[str, str]) -> dict[str, object]:
    env = os.environ.copy()
    env.update(env_update)
    proc = subprocess.run(
        [sys.executable, str(motor_path)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_copy_motor_blob_and_readback(tmp_path: Path) -> None:
    root = repo_root()
    verified = verify_motor(root, "copy")
    assert verified["actual_blob_sha"] == "3689924361ce4a1a9fde4ae2b6f6009c37a6042d"

    source = tmp_path / "copy-source"
    dest = tmp_path / "copy-dest"
    source.mkdir()
    payload = source / "sample.txt"
    payload.write_text("yaiwes-g011-copy\n", encoding="utf-8")
    expected = sha256(payload)

    env = build_motor_env(
        source,
        dest,
        tmp_path / "copy-state.json",
        authorized_root=tmp_path,
        mutation_authorized=True,
    )
    result = run_motor(root / str(verified["motor_path"]), env)

    copied = dest / "sample.txt"
    assert result["verdict"] == "VERIFIED_CLOSED"
    assert result["failed"] == 0
    assert result["pending"] == 0
    assert copied.is_file()
    assert payload.is_file()
    assert sha256(copied) == expected == sha256(payload)


def test_move_motor_blob_and_readback(tmp_path: Path) -> None:
    root = repo_root()
    verified = verify_motor(root, "move")
    assert verified["actual_blob_sha"] == "9a21facfe11327cf60a2afca8f415ad52f0ecbe5"

    source = tmp_path / "move-source"
    dest = tmp_path / "move-dest"
    source.mkdir()
    payload = source / "sample.txt"
    payload.write_text("yaiwes-g011-move\n", encoding="utf-8")
    expected = sha256(payload)

    env = build_motor_env(
        source,
        dest,
        tmp_path / "move-state.json",
        authorized_root=tmp_path,
        mutation_authorized=True,
    )
    result = run_motor(root / str(verified["motor_path"]), env)

    moved = dest / "sample.txt"
    assert result["verdict"] == "VERIFIED_CLOSED"
    assert result["failed"] == 0
    assert result["pending"] == 0
    assert moved.is_file()
    assert not payload.exists()
    assert sha256(moved) == expected


def test_gate_fails_closed_on_invalid_inputs(tmp_path: Path) -> None:
    root = repo_root()
    with pytest.raises(ValueError, match="^UNSUPPORTED_MOTOR_OPERATION$"):
        verify_motor(root, "delete")

    source = tmp_path / "same"
    source.mkdir()
    with pytest.raises(ValueError, match="^SOURCE_DESTINATION_COLLISION$"):
        build_motor_env(
            source,
            source,
            tmp_path / "state.json",
            authorized_root=tmp_path,
            mutation_authorized=True,
        )


def test_gate_requires_authorized_root_and_explicit_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest"

    with pytest.raises(ValueError, match="^AUTHORIZED_ROOT_REQUIRED$"):
        build_motor_env(source, dest, tmp_path / "state.json")
    assert not dest.exists()

    with pytest.raises(PermissionError, match="^MUTATION_NOT_AUTHORIZED$"):
        build_motor_env(
            source,
            dest,
            tmp_path / "state.json",
            authorized_root=tmp_path,
        )
    assert not dest.exists()


def test_gate_rejects_destination_and_state_escape_without_mutation(tmp_path: Path) -> None:
    authorized = tmp_path / "authorized"
    authorized.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    outside_dest = tmp_path / "outside-dest"

    with pytest.raises(ValueError, match="^DEST_DIR_OUTSIDE_AUTHORIZED_ROOT$"):
        build_motor_env(
            source,
            outside_dest,
            authorized / "state.json",
            authorized_root=authorized,
            mutation_authorized=True,
        )
    assert not outside_dest.exists()

    safe_dest = authorized / "dest"
    outside_state = tmp_path / "outside-state.json"
    with pytest.raises(ValueError, match="^STATE_FILE_OUTSIDE_AUTHORIZED_ROOT$"):
        build_motor_env(
            source,
            safe_dest,
            outside_state,
            authorized_root=authorized,
            mutation_authorized=True,
        )
    assert not safe_dest.exists()
    assert not outside_state.exists()


def test_gate_rejects_symlink_escape_without_mutation(tmp_path: Path) -> None:
    authorized = tmp_path / "authorized"
    outside = tmp_path / "outside"
    authorized.mkdir()
    outside.mkdir()
    source = tmp_path / "source"
    source.mkdir()

    escape_link = authorized / "escape"
    escape_link.symlink_to(outside, target_is_directory=True)
    escaped_dest = escape_link / "dest"

    with pytest.raises(ValueError, match="^DEST_DIR_OUTSIDE_AUTHORIZED_ROOT$"):
        build_motor_env(
            source,
            escaped_dest,
            authorized / "state.json",
            authorized_root=authorized,
            mutation_authorized=True,
        )
    assert not (outside / "dest").exists()

    safe_dest = authorized / "dest"
    escaped_state = escape_link / "state.json"
    with pytest.raises(ValueError, match="^STATE_FILE_OUTSIDE_AUTHORIZED_ROOT$"):
        build_motor_env(
            source,
            safe_dest,
            escaped_state,
            authorized_root=authorized,
            mutation_authorized=True,
        )
    assert not safe_dest.exists()
    assert not (outside / "state.json").exists()
