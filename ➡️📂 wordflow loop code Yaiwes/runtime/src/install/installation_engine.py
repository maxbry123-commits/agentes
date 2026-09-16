"""Evidence-gated deterministic Installation Engine (T-005).

The engine never fabricates health PASS, environment hashes or invariant counts.
It consumes independently produced evidence and fails closed when evidence is
missing or incomplete.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping


class InstallationStateMachine:
    STATES: List[str] = [
        "INIT", "PRECHECK", "ENV_SETUP", "DEPS_RESOLVE",
        "DOWNLOAD", "VERIFY", "COMPILE", "INSTALL",
        "CONFIG", "HEALTH_CHECK", "FICHA_GEN", "COMPLETED",
    ]

    def __init__(self) -> None:
        self.current_step = 0

    def reset(self) -> None:
        self.current_step = 0

    def advance(self) -> str:
        if self.current_step < len(self.STATES) - 1:
            self.current_step += 1
        return self.STATES[self.current_step]


@dataclass(frozen=True)
class InstallationEvidence:
    source_hash_verified: bool
    dependencies_verified: bool
    build_pass: bool
    install_pass: bool
    health_check_pass: bool
    ficha_invariants_passed: int
    environment_hash: str
    evidence_ref: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "InstallationEvidence":
        return cls(
            source_hash_verified=data.get("source_hash_verified") is True,
            dependencies_verified=data.get("dependencies_verified") is True,
            build_pass=data.get("build_pass") is True,
            install_pass=data.get("install_pass") is True,
            health_check_pass=data.get("health_check_pass") is True,
            ficha_invariants_passed=int(data.get("ficha_invariants_passed", 0)),
            environment_hash=str(data.get("environment_hash", "")),
            evidence_ref=str(data.get("evidence_ref", "")),
        )


class InstallationEngine:
    """Consumes verification evidence and emits a truthful FichaContract result."""

    REQUIRED_INVARIANTS = 36

    def __init__(self) -> None:
        self.fsm = InstallationStateMachine()

    def run_installation(
        self,
        acquired_manifest: Dict[str, Any],
        evidence: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self.fsm.reset()
        installation_id = str(acquired_manifest.get("installation_id", "")).strip()
        if not installation_id:
            return self._blocked("INSTALLATION_ID_REQUIRED", "INIT", [])
        if evidence is None:
            return self._blocked("INSTALLATION_EVIDENCE_REQUIRED", "PRECHECK", ["INIT"])

        proof = InstallationEvidence.from_mapping(evidence)
        checks = {
            "source_hash_verified": proof.source_hash_verified,
            "dependencies_verified": proof.dependencies_verified,
            "build_pass": proof.build_pass,
            "install_pass": proof.install_pass,
            "health_check_pass": proof.health_check_pass,
            "ficha_invariants_passed": proof.ficha_invariants_passed >= self.REQUIRED_INVARIANTS,
            "environment_hash": proof.environment_hash.startswith("sha256:"),
            "evidence_ref": bool(proof.evidence_ref.strip()),
        }
        failed = sorted(name for name, passed in checks.items() if not passed)
        if failed:
            return {
                "installation_id": installation_id,
                "health_check": "FAIL",
                "ficha_contract": {
                    "valid": False,
                    "invariants_passed": proof.ficha_invariants_passed,
                    "environment_hash": proof.environment_hash or None,
                    "health_check": "FAIL",
                },
                "checks": checks,
                "failed_checks": failed,
                "execution_history": ["INIT", "PRECHECK"],
                "status": "BLOCKED_EVIDENCE_FAILED",
                "deployment_authorized": False,
            }

        history = [self.fsm.STATES[0]]
        while self.fsm.STATES[self.fsm.current_step] != "COMPLETED":
            history.append(self.fsm.advance())

        return {
            "installation_id": installation_id,
            "health_check": "PASS_VERIFIED",
            "ficha_contract": {
                "valid": True,
                "invariants_passed": proof.ficha_invariants_passed,
                "environment_hash": proof.environment_hash,
                "health_check": "PASS_VERIFIED",
                "evidence_ref": proof.evidence_ref,
            },
            "checks": checks,
            "failed_checks": [],
            "execution_history": history,
            "status": "COMPLETED_VERIFIED",
            "deployment_authorized": False,
        }

    @staticmethod
    def _blocked(reason: str, state: str, history: List[str]) -> Dict[str, Any]:
        return {
            "health_check": "NOT_VERIFIED",
            "ficha_contract": {"valid": False},
            "reason": reason,
            "execution_history": history + [state],
            "status": "BLOCKED",
            "deployment_authorized": False,
        }
