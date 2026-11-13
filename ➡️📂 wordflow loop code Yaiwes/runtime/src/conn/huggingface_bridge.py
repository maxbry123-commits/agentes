"""Read-only, public Hugging Face Hub metadata bridge for G-023."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Callable, Dict, Literal, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

CONTRACT = "yaiwes.huggingface_bridge/v1"
ResourceKind = Literal["MODEL", "DATASET", "SKILL", "RESOURCE"]
RepoType = Literal["model", "dataset", "space"]
_SHA = re.compile(r"^[0-9a-f]{40}$")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
_API_PLURAL = {"model": "models", "dataset": "datasets", "space": "spaces"}
_MAX_METADATA_BYTES = 8 * 1024 * 1024


class HuggingFaceBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class HFResourceRequest:
    request_id: str
    kind: ResourceKind
    repo_type: RepoType
    repo_id: str
    revision: str
    path: str = ""


class HuggingFaceBridge:
    """Verify public Hub metadata; never run Jobs, CI, inference or code."""

    def __init__(self, opener: Callable[..., Any] = urlopen, timeout_seconds: float = 15.0) -> None:
        if not 0 < timeout_seconds <= 60:
            raise ValueError("INVALID_TIMEOUT")
        self._opener = opener
        self._production_transport = opener is urlopen
        self.timeout_seconds = timeout_seconds

    def verify(self, resource: HFResourceRequest) -> Dict[str, Any]:
        path = self._validate(resource)
        endpoint = self._metadata_endpoint(resource)
        request = Request(
            endpoint,
            headers={"Accept": "application/json", "User-Agent": "yaiwes-hf-bridge/1"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read(_MAX_METADATA_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return self._blocked(resource, "HF_VERIFICATION_BLOCKED", str(exc))
        if len(raw) > _MAX_METADATA_BYTES:
            return self._blocked(resource, "HF_METADATA_TOO_LARGE", "response limit exceeded")
        try:
            metadata = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._blocked(resource, "HF_METADATA_INVALID", str(exc))
        if not isinstance(metadata, Mapping):
            return self._blocked(resource, "HF_METADATA_INVALID", "object required")

        remote_sha = str(metadata.get("sha", ""))
        if remote_sha != resource.revision:
            return self._blocked(resource, "HF_REVISION_MISMATCH", remote_sha)
        if metadata.get("private") is True or metadata.get("gated") not in (False, None):
            return self._blocked(resource, "HF_PUBLIC_RESOURCE_REQUIRED", "private or gated")

        file_evidence: Dict[str, Any] | None = None
        if path:
            siblings = metadata.get("siblings")
            if not isinstance(siblings, list):
                return self._blocked(resource, "HF_FILE_LIST_MISSING", path)
            row = next(
                (item for item in siblings if isinstance(item, Mapping) and item.get("rfilename") == path),
                None,
            )
            if row is None:
                return self._blocked(resource, "HF_RESOURCE_PATH_NOT_FOUND", path)
            blob_id = str(row.get("blobId", ""))
            size = row.get("size")
            if not _SHA.fullmatch(blob_id) or not isinstance(size, int) or size < 0:
                return self._blocked(resource, "HF_FILE_METADATA_INCOMPLETE", path)
            lfs = row.get("lfs")
            file_evidence = {"path": path, "blob_id": blob_id, "size": size}
            if isinstance(lfs, Mapping):
                lfs_sha = str(lfs.get("sha256", ""))
                if not re.fullmatch(r"[0-9a-f]{64}", lfs_sha):
                    return self._blocked(resource, "HF_LFS_METADATA_INVALID", path)
                file_evidence["content_sha256"] = lfs_sha
                file_evidence["remote_lfs_metadata_only"] = True

        evidence_material = {
            "contract": CONTRACT,
            "kind": resource.kind,
            "repo_type": resource.repo_type,
            "repo_id": resource.repo_id,
            "revision": resource.revision,
            "file": file_evidence,
        }
        digest = hashlib.sha256(
            json.dumps(evidence_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {
            **evidence_material,
            "status": "VERIFIED_PUBLIC_HF_RESOURCE" if self._production_transport else "VALIDATED_TEST_FIXTURE",
            "verified": self._production_transport,
            "verification_authorized": self._production_transport,
            "execution_authorized": False,
            "hf_jobs_allowed": False,
            "hf_ci_allowed": False,
            "secrets_used": False,
            "download_performed": False,
            "no_lfs_transfer": True,
            "evidence_ref": "sha256:" + digest,
        }

    def _validate(self, resource: HFResourceRequest) -> str:
        if not _REQUEST_ID.fullmatch(resource.request_id):
            raise HuggingFaceBridgeError("HF_REQUEST_ID_INVALID")
        if resource.kind not in {"MODEL", "DATASET", "SKILL", "RESOURCE"}:
            raise HuggingFaceBridgeError("HF_KIND_NOT_ALLOWED")
        if resource.repo_type not in _API_PLURAL:
            raise HuggingFaceBridgeError("HF_REPO_TYPE_NOT_ALLOWED")
        if resource.kind == "MODEL" and resource.repo_type != "model":
            raise HuggingFaceBridgeError("MODEL_REPO_TYPE_REQUIRED")
        if resource.kind == "DATASET" and resource.repo_type != "dataset":
            raise HuggingFaceBridgeError("DATASET_REPO_TYPE_REQUIRED")
        if not _REPO.fullmatch(resource.repo_id):
            raise HuggingFaceBridgeError("HF_REPO_ID_INVALID")
        if not _SHA.fullmatch(resource.revision):
            raise HuggingFaceBridgeError("PINNED_HF_REVISION_REQUIRED")
        path = resource.path.replace("\\", "/").strip()
        parsed = PurePosixPath(path)
        if path and (parsed.is_absolute() or ".." in parsed.parts):
            raise HuggingFaceBridgeError("HF_RESOURCE_PATH_INVALID")
        if resource.kind == "SKILL" and (not path or parsed.name != "SKILL.md"):
            raise HuggingFaceBridgeError("HF_SKILL_MD_REQUIRED")
        if resource.kind == "RESOURCE" and not path:
            raise HuggingFaceBridgeError("HF_RESOURCE_PATH_REQUIRED")
        return parsed.as_posix() if path else ""

    @staticmethod
    def _metadata_endpoint(resource: HFResourceRequest) -> str:
        repo = "/".join(quote(part, safe="") for part in resource.repo_id.split("/"))
        plural = _API_PLURAL[resource.repo_type]
        return f"https://huggingface.co/api/{plural}/{repo}/revision/{resource.revision}?blobs=true"

    @staticmethod
    def _blocked(resource: HFResourceRequest, status: str, detail: str) -> Dict[str, Any]:
        return {
            "contract": CONTRACT,
            "request_id": resource.request_id,
            "status": status,
            "detail": detail,
            "verified": False,
            "verification_authorized": False,
            "execution_authorized": False,
            "hf_jobs_allowed": False,
            "hf_ci_allowed": False,
            "secrets_used": False,
        }
