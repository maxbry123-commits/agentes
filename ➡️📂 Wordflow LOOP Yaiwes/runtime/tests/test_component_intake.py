import pytest

from runtime.src.core.component_intake import (
    CANONICAL_MOTORS,
    ComponentRequest,
    IntakeError,
    build_queue,
    validate_request,
)


def test_download_request_routes_only_to_canonical_motor_and_is_not_auto_authorized():
    request = ComponentRequest(
        "R1",
        "DOWNLOAD_EXTRACT",
        "https://github.com/example/project",
        "➡️📂 Wordflow LOOP Yaiwes/📂 archivos download/project",
        expected_ref="abc123",
    )
    invocation = validate_request(request)
    assert invocation.motor_path == CANONICAL_MOTORS["DOWNLOAD_EXTRACT"]["path"]
    assert invocation.expected_motor_blob == "84d566e2ee4e98e42eb3a864026d067d48caabd9"
    assert invocation.execution_authorized is False
    assert "READ_BACK_DESTINATION" in invocation.required_checks


def test_destination_outside_wordflow_fails_closed():
    with pytest.raises(IntakeError, match="DESTINATION_OUTSIDE_AUTHORIZED_ROOT"):
        validate_request(
            ComponentRequest("R2", "COPY", "source", "Core kernel Yaiwes/out")
        )


def test_duplicate_queue_request_fails_closed():
    request = ComponentRequest(
        "R3", "MOVE", "source", "➡️📂 Wordflow LOOP Yaiwes/dest"
    )
    with pytest.raises(IntakeError, match="DUPLICATE_REQUEST_ID"):
        build_queue((request, request))
