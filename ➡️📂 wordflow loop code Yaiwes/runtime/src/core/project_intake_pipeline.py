"""Run-scoped 1..100 file intake for YAIWES programming work.

Reuses FileAuditContract for each text file and produces a deterministic architecture
seed plus a safe workspace code destination. It never generates or executes code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping, Sequence

try:
    from .file_audit_contract import FileAuditContract, SourceDescriptor, AuditError
except ImportError:
    from file_audit_contract import FileAuditContract, SourceDescriptor, AuditError  # type: ignore

_PROJECT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_FILES = 100


class ProjectIntakeError(ValueError):
    pass


@dataclass(frozen=True)
class InputFile:
    source_id: str
    filename: str
    content: str
    provenance: str


@dataclass(frozen=True)
class ProjectIntakeResult:
    schema: str
    project_id: str
    profile: str
    destination: str
    file_count: int
    files: tuple[Mapping[str, Any], ...]
    architecture: Mapping[str, Any]
    requirements: tuple[Mapping[str, Any], ...]
    risks: tuple[str, ...]
    execution_authorized: bool = False
    code_generation_authorized: bool = False


def _safe_basename(name: str) -> str:
    value = name.replace("\\", "/").strip()
    if not value or PurePosixPath(value).name != value or ".." in PurePosixPath(value).parts:
        raise ProjectIntakeError("UNSAFE_INPUT_FILENAME")
    return value


def _normalize_project_id(value: str) -> str:
    value = value.strip()
    if not _PROJECT.fullmatch(value):
        raise ProjectIntakeError("PROJECT_ID_INVALID")
    return value


def _project_from_json(filename: str, content: str) -> str | None:
    if filename.lower() not in {"package.json", "project.json", "yaiwes-project.json"}:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping):
        return None
    for key in ("project_id", "name"):
        candidate = str(payload.get(key, "")).strip()
        if _PROJECT.fullmatch(candidate):
            return candidate
    return None


def _project_from_markdown(filename: str, content: str) -> str | None:
    if Path(filename).suffix.lower() not in {".md", ".markdown"}:
        return None
    for line in content.splitlines():
        s=line.strip()
        if s.startswith("# "):
            candidate=re.sub(r"[^A-Za-z0-9._-]+", "-", s[2:].strip()).strip("-")[:64]
            if _PROJECT.fullmatch(candidate):
                return candidate
            break
    return None


def infer_project_id(files: Sequence[InputFile], project_hint: str = "") -> str:
    if project_hint.strip():
        return _normalize_project_id(project_hint)
    candidates: list[str] = []
    for item in files:
        for candidate in (
            _project_from_json(item.filename, item.content),
            _project_from_markdown(item.filename, item.content),
        ):
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ProjectIntakeError("PROJECT_ID_NOT_DETECTED")
    raise ProjectIntakeError("PROJECT_ID_AMBIGUOUS:" + ",".join(sorted(candidates)))


def analyze_project(
    files: Iterable[InputFile],
    *,
    profile: str,
    project_hint: str = "",
) -> ProjectIntakeResult:
    items=tuple(files)
    if not (1 <= len(items) <= _MAX_FILES):
        raise ProjectIntakeError("FILE_COUNT_MUST_BE_1_TO_100")
    profile=profile.strip().lower()
    if profile not in {"backend","frontend","general"}:
        raise ProjectIntakeError("PROFILE_INVALID")

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    normalized: list[InputFile] = []
    for item in items:
        if not isinstance(item, InputFile):
            raise ProjectIntakeError("INPUT_FILE_REQUIRED")
        filename=_safe_basename(item.filename)
        if not item.source_id.strip() or not item.provenance.strip():
            raise ProjectIntakeError("INPUT_PROVENANCE_REQUIRED")
        if item.source_id in seen_ids:
            raise ProjectIntakeError("DUPLICATE_SOURCE_ID")
        if filename.lower() in seen_names:
            raise ProjectIntakeError("DUPLICATE_FILENAME")
        seen_ids.add(item.source_id)
        seen_names.add(filename.lower())
        normalized.append(InputFile(item.source_id.strip(), filename, item.content, item.provenance.strip()))

    project_id=infer_project_id(normalized, project_hint)
    auditor=FileAuditContract()
    audit_rows=[]
    formats=set()
    dependencies=set()
    capabilities=set()
    risks=set()
    requirements=[]
    for item in normalized:
        try:
            audit=auditor.audit_text(
                SourceDescriptor(
                    source_id=item.source_id,
                    filename=item.filename,
                    provenance=item.provenance,
                ),
                item.content,
            )
        except AuditError as exc:
            raise ProjectIntakeError(f"AUDIT_FAIL:{item.filename}:{exc}") from exc
        formats.add(audit.format)
        dependencies.update(audit.dependencies)
        capabilities.update(audit.capabilities)
        risks.update(audit.risks)
        for req in audit.requirements:
            row=dict(req)
            row["source_id"]=item.source_id
            row["filename"]=item.filename
            requirements.append(row)
        audit_rows.append({
            "source_id": item.source_id,
            "filename": item.filename,
            "provenance": item.provenance,
            "sha256": audit.sha256,
            "size_bytes": audit.size_bytes,
            "format": audit.format,
            "risk_level": audit.risk_level.value,
            "architecture": dict(audit.architecture),
            "interfaces": list(audit.interfaces),
            "dependencies": list(audit.dependencies),
            "capabilities": list(audit.capabilities),
            "risks": list(audit.risks),
        })

    architecture={
        "project_id": project_id,
        "profile": profile,
        "formats": sorted(formats),
        "dependencies": sorted(dependencies),
        "capabilities": sorted(capabilities),
        "risk_count": len(risks),
        "source_files": [row["filename"] for row in audit_rows],
        "pipeline": [
            "INPUT_FILES",
            "AUDIT",
            "ARCHITECTURE",
            "TASK_GRAPH",
            "SKILL_SELECTION",
            "SHERIFF",
            "EXECUTION",
            "COMPLETION_GATE",
            "EVIDENCE",
        ],
    }
    return ProjectIntakeResult(
        schema="yaiwes.project-intake/v1",
        project_id=project_id,
        profile=profile,
        destination=f"➡️📂 Wordflow LOOP Yaiwes/workspace/code/{project_id}",
        file_count=len(audit_rows),
        files=tuple(audit_rows),
        architecture=architecture,
        requirements=tuple(requirements),
        risks=tuple(sorted(risks)),
        execution_authorized=False,
        code_generation_authorized=False,
    )
