from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class AuditError(ValueError):
    """Fail-closed error for invalid audit inputs or Council output."""


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


ALLOWED_COUNCIL_VERDICTS = {"ADOPT", "ADAPT", "REJECT", "RESEARCH_MORE"}
ALLOWED_FINDING_KINDS = {
    "architecture",
    "capability",
    "dependency",
    "interface",
    "risk",
    "security",
    "test",
    "placement_hint",
}


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    filename: str
    provenance: str
    media_type: str = "text/plain"


@dataclass(frozen=True)
class CouncilFinding:
    member_id: str
    finding_kind: str
    statement: str
    evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class CouncilDecision:
    verdict: str
    rationale: str
    findings: tuple[CouncilFinding, ...] = ()
    dissent_count: int = 0


@dataclass(frozen=True)
class AuditResult:
    contract: str
    source: SourceDescriptor
    sha256: str
    size_bytes: int
    format: str
    architecture: Mapping[str, Any]
    interfaces: tuple[str, ...]
    dependencies: tuple[str, ...]
    capabilities: tuple[str, ...]
    risks: tuple[str, ...]
    risk_level: RiskLevel
    requirements: tuple[Mapping[str, Any], ...]
    council: CouncilDecision | None = None
    executable_action_authorized: bool = False

    def canonical_json(self) -> str:
        payload = asdict(self)
        payload["risk_level"] = self.risk_level.value
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class FileAuditContract:
    """Deterministic audit boundary before task generation.

    Council output is advisory and schema-normalized. It never grants execution,
    deployment, filesystem or network permission.
    """

    CONTRACT = "yaiwes.file_audit/v1"

    def audit_text(
        self,
        source: SourceDescriptor,
        text: str,
        *,
        council_output: Mapping[str, Any] | None = None,
    ) -> AuditResult:
        self._validate_source(source)
        if not isinstance(text, str):
            raise AuditError("AUDIT_TEXT_REQUIRED")

        raw = text.encode("utf-8")
        fmt = self._detect_format(source.filename, text)
        architecture, interfaces, dependencies, capabilities, risks = self._inspect(fmt, text)
        risk_level = self._risk_level(risks)
        requirements = self._requirements(architecture, interfaces, dependencies, capabilities, risks)
        council = self.normalize_council(council_output) if council_output is not None else None

        return AuditResult(
            contract=self.CONTRACT,
            source=source,
            sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),
            format=fmt,
            architecture=architecture,
            interfaces=tuple(sorted(set(interfaces))),
            dependencies=tuple(sorted(set(dependencies))),
            capabilities=tuple(sorted(set(capabilities))),
            risks=tuple(sorted(set(risks))),
            risk_level=risk_level,
            requirements=tuple(requirements),
            council=council,
            executable_action_authorized=False,
        )

    def normalize_council(self, payload: Mapping[str, Any]) -> CouncilDecision:
        if not isinstance(payload, Mapping):
            raise AuditError("COUNCIL_SCHEMA_INVALID")
        verdict = str(payload.get("verdict", "")).upper()
        rationale = str(payload.get("rationale", "")).strip()
        if verdict not in ALLOWED_COUNCIL_VERDICTS or not rationale:
            raise AuditError("COUNCIL_SCHEMA_INVALID")

        raw_findings = payload.get("findings", [])
        if not isinstance(raw_findings, Sequence) or isinstance(raw_findings, (str, bytes)):
            raise AuditError("COUNCIL_FINDINGS_INVALID")

        findings: list[CouncilFinding] = []
        members: set[str] = set()
        for raw in raw_findings:
            if not isinstance(raw, Mapping):
                raise AuditError("COUNCIL_FINDING_INVALID")
            member_id = str(raw.get("member_id", "")).strip()
            kind = str(raw.get("finding_kind", "")).strip()
            statement = str(raw.get("statement", "")).strip()
            confidence = raw.get("confidence", 0.0)
            refs = raw.get("evidence_refs", [])
            if not member_id or kind not in ALLOWED_FINDING_KINDS or not statement:
                raise AuditError("COUNCIL_FINDING_INVALID")
            if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
                raise AuditError("COUNCIL_CONFIDENCE_INVALID")
            if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
                raise AuditError("COUNCIL_EVIDENCE_REFS_INVALID")
            ref_tuple = tuple(str(ref).strip() for ref in refs if str(ref).strip())
            findings.append(CouncilFinding(member_id, kind, statement, ref_tuple, float(confidence)))
            members.add(member_id)

        dissent_count = payload.get("dissent_count", 0)
        if not isinstance(dissent_count, int) or dissent_count < 0 or dissent_count > len(members):
            raise AuditError("COUNCIL_DISSENT_INVALID")

        return CouncilDecision(verdict, rationale, tuple(findings), dissent_count)

    @staticmethod
    def _validate_source(source: SourceDescriptor) -> None:
        if not source.source_id.strip() or not source.filename.strip() or not source.provenance.strip():
            raise AuditError("SOURCE_DESCRIPTOR_INCOMPLETE")
        if Path(source.filename).name != source.filename:
            raise AuditError("SOURCE_FILENAME_MUST_BE_BASENAME")

    @staticmethod
    def _detect_format(filename: str, text: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".py":
            return "python"
        if suffix == ".json":
            try:
                json.loads(text)
                return "json"
            except json.JSONDecodeError as exc:
                raise AuditError("INVALID_JSON") from exc
        if suffix in {".yaml", ".yml"}:
            return "yaml"
        if suffix in {".md", ".markdown"}:
            return "markdown"
        return "text"

    def _inspect(self, fmt: str, text: str) -> tuple[dict[str, Any], list[str], list[str], list[str], list[str]]:
        architecture: dict[str, Any] = {"format": fmt, "symbols": [], "sections": []}
        interfaces: list[str] = []
        dependencies: list[str] = []
        capabilities: list[str] = []
        risks: list[str] = []

        if fmt == "python":
            try:
                tree = ast.parse(text)
            except SyntaxError as exc:
                raise AuditError("PYTHON_SYNTAX_INVALID") from exc
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    architecture["symbols"].append(node.name)
                    capabilities.append(node.name)
                elif isinstance(node, ast.Import):
                    dependencies.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    dependencies.append(node.module.split(".")[0])
                elif isinstance(node, ast.Call):
                    name = self._call_name(node.func)
                    if name in {"eval", "exec", "compile", "os.system", "subprocess.Popen", "subprocess.run"}:
                        risks.append(f"DANGEROUS_CALL:{name}")
                elif isinstance(node, ast.FunctionDef):
                    interfaces.append(node.name)
            architecture["symbols"] = sorted(set(architecture["symbols"]))
            interfaces.extend(architecture["symbols"])

        elif fmt == "json":
            value = json.loads(text)
            if isinstance(value, Mapping):
                architecture["keys"] = sorted(str(k) for k in value.keys())
                capabilities.extend(str(k) for k in value.keys())
            else:
                architecture["root_type"] = type(value).__name__

        elif fmt == "markdown":
            sections = []
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    heading = stripped.lstrip("#").strip()
                    if heading:
                        sections.append(heading)
            architecture["sections"] = sections
            capabilities.extend(sections)

        lowered = text.lower()
        for marker in ("rm -rf", "curl | sh", "wget | sh", "chmod 777", "disable security", "bypass auth"):
            if marker in lowered:
                risks.append(f"SUSPICIOUS_TEXT:{marker}")

        return architecture, interfaces, dependencies, capabilities, risks

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts: list[str] = []
            current: ast.AST = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    @staticmethod
    def _risk_level(risks: Iterable[str]) -> RiskLevel:
        risks = tuple(risks)
        if any(item.startswith("DANGEROUS_CALL") for item in risks):
            return RiskLevel.HIGH
        if risks:
            return RiskLevel.REVIEW_REQUIRED
        return RiskLevel.LOW

    @staticmethod
    def _requirements(
        architecture: Mapping[str, Any],
        interfaces: Sequence[str],
        dependencies: Sequence[str],
        capabilities: Sequence[str],
        risks: Sequence[str],
    ) -> list[Mapping[str, Any]]:
        requirements: list[Mapping[str, Any]] = []
        if capabilities:
            requirements.append({"kind": "capability", "items": sorted(set(capabilities))})
        if interfaces:
            requirements.append({"kind": "interface", "items": sorted(set(interfaces))})
        if dependencies:
            requirements.append({"kind": "dependency", "items": sorted(set(dependencies))})
        if risks:
            requirements.append({"kind": "risk_gate", "items": sorted(set(risks)), "action": "BLOCK_AND_REVIEW"})
        requirements.append({"kind": "architecture", "value": dict(architecture)})
        return requirements
