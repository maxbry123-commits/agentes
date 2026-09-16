import sys
import unittest

from runtime.src.install.deployment_gate import DeploymentEvidence, evaluate_deployment
from runtime.src.uek.sandbox_manager import SandboxManager


class SandboxEnforcementG022Tests(unittest.TestCase):
    def test_external_attestation_cannot_authorize_execution(self):
        result = SandboxManager().acquire_sandbox(
            "python",
            {
                "backend": "bubblewrap",
                "process_isolation": True,
                "filesystem_isolation": True,
                "network_enforced": True,
                "memory_enforced": True,
                "evidence_ref": "evidence://fabricated",
            },
        )
        self.assertEqual(result["status"], "BLOCKED_UNTRUSTED_ATTESTATION")
        self.assertFalse(result["execution_authorized"])

    def test_missing_backend_fails_closed(self):
        result = SandboxManager(backend_path="/missing/bwrap").execute_isolated(
            "python", [sys.executable, "-c", "print('must-not-run')"]
        )
        self.assertEqual(result["status"], "BLOCKED_BACKEND_UNAVAILABLE")
        self.assertFalse(result["execution_authorized"])

    def test_arbitrary_executable_cannot_impersonate_backend(self):
        result = SandboxManager(backend_path="/bin/true").execute_isolated(
            "python", [sys.executable, "-c", "print('must-not-run')"]
        )
        self.assertEqual(result["status"], "BLOCKED_UNTRUSTED_BACKEND")
        self.assertFalse(result["execution_authorized"])

    def test_real_backend_probe_never_fabricates_success(self):
        result = SandboxManager(timeout_seconds=3).execute_isolated(
            "python", [sys.executable, "-c", "print('isolated')"]
        )
        if result["status"] == "EXECUTION_VERIFIED":
            self.assertTrue(all(result["checks"].values()))
            self.assertTrue(result["evidence_ref"].startswith("sha256:"))
            self.assertEqual(result["stdout"].strip(), "isolated")
        else:
            self.assertFalse(result["execution_authorized"])
            self.assertIn("BLOCKED_", result["status"])

    def test_deploy_remains_blocked_after_failed_physical_probe(self):
        probe = SandboxManager(backend_path="/missing/bwrap").execute_isolated(
            "python", [sys.executable, "-c", "print('no')"]
        )
        evidence = DeploymentEvidence(
            artifact_hash_verified=True,
            installation_verified=True,
            sandbox_verified=probe["status"] == "EXECUTION_VERIFIED",
            tests_pass=True,
            independent_review_pass=True,
            output_schema_pass=True,
            checkpoint_created=True,
            rollback_ready=True,
            health_check_pass=True,
            evidence_refs=("evidence://g022-negative",),
        )
        decision = evaluate_deployment(evidence)
        self.assertEqual(decision.status, "PROMOTION_BLOCKED")
        self.assertFalse(decision.promote_authorized)


if __name__ == "__main__":
    unittest.main()
