import pytest

from runtime.src.core.existing_code_intake import (
    ExistingCodeIntakeError,
    ExistingCodeRequest,
    validate_existing_code,
)


def _request(**overrides):
    values = {
        "intake_id": "E1",
        "source_ref": "https://github.com/example/repo@abc/file.py",
        "source_content": b"def add(a,b): return a+b\n",
        "source_license": "MIT",
        "language": "python",
        "requested_decision": "ADAPT",
        "destination": "➡️📂 Wordflow LOOP Yaiwes/runtime/src/tools/add.py",
        "provenance_refs": ("source:abc", "license:MIT"),
        "safety_verdict": "ALLOW_STATIC_REVIEW",
        "motor_operation": "COPY",
    }
    values.update(overrides)
    return ExistingCodeRequest(**values)


def test_existing_code_packet_is_hash_bound_and_not_executable():
    packet = validate_existing_code(_request())
    assert len(packet.source_sha256) == 64
    assert packet.decision == "ADAPT"
    assert packet.execution_authorized is False
    assert packet.deployment_authorized is False


def test_outside_destination_fails_closed():
    with pytest.raises(ExistingCodeIntakeError, match="DESTINATION_OUTSIDE_AUTHORIZED_ROOT"):
        validate_existing_code(_request(destination="Core kernel Yaiwes/file.py"))


def test_unsafe_code_must_be_rejected_before_movement():
    with pytest.raises(ExistingCodeIntakeError, match="UNSAFE_CODE_CANNOT_ADVANCE"):
        validate_existing_code(_request(safety_verdict="BLOCK_AND_REVIEW", requested_decision="ADAPT"))
    packet = validate_existing_code(_request(safety_verdict="BLOCK_AND_REVIEW", requested_decision="REJECT"))
    assert packet.decision == "REJECT"


def test_noncanonical_transfer_operation_fails():
    with pytest.raises(ExistingCodeIntakeError, match="CANONICAL_MOTOR_OPERATION_REQUIRED"):
        validate_existing_code(_request(motor_operation="RSYNC"))
