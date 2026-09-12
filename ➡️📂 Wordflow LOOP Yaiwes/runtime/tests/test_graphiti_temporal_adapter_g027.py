from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from runtime.src.core.graphiti_temporal_adapter import (
    PLUGIN_ID,
    SOURCE_TREE_SHA,
    build_add_episode_request,
    build_search_request,
    canonical_source_proof,
    graphiti_ficha_manifest,
    sandbox_probe,
    verify_graphiti_fables_registration,
    verify_source_proof,
)


class FakeSandboxBlocked:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def execute_isolated(self, sandbox_type, argv):
        return {
            "status": "BLOCKED_BACKEND_UNAVAILABLE",
            "execution_authorized": False,
            "type": sandbox_type,
        }


class FakeSandboxPass:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def execute_isolated(self, sandbox_type, argv):
        return {
            "status": "EXECUTION_VERIFIED",
            "execution_authorized": True,
            "type": sandbox_type,
            "evidence_ref": "sha256:" + "1" * 64,
        }


class GraphitiTemporalAdapterTests(unittest.TestCase):
    def test_source_proof_is_pinned_and_mismatch_fails_closed(self):
        proof = canonical_source_proof()
        self.assertEqual(proof.tree_sha, SOURCE_TREE_SHA)
        with self.assertRaisesRegex(ValueError, "GRAPHITI_SOURCE_PROOF_MISMATCH"):
            verify_source_proof(
                {
                    "repository": proof.repository,
                    "path": proof.path,
                    "tree_sha": "0" * 40,
                    "entry_blob": proof.entry_blob,
                    "init_blob": proof.init_blob,
                    "license_blob": proof.license_blob,
                    "license": proof.license,
                }
            )

    def test_episode_request_is_temporal_and_not_authorized(self):
        request = build_add_episode_request(
            name="decision-1",
            content="Director approved canonical Fables.",
            source_description="Crazy Wall",
            reference_time=datetime(2026, 9, 12, 20, 0, tzinfo=timezone.utc),
            group_id="yaiwes",
        )
        self.assertEqual(request["operation"], "add_episode")
        self.assertEqual(request["payload"]["reference_time"], "2026-09-12T20:00:00Z")
        self.assertFalse(request["execution_authorized"])
        with self.assertRaisesRegex(ValueError, "REFERENCE_TIME_TIMEZONE_REQUIRED"):
            build_add_episode_request(
                name="x",
                content="y",
                source_description="z",
                reference_time=datetime(2026, 9, 12, 20, 0),
                group_id="yaiwes",
            )

    def test_search_request_bounds(self):
        request = build_search_request(query="where is source proof", group_id="yaiwes", limit=25)
        self.assertEqual(request["payload"]["limit"], 25)
        self.assertFalse(request["execution_authorized"])
        for bad in (0, 101, True):
            with self.assertRaisesRegex(ValueError, "LIMIT_OUT_OF_RANGE"):
                build_search_request(query="q", group_id="g", limit=bad)

    def test_ficha_manifest_requires_process_sandbox(self):
        manifest = graphiti_ficha_manifest()
        self.assertEqual(manifest["artifact_id"], PLUGIN_ID)
        self.assertEqual(manifest["seguridad"]["sandbox"], "process")
        self.assertEqual(manifest["ejecucion"]["transport"], "importlib")
        self.assertEqual(manifest["ejecucion"]["runtime_type"], "io")

    def test_registration_fails_closed_when_base_fables_not_verified(self):
        result = verify_graphiti_fables_registration(
            base_binding_verifier=lambda: SimpleNamespace(verified=False)
        )
        self.assertFalse(result.verified)
        self.assertFalse(result.execution_authorized)
        self.assertIn("GRAPHITI_FABLES_PRECONDITION_FAILED", result.reason_codes)

    def test_sandbox_probe_blocks_without_backend(self):
        result = sandbox_probe(manager_factory=FakeSandboxBlocked)
        self.assertEqual(result["status"], "BLOCKED_BY_SANDBOX")
        self.assertFalse(result["execution_authorized"])

    def test_sandbox_probe_only_authorizes_verified_execution(self):
        result = sandbox_probe(manager_factory=FakeSandboxPass)
        self.assertEqual(result["status"], "SANDBOX_VERIFIED")
        self.assertTrue(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
