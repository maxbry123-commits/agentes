"""loop-engineer/evidence@1 — hashed evidence + artifact provenance.

``loop doctor`` discovers and validates records from the declared location
``.loop/evidence/*.json`` (reference/repo-os-contract.md #17), reports
``self_verified_evidence`` / ``missing_evidence_record``, and — since the
evidence-wiring release — composes ``verify_evidence()`` below over every
structurally-valid record, so a referenced artifact that does not hash to the
digest its record declares fails doctor as ``hash_mismatch``. Doctor also
compares the latest record per task against the live TASKS.json goalpost
(``policy_digest_mismatch``), and re-hashes whatever an event bound into the
chain (``evidence_chain_mismatch`` / ``missing_bound_evidence``).

What is still NOT checked here: ``code_digest`` is never re-hashed against the
verifier file (a verify script legitimately changes between runs, and an
unbaselined comparison would fire on every honest edit), and none of this proves
provenance — a hand-written record whose pointer resolves and whose digests are
self-consistent is indistinguishable from one a dispatch produced. Verification
proves the pointer, never the producer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .contract import ContractIssue, _resolve_requested_mode, _schemas_dir
from .verifier import CODE_DIGEST_BASES


EVIDENCE_SCHEMA_ID = "loop-engineer/evidence@1"
VERIFY_BUNDLE_KIND = "verify-bundle"
_URI_PATTERN = re.compile(r"^(?!/)(?![A-Za-z][A-Za-z0-9+.\-]*://).+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def verify_bundle_is_green(bundle: Mapping[str, Any]) -> bool:
    """The repo's ONE green-marker rule for a verify bundle.

    A bundle is green when it says so explicitly — ``outcome == "PASS"`` or
    ``passed is True``. A bundle carrying only a numeric ``score`` reads RED: a
    score is not a verdict, and treating one as a pass is exactly the false
    completion this kernel exists to refuse (the rule originated in
    ``scripts/metrics.py``, which now imports it rather than restating it).
    """
    if not isinstance(bundle, Mapping):
        return False
    return str(bundle.get("outcome", "")).upper() == "PASS" or bundle.get("passed") is True


class EvidenceError(ValueError):
    """The workspace-root precondition for evidence verification was not met."""


def _load_evidence_schema() -> dict[str, Any]:
    return json.loads((_schemas_dir() / "evidence.schema.json").read_text(encoding="utf-8"))


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_valid_uri(value: Any) -> bool:
    return _is_non_empty_string(value) and _URI_PATTERN.fullmatch(value) is not None


def _is_sha256_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None)


def _structural_validate_evidence(data: dict[str, Any]) -> list[ContractIssue]:
    """Stdlib fallback equivalent to the schema's complete evidence surface."""
    issues: list[ContractIssue] = []
    if data.get("schema") != EVIDENCE_SCHEMA_ID:
        issues.append(ContractIssue("invalid_evidence", f"schema must equal {EVIDENCE_SCHEMA_ID!r}"))
    for field in ("id", "kind", "media_type", "created_at"):
        if not _is_non_empty_string(data.get(field)):
            issues.append(ContractIssue("invalid_evidence", f"{field} must be a non-empty string"))
    if not _is_valid_uri(data.get("uri")):
        issues.append(ContractIssue("invalid_uri", "uri must be a non-empty workspace-relative POSIX path without a URI scheme"))
    sha256 = data.get("sha256")
    if not isinstance(sha256, str) or _SHA256_PATTERN.fullmatch(sha256) is None:
        issues.append(ContractIssue("invalid_evidence", "sha256 must be a 64-character lowercase hexadecimal string"))

    produced_by = data.get("produced_by")
    if not isinstance(produced_by, dict):
        issues.append(ContractIssue("invalid_evidence", "produced_by must be an object"))
    else:
        for field in ("run_id", "task_id", "attempt", "executor"):
            if field not in produced_by:
                issues.append(ContractIssue("invalid_evidence", f"produced_by missing required field {field!r}"))
        if not _is_non_empty_string(produced_by.get("run_id")):
            issues.append(ContractIssue("invalid_evidence", "produced_by.run_id must be a non-empty string"))
        task_id = produced_by.get("task_id")
        if task_id is not None and not isinstance(task_id, str):
            issues.append(ContractIssue("invalid_evidence", "produced_by.task_id must be a string or null"))
        attempt = produced_by.get("attempt")
        if attempt is not None and (not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1):
            issues.append(ContractIssue("invalid_evidence", "produced_by.attempt must be an integer >= 1 or null"))
        if not _is_non_empty_string(produced_by.get("executor")):
            issues.append(ContractIssue("invalid_evidence", "produced_by.executor must be a non-empty string"))

    verified_by = data.get("verified_by")
    if verified_by is not None:
        if not isinstance(verified_by, dict):
            issues.append(ContractIssue("invalid_evidence", "verified_by must be an object or null"))
        else:
            for field in ("by", "at"):
                if not _is_non_empty_string(verified_by.get(field)):
                    issues.append(ContractIssue("invalid_evidence", f"verified_by.{field} must be a non-empty string"))
            command = verified_by.get("command")
            if command is not None and not isinstance(command, str):
                issues.append(ContractIssue("invalid_evidence", "verified_by.command must be a string or null"))
            for field in ("code_digest", "policy_digest"):
                if not _is_sha256_or_null(verified_by.get(field)):
                    issues.append(ContractIssue(
                        "invalid_evidence",
                        f"verified_by.{field} must be a 64-character lowercase hexadecimal string or null"))
            basis = verified_by.get("code_digest_basis")
            if basis is not None and basis not in CODE_DIGEST_BASES:
                issues.append(ContractIssue(
                    "invalid_evidence",
                    f"verified_by.code_digest_basis must be null or one of {CODE_DIGEST_BASES}"))

    policy_result = data.get("policy_result")
    if policy_result is not None:
        if not isinstance(policy_result, dict):
            issues.append(ContractIssue("invalid_evidence", "policy_result must be an object or null"))
        elif not isinstance(policy_result.get("ok"), bool):
            issues.append(ContractIssue("invalid_evidence", "policy_result.ok must be a boolean"))
    return issues


