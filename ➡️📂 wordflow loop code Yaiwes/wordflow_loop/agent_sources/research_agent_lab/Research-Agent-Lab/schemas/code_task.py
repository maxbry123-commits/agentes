from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class CodeTask:
    title: str
    task_id: str = field(default_factory=lambda: new_id("codetask"))
    experiment_id: str = ""
    repository_path: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    protected_paths: list[str] = field(default_factory=list)
    proposed_files: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
    dry_run_first: bool = True
    backup_required: bool = True
    safety_policy: dict[str, object] = field(default_factory=dict)
