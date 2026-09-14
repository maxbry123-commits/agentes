from runtime.src.install.deployment_gate import (
    DeploymentEvidence,
    evaluate_deployment,
    post_promote_health_gate,
)
from runtime.src.install.installation_engine import InstallationEngine
from runtime.src.uek.sandbox_manager import SandboxManager


def test_installation_no_longer_fabricates_pass_without_evidence():
    result = InstallationEngine().run_installation({"installation_id": "I1"})
    assert result["status"] == "BLOCKED"
    assert result["health_check"] == "NOT_VERIFIED"
    assert result["deployment_authorized"] is False


def test_installation_can_pass_only_with_complete_verified_evidence():
    result = InstallationEngine().run_installation(
        {"installation_id": "I2"},
        {
            "source_hash_verified": True,
            "dependencies_verified": True,
            "build_pass": True,
            "install_pass": True,
            "health_check_pass": True,
            "ficha_invariants_passed": 36,
            "environment_hash": "sha256:abc",
            "evidence_ref": "evidence://install/I2",
        },
    )
    assert result["status"] == "COMPLETED_VERIFIED"
    assert result["health_check"] == "PASS_VERIFIED"
    assert result["deployment_authorized"] is False


def test_sandbox_requires_backend_execution_not_caller_attestation():
    manager = SandboxManager(network_policy="DENY", memory_limit_mb=512)
    missing = manager.acquire_sandbox("python")
    assert missing["status"] == "BLOCKED_EXECUTION_REQUIRED"
    assert missing["execution_authorized"] is False

    fabricated = manager.acquire_sandbox(
        "python",
        {
            "backend": "nsjail",
            "process_isolation": True,
            "filesystem_isolation": True,
            "network_enforced": True,
            "memory_enforced": True,
            "evidence_ref": "evidence://sandbox/1",
        },
    )
    assert fabricated["status"] == "BLOCKED_UNTRUSTED_ATTESTATION"
    assert fabricated["execution_authorized"] is False


def test_deployment_is_blocked_until_every_gate_passes():
    incomplete = DeploymentEvidence(
        artifact_hash_verified=True,
        installation_verified=True,
        sandbox_verified=False,
        tests_pass=True,
        independent_review_pass=True,
        output_schema_pass=True,
        checkpoint_created=True,
        rollback_ready=True,
        health_check_pass=True,
        evidence_refs=("evidence://1",),
    )
    assert evaluate_deployment(incomplete).status == "PROMOTION_BLOCKED"

    complete = DeploymentEvidence(
        artifact_hash_verified=True,
        installation_verified=True,
        sandbox_verified=True,
        tests_pass=True,
        independent_review_pass=True,
        output_schema_pass=True,
        checkpoint_created=True,
        rollback_ready=True,
        health_check_pass=True,
        evidence_refs=("evidence://install", "evidence://sandbox", "evidence://tests"),
    )
    assert evaluate_deployment(complete).status == "PROMOTE_READY"
    assert evaluate_deployment(complete).promote_authorized is True


def test_post_promote_failure_requires_rollback():
    decision = post_promote_health_gate(False, True, True)
    assert decision.status == "ROLLBACK_REQUIRED"
    assert decision.rollback_required is True
