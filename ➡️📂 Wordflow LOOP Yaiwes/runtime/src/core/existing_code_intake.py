"""Deterministic intake contract for existing code/components.

This module classifies and validates existing code before any copy/move/adapt
operation. It never executes the candidate and never chooses an external
location outside the authorized Wordflow root.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Tuple

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
