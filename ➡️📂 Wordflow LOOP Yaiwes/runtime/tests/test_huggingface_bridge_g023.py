import io
import json
import unittest

from runtime.src.conn.huggingface_bridge import (
    HFResourceRequest,
    HuggingFaceBridge,
    HuggingFaceBridgeError,
)
from runtime.src.conn.manager import ConnectionManager
from runtime.src.storage.artifact_router import ArtifactRouter

REVISION = "a" * 40


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _opener(payload):
    def open_request(request, timeout):
        assert request.full_url.startswith("https://huggingface.co/api/")
        assert "authorization" not in {key.lower() for key in request.headers}
        return _Response(json.dumps(payload).encode("utf-8"))

    return open_request


class HuggingFaceBridgeG023Tests(unittest.TestCase):
    def test_model_and_dataset_must_use_matching_repo_type(self):
        bridge = HuggingFaceBridge(_opener({}))
        with self.assertRaisesRegex(HuggingFaceBridgeError, "MODEL_REPO_TYPE_REQUIRED"):
            bridge.verify(HFResourceRequest("1", "MODEL", "dataset", "org/repo", REVISION))
        with self.assertRaisesRegex(HuggingFaceBridgeError, "DATASET_REPO_TYPE_REQUIRED"):
            bridge.verify(HFResourceRequest("2", "DATASET", "model", "org/repo", REVISION))

    def test_unpinned_revision_and_unsafe_path_fail_closed(self):
        bridge = HuggingFaceBridge(_opener({}))
        with self.assertRaisesRegex(HuggingFaceBridgeError, "PINNED_HF_REVISION_REQUIRED"):
            bridge.verify(HFResourceRequest("1", "MODEL", "model", "org/repo", "main"))
        with self.assertRaisesRegex(HuggingFaceBridgeError, "HF_RESOURCE_PATH_INVALID"):
            bridge.verify(HFResourceRequest("2", "RESOURCE", "model", "org/repo", REVISION, "../x"))

    def test_skill_requires_exact_skill_md_and_verified_file_metadata(self):
        payload = {
            "sha": REVISION,
            "private": False,
            "gated": False,
            "siblings": [{"rfilename": "skills/demo/SKILL.md", "blobId": "b" * 40, "size": 91}],
        }
        result = HuggingFaceBridge(_opener(payload)).verify(
            HFResourceRequest("s1", "SKILL", "dataset", "org/skills", REVISION, "skills/demo/SKILL.md")
        )
        self.assertEqual(result["status"], "VALIDATED_TEST_FIXTURE")
        self.assertFalse(result["verified"])
        self.assertFalse(result["verification_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["hf_jobs_allowed"])
        self.assertFalse(result["secrets_used"])

    def test_revision_mismatch_private_and_missing_path_are_blocked(self):
        base = HFResourceRequest("r1", "RESOURCE", "model", "org/repo", REVISION, "config.json")
        mismatch = HuggingFaceBridge(_opener({"sha": "c" * 40})).verify(base)
        self.assertEqual(mismatch["status"], "HF_REVISION_MISMATCH")
        private = HuggingFaceBridge(_opener({"sha": REVISION, "private": True})).verify(base)
        self.assertEqual(private["status"], "HF_PUBLIC_RESOURCE_REQUIRED")
        missing = HuggingFaceBridge(
            _opener({"sha": REVISION, "private": False, "gated": False, "siblings": []})
        ).verify(base)
        self.assertEqual(missing["status"], "HF_RESOURCE_PATH_NOT_FOUND")

    def test_hf_static_paths_no_longer_fabricate_health_or_acquisition(self):
        manager = ConnectionManager()
        registered = manager.register_connection("huggingface", {"endpoint": "https://huggingface.co"})
        self.assertEqual(registered["status"], "CONFIGURED_NOT_VERIFIED")
        self.assertFalse(manager.preflight_check(registered["conn_id"])["passed"])
        artifact = ArtifactRouter().acquire_artifact(
            {"artifact_id": "hf1", "source_provider": "huggingface", "raw_data": b"fake"}
        )
        self.assertEqual(artifact["status"], "USE_VERIFIED_HUGGINGFACE_BRIDGE")
        self.assertFalse(artifact["hash_verified"])

    def test_lfs_is_metadata_only_and_never_transferred(self):
        payload = {
            "sha": REVISION,
            "private": False,
            "gated": False,
            "siblings": [
                {
                    "rfilename": "model.safetensors",
                    "blobId": "d" * 40,
                    "size": 10,
                    "lfs": {"sha256": "e" * 64, "size": 10, "pointerSize": 127},
                }
            ],
        }
        result = HuggingFaceBridge(_opener(payload)).verify(
            HFResourceRequest("m1", "RESOURCE", "model", "org/repo", REVISION, "model.safetensors")
        )
        self.assertTrue(result["no_lfs_transfer"])
        self.assertTrue(result["file"]["remote_lfs_metadata_only"])
        self.assertFalse(result["download_performed"])


if __name__ == "__main__":
    unittest.main()
