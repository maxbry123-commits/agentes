from __future__ import annotations
from dataclasses import dataclass, field
from schemas.base import new_id


@dataclass(slots=True)
class CodePatch:
    patch_id: str = field(default_factory=lambda: new_id("patch"))
    experiment_id: str = ""
    task_id: str = ""
    attempt: int = 0
    mode: str = "copy"
    work_dir: str = ""
    changed_files: list[dict] = field(default_factory=list)
    backup_paths: dict[str, str] = field(default_factory=dict)
    diff_summary: str = ""
    status: str = "pending"
    reason: str = ""
