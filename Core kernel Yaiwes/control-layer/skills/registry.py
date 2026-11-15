"""W09 · Skill Registry + Resolver · block si skill obligatoria falta."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


class SkillMissingError(Exception):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__("skills_missing:" + ",".join(missing))


@dataclass
class SkillManifest:
    id: str
    name: str
    version: str = "1.0.0"
    required: bool = False
    tags: list[str] = field(default_factory=list)
    path: str = ""
    validated: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SkillRegistry:
    def __init__(self) -> None:
        self._by_id: Dict[str, SkillManifest] = {}

    def register(self, skill: SkillManifest | dict) -> SkillManifest:
        s = skill if isinstance(skill, SkillManifest) else SkillManifest(
            id=str(skill["id"]),
            name=str(skill.get("name") or skill["id"]),
            version=str(skill.get("version") or "1.0.0"),
            required=bool(skill.get("required", False)),
            tags=list(skill.get("tags") or []),
            path=str(skill.get("path") or ""),
            validated=bool(skill.get("validated", False)),
            meta=dict(skill.get("meta") or {}),
        )
        self._by_id[s.id] = s
        return s

    def get(self, skill_id: str) -> SkillManifest | None:
        return self._by_id.get(skill_id)

    def resolve_required(self, required_ids: list[str]) -> list[SkillManifest]:
        missing = [sid for sid in required_ids if sid not in self._by_id or not self._by_id[sid].validated]
        if missing:
            raise SkillMissingError(missing)
        return [self._by_id[sid] for sid in required_ids]

    def list_all(self) -> list[SkillManifest]:
        return list(self._by_id.values())
