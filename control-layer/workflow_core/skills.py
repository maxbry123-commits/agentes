from dataclasses import dataclass


@dataclass(frozen=True)
class SkillRequirement:
    skill_id: str
    required: bool = True
