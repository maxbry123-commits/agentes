"""Fail-closed intake and adapter for the immutable canonical motors.

The adapter validates requests, locks motor blobs, creates the exact motor
environment and verifies the motor's persisted result. It never authorizes a
motor run by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Dict, Literal, Mapping, Tuple
from urllib.parse import urlparse

CONTRACT = "yaiwes.component_intake/v2"
AUTHORIZED_REPOSITORY_ROOT = "➡️📂 Wordflow LOOP Yaiwes"
Operation = Literal["DOWNLOAD_EXTRACT", "EXTRACT", "COPY", "MOVE"]

CANONICAL_MOTORS: Dict[str, Dict[str, str]] = {
    "DOWNLOAD_EXTRACT": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py",
        "blob": "84d566e2ee4e98e42eb3a864026d067d48caabd9",
        "engine_path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py",
        "engine_blob": "91e6e4486692eab314be5c7130d8310d3c855397",
    },
    "EXTRACT": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂 Motor de extracción zip/motor_1_extract_only.py",
        "blob": "a52d5dc0e6ff26f75d753b848dcc1a40c5dd4500",
    },
    "COPY": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de copiar archivos/motor_3_copy_batches.py",
        "blob": "3689924361ce4a1a9fde4ae2b6f6009c37a6042d",
    },
    "MOVE": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/➡️📂motor de moves archivos/motor_4_move_batches.py",
        "blob": "9a21facfe11327cf60a2afca8f415ad52f0ecbe5",
    },
}

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class IntakeError(ValueError):
    pass


@dataclass(frozen=True)
class ComponentRequest:
    request_id: str
    operation: Operation
    source: str
    destination: str
    expected_ref: str = ""
    expected_sha256: str = ""


@dataclass(frozen=True)
class MotorInvocation:
    request_id: str
    operation: Operation
    motor_path: str
    expected_motor_blob: str
    source: str
    destination: str
    expected_ref: str
    expected_sha256: str
    required_checks: Tuple[str, ...]
    execution_authorized: bool = False


@dataclass(frozen=True)
class PreparedMotor:
    invocation: MotorInvocation
    motor_file: Path
    authorized_root: Path
    environment: Tuple[Tuple[str, str], ...]
    queue_document: str = ""
    execution_authorized: bool = False

    def env(self) -> Dict[str, str]:
        return dict(self.environment)


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_hash(root: Path) -> Dict[str, Any]:
    digest = hashlib.sha256()
    files = 0
    total = 0
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        file_digest = _sha256(path)
        size = path.stat().st_size
        digest.update(
            relative.encode("utf-8")
            + b"\0"
            + file_digest.encode("ascii")
            + b"\0"
            + str(size).encode("ascii")
            + b"\n"
        )
        files += 1
        total += size
    return {"files": files, "bytes": total, "sha256": digest.hexdigest()}


def _safe_repo_path(value: str, *, label: str) -> str:
    normalized = value.replace("\\", "/").strip().rstrip("/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise IntakeError(f"{label}_INVALID")
    if not path.parts or path.parts[0] != AUTHORIZED_REPOSITORY_ROOT:
        raise IntakeError(f"{label}_OUTSIDE_AUTHORIZED_ROOT")
    return path.as_posix()


def _resolve_inside(candidate: Path, root: Path, *, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise IntakeError(f"{label}_OUTSIDE_AUTHORIZED_ROOT") from exc
    return resolved


def _resolve_scoped_path(value: str, root: Path, *, label: str) -> Path:
    parts = PurePosixPath(value).parts
    if not parts or parts[0] != AUTHORIZED_REPOSITORY_ROOT:
        raise IntakeError(f"{label}_OUTSIDE_AUTHORIZED_ROOT")
    return _resolve_inside(root.joinpath(*parts[1:]), root, label=label)


def validate_request(request: ComponentRequest) -> MotorInvocation:
    if not _ID.fullmatch(request.request_id):
        raise IntakeError("REQUEST_ID_INVALID")
    if request.operation not in CANONICAL_MOTORS:
        raise IntakeError("OPERATION_NOT_ALLOWED")

    destination = _safe_repo_path(request.destination, label="DESTINATION")
    source = request.source.strip()
    if request.operation == "DOWNLOAD_EXTRACT":
        parsed = urlparse(source)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise IntakeError("SOURCE_HTTPS_GITHUB_REQUIRED")
        if not _SHA1.fullmatch(request.expected_ref):
            raise IntakeError("PINNED_SOURCE_REF_REQUIRED")
    else:
        source = _safe_repo_path(source, label="SOURCE")
        if request.operation == "EXTRACT" and not _SHA256.fullmatch(request.expected_sha256):
            raise IntakeError("ARCHIVE_SHA256_REQUIRED")

    motor = CANONICAL_MOTORS[request.operation]
    return MotorInvocation(
        request_id=request.request_id,
        operation=request.operation,
        motor_path=motor["path"],
        expected_motor_blob=motor["blob"],
        source=source,
        destination=destination,
        expected_ref=request.expected_ref,
        expected_sha256=request.expected_sha256,
        required_checks=(
            "VERIFY_MOTOR_BLOB_BEFORE_RUN",
            "VERIFY_PINNED_SOURCE_OR_ARCHIVE_SHA256",
            "NO_LFS",
            "NO_FORCE",
            "FAIL_ON_COLLISION",
            "READ_BACK_DESTINATION",
            "VERIFY_HASH_OR_TREE_HASH",
            "PERSIST_EVIDENCE",
        ),
        execution_authorized=False,
    )


def build_queue(requests: Tuple[ComponentRequest, ...]) -> Tuple[MotorInvocation, ...]:
    seen = set()
    invocations = []
    for request in requests:
        if request.request_id in seen:
            raise IntakeError("DUPLICATE_REQUEST_ID")
        seen.add(request.request_id)
        invocations.append(validate_request(request))
    return tuple(invocations)


def _verify_locked_file(repo_root: Path, path: str, expected_blob: str) -> Path:
    file_path = (repo_root / path).resolve()
    if not file_path.is_file():
        raise IntakeError("CANONICAL_MOTOR_NOT_FOUND")
    if _git_blob_sha(file_path) != expected_blob:
        raise IntakeError("MOTOR_CODE_LOCK_GAP")
    return file_path


def prepare_motor(
    request: ComponentRequest,
    *,
    repo_root: Path,
    authorized_root: Path,
) -> PreparedMotor:
    """Prepare a verified invocation without creating files or running code."""
    invocation = validate_request(request)
    root = authorized_root.resolve()
    if not root.is_dir():
        raise IntakeError("AUTHORIZED_ROOT_NOT_FOUND")
    motor = _verify_locked_file(repo_root, invocation.motor_path, invocation.expected_motor_blob)
    destination = _resolve_scoped_path(invocation.destination, root, label="DESTINATION")
    state = _resolve_inside(
        root / "wordflow_loop" / "intake" / f"{request.request_id}.state.json",
        root,
        label="STATE_FILE",
    )

    if invocation.operation == "EXTRACT":
        source = _resolve_scoped_path(invocation.source, root, label="SOURCE")
        if not source.is_file():
            raise IntakeError("ARCHIVE_NOT_FOUND")
        if _sha256(source) != invocation.expected_sha256:
            raise IntakeError("ARCHIVE_SHA256_MISMATCH")
        env = {
            "ARCHIVE_INPUT": str(source),
            "DEST_DIR": str(destination),
            "STATE_FILE": str(state),
            "BATCH_SIZE": "25",
            "MAX_BATCHES": "0",
        }
        return PreparedMotor(invocation, motor, root, tuple(sorted(env.items())))

    if invocation.operation == "DOWNLOAD_EXTRACT":
        spec = CANONICAL_MOTORS["DOWNLOAD_EXTRACT"]
        engine = _verify_locked_file(repo_root, spec["engine_path"], spec["engine_blob"])
        queue_file = _resolve_inside(
            root / "wordflow_loop" / "intake" / f"{request.request_id}.queue.json",
            root,
            label="QUEUE_FILE",
        )
        index_file = _resolve_inside(
            root / "wordflow_loop" / "intake" / f"{request.request_id}.index.md",
            root,
            label="INDEX_FILE",
        )
        slug = request.source.rstrip("/").rsplit("/", 1)[-1]
        queue = {
            "schema": CONTRACT,
            "queue": [{
                "id": request.request_id,
                "source_repo": request.source,
                "source_ref": request.expected_ref,
                "slug": slug,
                "dest_repo": "maxbry123-commits/agentes",
                "dest_branch": "main",
                "dest_root": request.destination,
                "publish": False,
            }],
        }
        env = {
            "QUEUE_FILE": str(queue_file),
            "STATE_FILE": str(state),
            "ENGINE_PATH": str(engine),
            "INDEX_PATH": str(index_file),
            "MAX_RETRIES": "1",
            "LOOP_SLEEP_SECONDS": "0",
        }
        document = json.dumps(queue, ensure_ascii=False, sort_keys=True) + "\n"
        return PreparedMotor(
            invocation,
            motor,
            root,
            tuple(sorted(env.items())),
            queue_document=document,
        )

    raise IntakeError("G012_ONLY_SUPPORTS_DOWNLOAD_OR_EXTRACT")


def persist_queue(prepared: PreparedMotor, *, mutation_authorized: bool) -> Path:
    if prepared.invocation.operation != "DOWNLOAD_EXTRACT" or not prepared.queue_document:
        raise IntakeError("QUEUE_DOCUMENT_NOT_AVAILABLE")
    if not mutation_authorized:
        raise PermissionError("MUTATION_NOT_AUTHORIZED")
    queue_path = _resolve_inside(
        Path(prepared.env()["QUEUE_FILE"]),
        prepared.authorized_root,
        label="QUEUE_FILE",
    )
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = queue_path.with_name(queue_path.name + ".tmp")
    temporary.write_text(prepared.queue_document, encoding="utf-8")
    os.replace(temporary, queue_path)
    if queue_path.read_text(encoding="utf-8") != prepared.queue_document:
        raise IntakeError("QUEUE_READBACK_MISMATCH")
    return queue_path


def verify_readback(
    prepared: PreparedMotor,
    result: Mapping[str, Any],
    *,
    destination: Path | None = None,
) -> Dict[str, Any]:
    """Validate real motor output; presence alone is never a PASS."""
    if result.get("verdict") != "VERIFIED_CLOSED":
        raise IntakeError("MOTOR_NOT_VERIFIED_CLOSED")
    if prepared.invocation.operation == "EXTRACT":
        if result.get("failed") != 0 or result.get("pending") != 0:
            raise IntakeError("EXTRACTION_INCOMPLETE")
        tree = result.get("tree")
        if not isinstance(tree, Mapping) or not _SHA256.fullmatch(str(tree.get("sha256", ""))):
            raise IntakeError("TREE_HASH_MISSING")
        if destination is None or not destination.is_dir():
            raise IntakeError("DESTINATION_READBACK_MISSING")
        actual_tree = _tree_hash(destination)
        expected_tree = {
            "files": tree.get("files"),
            "bytes": tree.get("bytes"),
            "sha256": tree.get("sha256"),
        }
        if actual_tree != expected_tree:
            raise IntakeError("DESTINATION_TREE_HASH_MISMATCH")
    else:
        balance = result.get("balance")
        if not isinstance(balance, Mapping):
            raise IntakeError("QUEUE_BALANCE_MISSING")
        if balance.get("failed") != 0 or balance.get("pending") != 0:
            raise IntakeError("QUEUE_INCOMPLETE")
        state_path = _resolve_inside(
            Path(prepared.env()["STATE_FILE"]),
            prepared.authorized_root,
            label="STATE_FILE",
        )
        if not state_path.is_file():
            raise IntakeError("STATE_READBACK_MISSING")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        row = state.get("items", {}).get(prepared.invocation.request_id, {})
        payload = row.get("result", {})
        if row.get("status") != "VERIFIED_CLOSED":
            raise IntakeError("REQUEST_NOT_VERIFIED_CLOSED")
        if payload.get("source_commit") != prepared.invocation.expected_ref:
            raise IntakeError("SOURCE_REF_READBACK_MISMATCH")
        if payload.get("extraction_verified") is not True:
            raise IntakeError("EXTRACTION_READBACK_MISSING")
        extracted = payload.get("extracted_tree", {})
        if not _SHA256.fullmatch(str(extracted.get("sha256", ""))):
            raise IntakeError("TREE_HASH_MISSING")
    return {
        "contract": CONTRACT,
        "request_id": prepared.invocation.request_id,
        "operation": prepared.invocation.operation,
        "verdict": "VERIFIED_CLOSED",
        "execution_authorized": False,
    }
