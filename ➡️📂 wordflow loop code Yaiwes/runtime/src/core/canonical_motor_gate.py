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


def _resolve_inside_authorized_root(
    candidate: Path,
    authorized_root: Path,
    label: str,
) -> Path:
    root = authorized_root.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label}_OUTSIDE_AUTHORIZED_ROOT") from exc
    return resolved


def build_motor_env(
    source_dir: Path,
    dest_dir: Path,
    state_file: Path,
    *,
    authorized_root: Path | None = None,
    mutation_authorized: bool = False,
) -> dict[str, str]:
    if authorized_root is None:
        raise ValueError("AUTHORIZED_ROOT_REQUIRED")

    root = authorized_root.resolve()
    if not root.is_dir():
        raise ValueError("AUTHORIZED_ROOT_NOT_FOUND")

    source = source_dir.resolve()
    dest = _resolve_inside_authorized_root(dest_dir, root, "DEST_DIR")
    state = _resolve_inside_authorized_root(state_file, root, "STATE_FILE")

    if source == dest:
        raise ValueError("SOURCE_DESTINATION_COLLISION")
    if not source.is_dir():
        raise ValueError("SOURCE_DIR_NOT_FOUND")

    # Path.resolve() follows every existing symlink in the candidate chain.
    # The containment checks above therefore fail closed when either the
    # destination or state path traverses a symlink outside authorized_root.
    if not mutation_authorized:
        raise PermissionError("MUTATION_NOT_AUTHORIZED")

    # No filesystem mutation occurs before every path gate and the explicit
    # mutation authorization have passed.
    dest.mkdir(parents=True, exist_ok=True)
    return {
        "SOURCE_DIR": str(source),
        "DEST_DIR": str(dest),
        "STATE_FILE": str(state),
        "COLLISION_POLICY": "fail",
        "BATCH_SIZE": "25",
        "MAX_BATCHES": "0",
    }
