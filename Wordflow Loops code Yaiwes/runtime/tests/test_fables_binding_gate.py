from runtime.src.core.code_generation_policy import GenerationRequest, authorize_generation
from runtime.src.core.fables_binding_gate import (
    BUS_SOURCE_UPLOAD_SHA256,
    FICHA_SOURCE_UPLOAD_SHA256,
    verify_canonical_fables_binding,
)
from runtime.src.uek.universal_plugin_bus_v2_integrated import (
    ComponentCandidate,
    TargetConventions,
    UniversalPluginBus,
)


def test_source_provenance_is_exact():
    assert BUS_SOURCE_UPLOAD_SHA256 == "5e4595a86bfd68a3c1fde70ba614ce7b9ec6ea4d6c867912e836cca33c626fc3"
    assert FICHA_SOURCE_UPLOAD_SHA256 == "759d0d7855d8df106462b966bfc4ee543f24a3e789a27048f253159b58ff8d1a"


def test_canonical_fables_binding_registers_and_verifies():
    result = verify_canonical_fables_binding()
    assert result.verified is True
    assert result.registry_verified is True
    assert result.ficha_verified is True
    assert result.unsafe_candidate_rejected is True
    assert result.execution_authorized is False
    assert result.deployment_authorized is False
    assert "CANONICAL_FABLES_BINDING_VERIFIED" in result.reason_codes


def test_unsafe_candidate_is_rejected_before_registration():
    bus = UniversalPluginBus()
    unsafe = bus.hot_swap.shadow_load(
        "unsafe",
        ComponentCandidate("exec('raise RuntimeError(\"MUST_NOT_RUN\")')", "python"),
        1,
    )
    assert bus.hot_swap.run_shadow_tests(unsafe) is False


def test_generation_policy_uses_verified_binding_not_literal_only():
    req = GenerationRequest(
        task_id="T-G018",
        capability="safe-generation",
        reuse_decision="GENERATE",
        placement="D_WORDFLOW",
        target_path="runtime/src/core/generated_candidate.py",
        contract_id="yaiwes.capability/v1",
        fables_binding="UNIVERSAL_PLUGIN_BUS",
        provenance_ref="G018:test",
        requested_by_llm=True,
    )
    decision = authorize_generation(req)
    assert decision.allowed is True
    assert "FABLES_BINDING_VERIFIED" in decision.reason_codes
    assert decision.execution_authorized is False
    assert decision.deployment_authorized is False

    bad = GenerationRequest(
        task_id="T-G018-BAD",
        capability="safe-generation",
        reuse_decision="GENERATE",
        placement="D_WORDFLOW",
        target_path="runtime/src/core/generated_candidate.py",
        contract_id="yaiwes.capability/v1",
        fables_binding="STRING_ONLY_NOT_CANONICAL",
        provenance_ref="G018:test",
    )
    denied = authorize_generation(bad)
    assert denied.allowed is False
    assert denied.reason_codes == ("FABLES_BINDING_REQUIRED",)
