from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class CodeFileSummary:
    path: str
    role: str = ""
    imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    config_keys: list[str] = field(default_factory=list)
    important_patterns: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CodebaseReport:
    repository_path: str
    report_id: str = field(default_factory=lambda: new_id("codebase"))
    files: list[CodeFileSummary] = field(default_factory=list)
    project_notes: str = ""
    integration_points: list[str] = field(default_factory=list)
    suggested_first_patch_files: list[str] = field(default_factory=list)
    smoke_commands: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
