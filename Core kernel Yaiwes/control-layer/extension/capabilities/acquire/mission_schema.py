"""OpenClaw AcquireMission + SOURCE_SCHEMA (deterministic pin contract).

Implements guide §1–§2. Does not execute network or mutation.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_REFS = frozenset({"main", "latest", "head", "master", "develop"})
OFFICIAL_REPO = "https://github.com/openclaw/openclaw.git"

SCHEMA_VERSION = "1.0.0-openclaw-source"


@dataclass
class SourceSpec:
    repository: str
    ref: str
    commit: str
    method: Literal["git-source"] = "git-source"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InstallSpec:
    method: Literal["git-source"] = "git-source"
    checkout_dir: str = "agents/OpenClaw/source/checkout"
    build_ui: bool = True
    install_wrapper: bool = True
    onboard: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicySpec:
    allow_network: bool = True
    allow_build: bool = True
    allow_install: bool = True
    allow_overwrite: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AcquireMission:
    mission_id: str
    agent: str
    source: SourceSpec
    install: InstallSpec = field(default_factory=InstallSpec)
    policy: PolicySpec = field(default_factory=PolicySpec)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "agent": self.agent,
            "source": self.source.to_dict(),
            "install": self.install.to_dict(),
            "policy": self.policy.to_dict(),
            "schema_version": self.schema_version,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "AcquireMission":
        src = d.get("source") or {}
        inst = d.get("install") or {}
        pol = d.get("policy") or {}
        return AcquireMission(
            mission_id=str(d["mission_id"]),
            agent=str(d.get("agent") or "OpenClaw"),
            source=SourceSpec(
                repository=str(src.get("repository") or ""),
                ref=str(src.get("ref") or ""),
                commit=str(src.get("commit") or "").lower(),
                method=src.get("method") or "git-source",  # type: ignore[arg-type]
            ),
            install=InstallSpec(
                method=inst.get("method") or "git-source",  # type: ignore[arg-type]
                checkout_dir=str(
                    inst.get("checkout_dir") or "agents/OpenClaw/source/checkout"
                ),
                build_ui=bool(inst.get("build_ui", True)),
                install_wrapper=bool(inst.get("install_wrapper", True)),
                onboard=bool(inst.get("onboard", False)),
            ),
            policy=PolicySpec(
                allow_network=bool(pol.get("allow_network", True)),
                allow_build=bool(pol.get("allow_build", True)),
                allow_install=bool(pol.get("allow_install", True)),
                allow_overwrite=bool(pol.get("allow_overwrite", False)),
            ),
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]

    @property
    def status(self) -> str:
        return "VALID" if self.ok else "INVALID"


def validate_source_schema(source: SourceSpec | dict[str, Any]) -> ValidationResult:
    """SOURCE_SCHEMA validation — guide §2."""
    if isinstance(source, dict):
        source = SourceSpec(
            repository=str(source.get("repository") or ""),
            ref=str(source.get("ref") or ""),
            commit=str(source.get("commit") or "").lower(),
            method=source.get("method") or "git-source",  # type: ignore[arg-type]
        )
    errors: list[str] = []
    repo = source.repository.rstrip("/")
    if repo != OFFICIAL_REPO.rstrip("/"):
        errors.append("REPOSITORY_NOT_OFFICIAL")
    ref_l = source.ref.strip().lower()
    if ref_l in FORBIDDEN_REFS:
        errors.append("FORBIDDEN_REF")
    if not COMMIT_RE.fullmatch(source.commit.strip().lower()):
        errors.append("INVALID_COMMIT_HEX40")
    if source.method != "git-source":
        errors.append("METHOD_NOT_GIT_SOURCE")
    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_mission(mission: AcquireMission | dict[str, Any]) -> ValidationResult:
    if isinstance(mission, dict):
        mission = AcquireMission.from_dict(mission)
    errors: list[str] = []
    if not mission.mission_id:
        errors.append("MISSING_MISSION_ID")
    if mission.agent != "OpenClaw":
        errors.append("AGENT_NOT_OPENCLAW")
    src = validate_source_schema(mission.source)
    errors.extend(src.errors)
    if not mission.install.checkout_dir.startswith("agents/OpenClaw/"):
        errors.append("CHECKOUT_DIR_OUTSIDE_ROOT")
    if mission.install.method != "git-source":
        errors.append("INSTALL_METHOD_NOT_GIT_SOURCE")
    return ValidationResult(ok=not errors, errors=tuple(errors))


# Canonical pinned mission (guide pin)
CANONICAL_OPENCLAW_MISSION = AcquireMission(
    mission_id="openclaw-source-build-0790d9f5",
    agent="OpenClaw",
    source=SourceSpec(
        repository=OFFICIAL_REPO,
        ref="v2026.7.1-2",
        commit="0790d9f593ad30c940ed93b5872a8cf6d6f3cf8c",
        method="git-source",
    ),
    install=InstallSpec(
        method="git-source",
        checkout_dir="agents/OpenClaw/source/checkout",
        build_ui=True,
        install_wrapper=True,
        onboard=False,
    ),
    policy=PolicySpec(
        allow_network=True,
        allow_build=True,
        allow_install=True,
        allow_overwrite=False,
    ),
)