def _jsonschema_validate_evidence(data: dict[str, Any]) -> list[ContractIssue]:
    import jsonschema  # type: ignore

    validator = jsonschema.Draft202012Validator(_load_evidence_schema())
    issues: list[ContractIssue] = []
    for error in validator.iter_errors(data):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        code = "invalid_uri" if tuple(error.absolute_path) == ("uri",) else "invalid_evidence"
        issues.append(ContractIssue(code, f"{location}: {error.message}"))
    return issues


def evidence_issues(data: Any, *, resolved_mode: str) -> list[ContractIssue]:
    """Mode-dispatched issue list for one record — the seam doctor discovery reuses."""
    if not isinstance(data, dict):
        return [ContractIssue("invalid_evidence", "evidence record must be an object")]
    if resolved_mode == "jsonschema":
        return _jsonschema_validate_evidence(data)
    return _structural_validate_evidence(data)


def validate_evidence(data: dict[str, Any], *, mode: str | None = None) -> dict[str, Any]:
    """Validate a standalone evidence@1 record in the requested validation mode."""
    requested_mode, resolved_mode = _resolve_requested_mode(mode)
    issues = evidence_issues(data, resolved_mode=resolved_mode)
    return {"ok": not issues, "validation_mode": resolved_mode, "requested_mode": requested_mode,
            "schemas_checked": [EVIDENCE_SCHEMA_ID], "issues": issues}


def verify_evidence(evidence: Mapping[str, Any], *, workspace_root: str | Path) -> dict[str, Any]:
    """Verify one evidence record's workspace containment and SHA-256 content."""
    root = Path(workspace_root)
    if not root.is_dir():
        raise EvidenceError(f"workspace_root must be an existing directory: {root}")

    checks: dict[str, bool | None] = {
        "structural": None, "within_workspace": None, "path_exists": None, "hash_match": None,
    }
    record = dict(evidence) if isinstance(evidence, Mapping) else evidence
    report = validate_evidence(record, mode="basic")
    checks["structural"] = report["ok"]
    if not report["ok"]:
        return {"ok": False, "checks": checks, "issues": report["issues"]}

    uri = record["uri"]
    if not _is_valid_uri(uri):
        checks["structural"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("invalid_uri", "uri must be a workspace-relative POSIX path without a URI scheme")]}
    try:
        resolved = (root / uri).resolve(strict=True)
    except ValueError:
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("invalid_uri", f"uri cannot be resolved as a path: {uri}")]}
    except (OSError, FileNotFoundError, RuntimeError):
        checks["path_exists"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("missing_evidence_path", f"evidence path does not exist: {uri}")]}

    checks["path_exists"] = True
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        checks["within_workspace"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("workspace_escape", f"evidence path escapes workspace: {uri}")]}
    checks["within_workspace"] = True
    try:
        fd = os.open(
            resolved,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
    except OSError:
        checks["path_exists"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("missing_evidence_path", f"evidence path is unavailable: {uri}")]}
    try:
        file_stat = os.fstat(fd)
    except OSError:
        os.close(fd)
        checks["path_exists"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("missing_evidence_path", f"evidence path is unavailable: {uri}")]}
    if not stat.S_ISREG(file_stat.st_mode):
        os.close(fd)
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("not_a_file", f"evidence path is not a file: {uri}")]}

    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "rb") as source:
            while chunk := source.read(64 * 1024):
                digest.update(chunk)
    except OSError:
        checks["path_exists"] = False
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("missing_evidence_path", f"evidence path is unavailable: {uri}")]}
    checks["hash_match"] = digest.hexdigest() == record["sha256"]
    if not checks["hash_match"]:
        return {"ok": False, "checks": checks,
                "issues": [ContractIssue("hash_mismatch", f"sha256 does not match evidence path: {uri}")]}
    return {"ok": True, "checks": checks, "issues": []}


