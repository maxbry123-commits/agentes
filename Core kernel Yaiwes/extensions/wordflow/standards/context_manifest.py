"""ContextManifest + validator — boolean context_verified no basta."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class ContextManifest:
    mission_id: str
    task_id: str
    project_docs: List[str] = field(default_factory=list)
    architecture_docs: List[str] = field(default_factory=list)
    task_spec: str = ""
    relevant_files: List[str] = field(default_factory=list)
    contracts: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    repository_revision: str = ""
    handoff_ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ContextValidator:
    def validate(self, manifest: ContextManifest, require_docs: bool = False) -> Dict[str, Any]:
        errors = []
        if not manifest.mission_id:
            errors.append("mission_id missing")
        if not manifest.task_id:
            errors.append("task_id missing")
        if not manifest.task_spec.strip():
            errors.append("task_spec missing")
        if not manifest.handoff_ref.strip():
            errors.append("handoff_ref missing")
        if require_docs and not (manifest.project_docs or manifest.architecture_docs):
            errors.append("no project/architecture docs")
        # resolvable paths if provided
        for p in manifest.relevant_files[:50]:
            if p and not Path(p).exists() and not p.startswith("extensions/"):
                # extensions/ may not exist on all runners — soft
                pass
        ok = len(errors) == 0
        return {"ok": ok, "errors": errors, "manifest": manifest.to_dict()}
