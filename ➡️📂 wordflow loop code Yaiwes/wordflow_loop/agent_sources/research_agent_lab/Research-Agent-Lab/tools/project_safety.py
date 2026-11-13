from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch

from schemas.topic_pack import TopicPack


@dataclass(slots=True)
class ProjectSafetyPolicy:
    repo_path: str
    allowed_paths: list[str] = field(default_factory=list)
    protected_paths: list[str] = field(default_factory=list)
    backup_required: bool = True
    dry_run_first: bool = True
    max_files_per_patch: int = 8

    @classmethod
    def from_topic(cls, topic: TopicPack) -> "ProjectSafetyPolicy":
        codebase = topic.codebase
        return cls(
            repo_path=str(codebase.get("repo_path", "")),
            allowed_paths=topic.allowed_auto_edit(),
            protected_paths=topic.protected_files(),
            backup_required=bool(codebase.get("backup_required", True)),
            dry_run_first=bool(codebase.get("dry_run_first", True)),
            max_files_per_patch=int(codebase.get("max_files_per_patch", 8)),
        )

    def is_protected(self, relative_path: str) -> bool:
        normalized = self._normalize(relative_path)
        return any(fnmatch.fnmatch(normalized, self._normalize(pattern)) for pattern in self.protected_paths)

    def is_allowed(self, relative_path: str) -> bool:
        normalized = self._normalize(relative_path)
        return any(fnmatch.fnmatch(normalized, self._normalize(pattern)) for pattern in self.allowed_paths)

    def validate_planned_paths(self, paths: list[str]) -> list[str]:
        problems: list[str] = []
        if len(paths) > self.max_files_per_patch:
            problems.append(
                f"planned patch touches {len(paths)} files; limit is {self.max_files_per_patch}"
            )
        for path in paths:
            if self.is_protected(path):
                problems.append(f"protected path cannot be edited: {path}")
            elif not self.is_allowed(path):
                problems.append(f"path is outside allowed edit scope: {path}")
        return problems

    def resolve_repo_path(self) -> Path:
        if not self.repo_path:
            raise ValueError("repo_path is not configured")
        return Path(self.repo_path).resolve()

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "allowed_paths": self.allowed_paths,
            "protected_paths": self.protected_paths,
            "backup_required": self.backup_required,
            "dry_run_first": self.dry_run_first,
            "max_files_per_patch": self.max_files_per_patch,
        }

    def _normalize(self, path: str) -> str:
        p = path.replace("\\", "/")
        if p.endswith("/"):
            p = p.rstrip("/") + "/*"
        return p.lstrip("/")
