from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

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

    env = build_motor_env(source, dest, tmp_path / "copy-state.json")
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

    env = build_motor_env(source, dest, tmp_path / "move-state.json")
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
    try:
        verify_motor(root, "delete")
    except ValueError as exc:
        assert str(exc) == "UNSUPPORTED_MOTOR_OPERATION"
    else:
        raise AssertionError("unsupported motor must fail closed")

    source = tmp_path / "same"
    source.mkdir()
    try:
        build_motor_env(source, source, tmp_path / "state.json")
    except ValueError as exc:
        assert str(exc) == "SOURCE_DESTINATION_COLLISION"
    else:
        raise AssertionError("same source/destination must fail closed")
