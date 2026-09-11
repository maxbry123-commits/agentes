from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

CONTRACT: Final[str] = "yaiwes.canonical_motor_gate/v1"

MOTOR_SPECS: Final[dict[str, dict[str, str]]] = {
    "copy": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de copiar archivos/motor_3_copy_batches.py",
        "blob_sha": "3689924361ce4a1a9fde4ae2b6f6009c37a6042d",
    },
    "move": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de moves archivos/motor_4_move_batches.py",
        "blob_sha": "9a21facfe11327cf60a2afca8f415ad52f0ecbe5",
    },
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def verify_motor(repo_root: Path, operation: str) -> dict[str, object]:
    if operation not in MOTOR_SPECS:
        raise ValueError("UNSUPPORTED_MOTOR_OPERATION")
    spec = MOTOR_SPECS[operation]
    motor_path = repo_root / spec["path"]
    if not motor_path.is_file():
        raise RuntimeError("CANONICAL_MOTOR_NOT_FOUND")
    actual_blob = git_blob_sha(motor_path)
    if actual_blob != spec["blob_sha"]:
        raise RuntimeError("MOTOR_CODE_LOCK_GAP")
    return {
        "contract": CONTRACT,
        "operation": operation,
        "motor_path": spec["path"],
        "expected_blob_sha": spec["blob_sha"],
        "actual_blob_sha": actual_blob,
        "verified": True,
        "rewrite_authorized": False,
        "execution_authorized": False,
    }


def build_motor_env(source_dir: Path, dest_dir: Path, state_file: Path) -> dict[str, str]:
    source = source_dir.resolve()
    dest = dest_dir.resolve()
    state = state_file.resolve()
    if source == dest:
        raise ValueError("SOURCE_DESTINATION_COLLISION")
    if not source.is_dir():
        raise ValueError("SOURCE_DIR_NOT_FOUND")
    dest.mkdir(parents=True, exist_ok=True)
    return {
        "SOURCE_DIR": str(source),
        "DEST_DIR": str(dest),
        "STATE_FILE": str(state),
        "COLLISION_POLICY": "fail",
        "BATCH_SIZE": "25",
        "MAX_BATCHES": "0",
    }
