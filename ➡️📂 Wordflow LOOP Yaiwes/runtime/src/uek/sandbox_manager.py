"""UEK sandbox policy gate.

A sandbox descriptor is not evidence of isolation. This manager only returns
READY_VERIFIED when an external backend supplies explicit isolation attestation.
It does not pretend to create kernel/container isolation by itself.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class SandboxAttestation:
    backend: str
    process_isolation: bool
    filesystem_isolation: bool
    network_enforced: bool
    memory_enforced: bool
    evidence_ref: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SandboxAttestation":
        return cls(
            backend=str(data.get("backend", "")),
            process_isolation=data.get("process_isolation") is True,
            filesystem_isolation=data.get("filesystem_isolation") is True,
            network_enforced=data.get("network_enforced") is True,
            memory_enforced=data.get("memory_enforced") is True,
            evidence_ref=str(data.get("evidence_ref", "")),
        )


class SandboxManager:
    """Fail-closed policy manager for externally enforced sandboxes."""

    ALLOWED_BACKENDS = {"bubblewrap", "nsjail", "firecracker", "gvisor", "container", "hf_job"}

    def __init__(self, network_policy: str = "DENY", memory_limit_mb: int = 512) -> None:
        if network_policy not in {"DENY", "ALLOWLIST"}:
            raise ValueError("INVALID_NETWORK_POLICY")
        if memory_limit_mb < 64:
            raise ValueError("MEMORY_LIMIT_TOO_LOW")
        self.network_policy = network_policy
        self.memory_limit_mb = memory_limit_mb

    def acquire_sandbox(
        self,
        sandbox_type: str,
        attestation: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Validate backend attestation; never fabricate READY state."""
        if not sandbox_type.strip():
            raise ValueError("SANDBOX_TYPE_REQUIRED")
        if attestation is None:
            return {
                "sandbox_id": None,
                "type": sandbox_type,
                "network_policy": self.network_policy,
                "memory_limit_mb": self.memory_limit_mb,
                "status": "BLOCKED_ATTESTATION_REQUIRED",
                "execution_authorized": False,
            }

        proof = SandboxAttestation.from_mapping(attestation)
        checks = {
            "backend_allowed": proof.backend in self.ALLOWED_BACKENDS,
            "process_isolation": proof.process_isolation,
            "filesystem_isolation": proof.filesystem_isolation,
            "network_enforced": proof.network_enforced,
            "memory_enforced": proof.memory_enforced,
            "evidence_ref": bool(proof.evidence_ref.strip()),
        }
        if not all(checks.values()):
            return {
                "sandbox_id": None,
                "type": sandbox_type,
                "backend": proof.backend,
                "checks": checks,
                "status": "BLOCKED_ATTESTATION_FAILED",
                "execution_authorized": False,
            }

        material = json.dumps(
            {
                "type": sandbox_type,
                "backend": proof.backend,
                "network_policy": self.network_policy,
                "memory_limit_mb": self.memory_limit_mb,
                "evidence_ref": proof.evidence_ref,
            },
            sort_keys=True,
        )
        sandbox_id = "sbx_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
        return {
            "sandbox_id": sandbox_id,
            "type": sandbox_type,
            "backend": proof.backend,
            "network_policy": self.network_policy,
            "memory_limit_mb": self.memory_limit_mb,
            "checks": checks,
            "status": "READY_VERIFIED",
            "execution_authorized": True,
            "evidence_ref": proof.evidence_ref,
        }

    def release_sandbox(self, sandbox_id: str, release_evidence_ref: str = "") -> Dict[str, Any]:
        if not sandbox_id.strip() or not release_evidence_ref.strip():
            return {"released": False, "status": "BLOCKED_RELEASE_EVIDENCE_REQUIRED"}
        return {
            "released": True,
            "sandbox_id": sandbox_id,
            "status": "RELEASE_RECORDED",
            "evidence_ref": release_evidence_ref,
        }
