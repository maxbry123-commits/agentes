"""Deterministic intake contract for existing code/components.

This module classifies and validates existing code before any copy/move/adapt
operation. It never executes the candidate and never chooses an external
location outside the authorized Wordflow root.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass
from typing import Literal, Mapping, Tuple

from .canonical_motor_gate import build_motor_env, verify_motor

Decision = Literal["REUSE", "PATCH", "ADAPT", "REJECT"]


class ExistingCodeIntakeError(ValueError):
    pass


@dataclass(frozen=True)
class ExistingCodeRequest:
    intake_id: str
    source_ref: str
    source_content: bytes
    source_license: str
    language: str
    requested_decision: Decision
    destination: str
    provenance_refs: Tuple[str, ...]
    safety_verdict: str
    motor_operation: str = "COPY"


@dataclass(frozen=True)
class ExistingCodePacket:
    intake_id: str
    source_ref: str
    source_sha256: str
    source_license: str
    language: str
    decision: Decision
    destination: str
    provenance_refs: Tuple[str, ...]
    safety_verdict: str
    motor_operation: str
    execution_authorized: bool
    deployment_authorized: bool


@dataclass(frozen=True)
class ExistingCodeTransferResult:
    contract: str
    packet: ExistingCodePacket
    motor_blob_sha: str
    motor_verdict: str
    destination_sha256: str
    state_sha256: str
    source_retained: bool
    readback_verified: bool


def validate_existing_code(request: ExistingCodeRequest) -> ExistingCodePacket:
    if not request.intake_id.strip():
        raise ExistingCodeIntakeError("INTAKE_ID_REQUIRED")
    if not request.source_ref.strip() or not request.source_content:
        raise ExistingCodeIntakeError("SOURCE_REQUIRED")
    if not request.source_license.strip():
        raise ExistingCodeIntakeError("LICENSE_REQUIRED")
    if not request.provenance_refs or any(not ref.strip() for ref in request.provenance_refs):
        raise ExistingCodeIntakeError("PROVENANCE_REQUIRED")
    if request.requested_decision not in {"REUSE", "PATCH", "ADAPT", "REJECT"}:
        raise ExistingCodeIntakeError("DECISION_INVALID")

    destination = request.destination.replace("\\", "/").strip()
    if not destination.startswith("➡️📂 Wordflow LOOP Yaiwes/"):
        raise ExistingCodeIntakeError("DESTINATION_OUTSIDE_AUTHORIZED_ROOT")
    if destination.startswith("/") or ".." in destination.split("/"):
        raise ExistingCodeIntakeError("DESTINATION_UNSAFE")

    if request.motor_operation not in {"COPY", "MOVE"}:
        raise ExistingCodeIntakeError("CANONICAL_MOTOR_OPERATION_REQUIRED")
    if request.safety_verdict not in {"ALLOW_STATIC_REVIEW", "BLOCK_AND_REVIEW"}:
        raise ExistingCodeIntakeError("SAFETY_VERDICT_REQUIRED")
    if request.safety_verdict == "BLOCK_AND_REVIEW" and request.requested_decision != "REJECT":
        raise ExistingCodeIntakeError("UNSAFE_CODE_CANNOT_ADVANCE")

    digest = hashlib.sha256(request.source_content).hexdigest()
    return ExistingCodePacket(
        intake_id=request.intake_id,
        source_ref=request.source_ref,
        source_sha256=digest,
        source_license=request.source_license,
        language=request.language.strip().lower() or "unknown",
        decision=request.requested_decision,
        destination=destination,
        provenance_refs=request.provenance_refs,
        safety_verdict=request.safety_verdict,
        motor_operation=request.motor_operation,
        execution_authorized=False,
        deployment_authorized=False,
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute_existing_code_transfer(
    request: ExistingCodeRequest,
    *,
    repo_root: Path,
    authorized_root: Path,
    source_file: Path,
    state_file: Path,
    mutation_authorized: bool = False,
    remove_source_authorized: bool = False,
    environment: Mapping[str, str] | None = None,
) -> ExistingCodeTransferResult:
    """Transfer one audited file through the locked canonical copy/move motor.

    The single-file restriction prevents a request hash from authorizing
    unreviewed sibling files.  The canonical motor performs the mutation; this
    adapter only builds its gated environment and verifies physical read-back.
    """
    packet = validate_existing_code(request)
    if packet.decision == "REJECT":
        raise ExistingCodeIntakeError("REJECT_DECISION_CANNOT_TRANSFER")
    if not mutation_authorized:
        raise ExistingCodeIntakeError("MUTATION_NOT_AUTHORIZED")
    if packet.motor_operation == "MOVE" and not remove_source_authorized:
        raise ExistingCodeIntakeError("REMOVE_SOURCE_NOT_AUTHORIZED")

    root = repo_root.resolve()
    auth = authorized_root.resolve()
    try:
        auth.relative_to(root)
    except ValueError as exc:
        raise ExistingCodeIntakeError("AUTHORIZED_ROOT_OUTSIDE_REPOSITORY") from exc
    if not source_file.is_file():
        raise ExistingCodeIntakeError("SOURCE_FILE_NOT_FOUND")
    source = source_file.resolve()
    siblings = [item for item in source.parent.rglob("*") if item.is_file()]
    if siblings != [source]:
        raise ExistingCodeIntakeError("SOURCE_SCOPE_MUST_CONTAIN_ONE_FILE")
    if source.read_bytes() != request.source_content:
        raise ExistingCodeIntakeError("SOURCE_CONTENT_MISMATCH")

    destination = (root / packet.destination).resolve()
    try:
        destination.relative_to(auth)
    except ValueError as exc:
        raise ExistingCodeIntakeError("DESTINATION_OUTSIDE_AUTHORIZED_ROOT") from exc
    if destination.name != source.name:
        raise ExistingCodeIntakeError("DESTINATION_FILENAME_MISMATCH")

    operation = packet.motor_operation.lower()
    verified_motor = verify_motor(auth, operation)
    try:
        motor_env = build_motor_env(
            source.parent,
            destination.parent,
            state_file,
            authorized_root=auth,
            mutation_authorized=True,
        )
    except (ValueError, PermissionError) as exc:
        raise ExistingCodeIntakeError(str(exc)) from exc
    env = os.environ.copy()
    if environment:
        env.update(environment)
    env.update(motor_env)
    process = subprocess.run(
        [sys.executable, str(auth / str(verified_motor["motor_path"]))],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if process.returncode != 0 or not process.stdout.strip():
        raise ExistingCodeIntakeError("CANONICAL_MOTOR_EXECUTION_FAILED")
    try:
        motor_result = json.loads(process.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise ExistingCodeIntakeError("CANONICAL_MOTOR_RESULT_INVALID") from exc
    if motor_result.get("verdict") != "VERIFIED_CLOSED":
        raise ExistingCodeIntakeError("CANONICAL_MOTOR_DID_NOT_CLOSE")
    if not destination.is_file() or _sha256_file(destination) != packet.source_sha256:
        raise ExistingCodeIntakeError("DESTINATION_READBACK_MISMATCH")
    if not state_file.is_file():
        raise ExistingCodeIntakeError("MOTOR_STATE_READBACK_MISSING")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    completed = state.get("completed", {})
    if completed.get(source.name) not in {
        "COPIED_VERIFIED",
        "VERIFIED_EXISTING",
        "MOVED_VERIFIED",
        "VERIFIED_EXISTING_AFTER_MOVE",
        "DEST_IDENTICAL_SOURCE_REMOVED",
    }:
        raise ExistingCodeIntakeError("MOTOR_STATE_READBACK_MISMATCH")
    source_retained = source.exists()
    if operation == "copy" and not source_retained:
        raise ExistingCodeIntakeError("COPY_REMOVED_SOURCE")
    if operation == "move" and source_retained:
        raise ExistingCodeIntakeError("MOVE_RETAINED_SOURCE")
    return ExistingCodeTransferResult(
        contract="yaiwes.existing_code_intake/v2",
        packet=packet,
        motor_blob_sha=str(verified_motor["actual_blob_sha"]),
        motor_verdict=str(motor_result["verdict"]),
        destination_sha256=_sha256_file(destination),
        state_sha256=_sha256_file(state_file),
        source_retained=source_retained,
        readback_verified=True,
    )
