"""Deterministic promotion/rollback gate for Wordflow deployments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DeploymentEvidence:
    artifact_hash_verified: bool
    installation_verified: bool
    sandbox_verified: bool
    tests_pass: bool
    independent_review_pass: bool
    output_schema_pass: bool
    checkpoint_created: bool
    rollback_ready: bool
    health_check_pass: bool
    evidence_refs: Tuple[str, ...]


@dataclass(frozen=True)
class DeploymentDecision:
    status: str
    promote_authorized: bool
    failed_gates: Tuple[str, ...]
    rollback_required: bool


def evaluate_deployment(evidence: DeploymentEvidence) -> DeploymentDecision:
    gates = {
        "ARTIFACT_HASH": evidence.artifact_hash_verified,
        "INSTALLATION": evidence.installation_verified,
        "SANDBOX": evidence.sandbox_verified,
        "TESTS": evidence.tests_pass,
        "INDEPENDENT_REVIEW": evidence.independent_review_pass,
        "OUTPUT_SCHEMA": evidence.output_schema_pass,
        "CHECKPOINT": evidence.checkpoint_created,
        "ROLLBACK_READY": evidence.rollback_ready,
        "HEALTH_CHECK": evidence.health_check_pass,
        "EVIDENCE_REFS": bool(evidence.evidence_refs) and all(ref.strip() for ref in evidence.evidence_refs),
    }
    failed = tuple(name for name, passed in gates.items() if not passed)
    if failed:
        return DeploymentDecision(
            status="PROMOTION_BLOCKED",
            promote_authorized=False,
            failed_gates=failed,
            rollback_required=evidence.installation_verified or evidence.health_check_pass,
        )
    return DeploymentDecision(
        status="PROMOTE_READY",
        promote_authorized=True,
        failed_gates=(),
        rollback_required=False,
    )


def post_promote_health_gate(health_ok: bool, readback_ok: bool, rollback_ready: bool) -> DeploymentDecision:
    if health_ok and readback_ok:
        return DeploymentDecision("DEPLOYED_VERIFIED", True, (), False)
    failed = tuple(
        name for name, ok in (("POST_HEALTH", health_ok), ("POST_READBACK", readback_ok)) if not ok
    )
    return DeploymentDecision(
        status="ROLLBACK_REQUIRED" if rollback_ready else "DEPLOYMENT_FAILURE_NO_ROLLBACK",
        promote_authorized=False,
        failed_gates=failed,
        rollback_required=rollback_ready,
    )
