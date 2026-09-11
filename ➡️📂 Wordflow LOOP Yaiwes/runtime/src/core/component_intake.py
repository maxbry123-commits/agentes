"""Deterministic intake/queue adapter for the immutable canonical motors.

This module does not download, extract, copy or move anything. It validates a
Director-supplied operation and emits an invocation contract for the exact
canonical motor. The motor remains the only implementation of the operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Tuple
from urllib.parse import urlparse

Operation = Literal["DOWNLOAD_EXTRACT", "EXTRACT", "COPY", "MOVE"]

CANONICAL_MOTORS: Dict[str, Dict[str, str]] = {
    "DOWNLOAD_EXTRACT": {
        "path": "➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py",
        "blob": "84d566e2ee4e98e42eb3a864026d067d48caabd9",
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


def _valid_source(source: str, operation: Operation) -> bool:
    if operation in {"COPY", "MOVE", "EXTRACT"}:
        normalized = source.replace("\\", "/")
        return bool(source.strip()) and ".." not in normalized.split("/")
    parsed = urlparse(source)
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


def validate_request(request: ComponentRequest) -> MotorInvocation:
    if not request.request_id.strip():
        raise IntakeError("REQUEST_ID_REQUIRED")
    if request.operation not in CANONICAL_MOTORS:
        raise IntakeError("OPERATION_NOT_ALLOWED")
    if not _valid_source(request.source, request.operation):
        raise IntakeError("SOURCE_INVALID")
    destination = request.destination.replace("\\", "/").strip()
    if not destination or destination.startswith("/") or ".." in destination.split("/"):
        raise IntakeError("DESTINATION_INVALID")
    if not destination.startswith("➡️📂 Wordflow LOOP Yaiwes/"):
        raise IntakeError("DESTINATION_OUTSIDE_AUTHORIZED_ROOT")

    motor = CANONICAL_MOTORS[request.operation]
    return MotorInvocation(
        request_id=request.request_id,
        operation=request.operation,
        motor_path=motor["path"],
        expected_motor_blob=motor["blob"],
        source=request.source,
        destination=destination,
        expected_ref=request.expected_ref,
        expected_sha256=request.expected_sha256,
        required_checks=(
            "VERIFY_MOTOR_BLOB_BEFORE_RUN",
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
