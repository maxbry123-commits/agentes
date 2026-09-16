from runtime.src.core.code_generation_policy import GenerationRequest, authorize_generation


def _request(**overrides):
    data = {
        "task_id": "T-G006",
        "capability": "minimal-safe-generation",
        "reuse_decision": "GENERATE",
        "placement": "D_WORDFLOW",
        "target_path": "runtime/src/core/generated_candidate.py",
        "contract_id": "yaiwes.capability/v1",
        "fables_binding": "UNIVERSAL_PLUGIN_BUS",
        "provenance_ref": "G006:test",
        "requested_by_llm": False,
    }
    data.update(overrides)
    return GenerationRequest(**data)


def test_reuse_must_be_exhausted_before_generation():
    decision = authorize_generation(_request(reuse_decision="REUSE"))
    assert decision.allowed is False
    assert decision.reason_codes == ("REUSE_POLICY_NOT_GENERATE",)


def test_placement_and_target_path_fail_closed():
    bad_placement = authorize_generation(_request(placement="UNKNOWN"))
    assert bad_placement.allowed is False
    assert bad_placement.reason_codes == ("PLACEMENT_NOT_APPROVED",)

    traversal = authorize_generation(_request(target_path="../escape.py"))
    assert traversal.allowed is False
    assert traversal.reason_codes == ("TARGET_PATH_NOT_AUTHORIZED_RELATIVE",)

    workflow_path = authorize_generation(_request(target_path=".github/workflows/escape.yml"))
    assert workflow_path.allowed is False
    assert workflow_path.reason_codes == ("TARGET_PATH_NOT_AUTHORIZED_RELATIVE",)


def test_canonical_fables_binding_must_be_verified_not_literal_substitute():
    denied = authorize_generation(_request(fables_binding="STRING_ONLY_NOT_CANONICAL"))
    assert denied.allowed is False
    assert denied.reason_codes == ("FABLES_BINDING_REQUIRED",)

    allowed = authorize_generation(_request())
    assert allowed.allowed is True
    assert allowed.candidate_generation_allowed is True
    assert "FABLES_BINDING_VERIFIED" in allowed.reason_codes
    assert "CANONICAL_FABLES_BINDING_VERIFIED" in allowed.reason_codes


def test_llm_can_request_candidate_but_never_authorize_execution_or_deployment():
    decision = authorize_generation(_request(requested_by_llm=True))
    assert decision.allowed is True
    assert decision.candidate_generation_allowed is True
    assert decision.execution_authorized is False
    assert decision.deployment_authorized is False
    assert "LLM_MAY_DRAFT_BUT_CANNOT_AUTHORIZE_EXECUTION" in decision.reason_codes


def test_missing_required_fields_fail_closed():
    decision = authorize_generation(_request(task_id="", contract_id=""))
    assert decision.allowed is False
    assert decision.candidate_generation_allowed is False
    assert decision.reason_codes == ("MISSING_REQUIRED_FIELDS:task_id,contract_id",)