def artifact_object_path(workspace_root: str | Path, sha256: str) -> Path:
    """Return evidence@1's content-addressed artifact location without I/O."""
    return Path(workspace_root) / ".loop" / "artifacts" / "objects" / sha256[:2] / sha256


#: A chain-bound path is attacker-nameable — any event may declare any string. A gate
#: must therefore never perform an unbounded read on one. 64 MiB is far above any
#: artifact this kernel writes and far below "read whatever is at the other end".
MAX_BOUND_ARTIFACT_BYTES = 64 * 1024 * 1024

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def _lexical_escape(rel: object) -> str | None:
    """Why this declared path is not workspace-relative — decided with ZERO I/O.

    Runs before anything is opened, so an escaping path is reported rather than read.
    """
    if not isinstance(rel, str) or not rel.strip():
        return "is not a non-empty path"
    if "\\" in rel:
        return "contains a backslash, which is not a workspace-relative POSIX path"
    if _DRIVE_PREFIX.match(rel):
        return "names a drive letter"
    pure = PurePosixPath(rel)
    if pure.is_absolute():
        return "is an absolute path"
    if ".." in pure.parts:
        return "traverses out of the workspace with '..'"
    return None


def hash_bound_artifact(
    workspace_root: str | Path, rel: object, *, max_bytes: int = MAX_BOUND_ARTIFACT_BYTES,
) -> tuple[str, str]:
    """Containment-check a chain-bound path, then stream-hash it under a cap.

    Returns ``(code, detail)``:

    * ``("ok", <hex digest>)``;
    * ``("escape", <why>)`` — the path is not inside the workspace. For a lexical
      escape NOTHING on disk was touched; a symlinked escape is caught after
      resolution, exactly as ``verify_evidence`` catches it;
    * ``("unreadable", <why>)`` — contained, but its bytes could not be hashed:
      absent, not a regular file (so ``/dev/zero`` and friends are refused rather
      than read forever), or larger than ``max_bytes``.
    """
    escape = _lexical_escape(rel)
    if escape is not None:
        return "escape", escape
    root = Path(workspace_root)
    try:
        resolved = (root / str(rel)).resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        return "unreadable", "is absent or cannot be resolved"
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return "escape", "resolves outside the workspace (a symlinked component)"
    try:
        fd = os.open(resolved, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return "unreadable", "is absent or cannot be opened"
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            return "unreadable", "is not a regular file"
        if file_stat.st_size > max_bytes:
            return "unreadable", (f"is {file_stat.st_size} bytes, above the {max_bytes}-byte "
                                  f"bound-artifact read cap, so its digest was not computed")
        digest = hashlib.sha256()
        read = 0
        duplicate = os.dup(fd)
        try:
            source = os.fdopen(duplicate, "rb")
        except OSError:
            os.close(duplicate)          # fdopen never took ownership
            raise
        with source:
            while chunk := source.read(64 * 1024):
                read += len(chunk)
                if read > max_bytes:
                    return "unreadable", (f"grew past the {max_bytes}-byte bound-artifact "
                                          f"read cap while being hashed")
                digest.update(chunk)
    except OSError:
        return "unreadable", "is absent or cannot be read"
    finally:
        os.close(fd)
    return "ok", digest.hexdigest()
