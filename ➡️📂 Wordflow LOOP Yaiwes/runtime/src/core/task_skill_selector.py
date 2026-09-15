"""Deterministic task-to-skill selector for YAIWES.

This module does not download or execute skills. It ranks only an already verified
catalog and fails closed when a task cannot be covered by at least three relevant
skills. Acquisition and execution remain separate Sheriff-controlled steps.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping, Sequence, Any

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{1,63}")
_ALLOWED_PROFILES = {"backend", "frontend", "general"}


class SkillSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class SkillRecord:
    name: str
    version: str
    origin: str
    path: str
    tags: tuple[str, ...]
    verified: bool = False
    enabled: bool = True
    sha256: str = ""


@dataclass(frozen=True)
class SkillSelection:
    task_id: str
    profile: str
    selected: tuple[SkillRecord, ...]
    scores: tuple[tuple[str, int], ...]
    min_skills: int
    max_skills: int
    passed: bool
    reason: str


def _tokens(value: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN.finditer(value or "")}


def _coerce_record(value: SkillRecord | Mapping[str, Any]) -> SkillRecord:
    if isinstance(value, SkillRecord):
        return value
    if not isinstance(value, Mapping):
        raise SkillSelectionError("SKILL_RECORD_MAPPING_REQUIRED")
    tags = value.get("tags", ())
    if not isinstance(tags, Sequence) or isinstance(tags, (str, bytes)):
        raise SkillSelectionError("SKILL_TAGS_LIST_REQUIRED")
    record = SkillRecord(
        name=str(value.get("name", "")).strip(),
        version=str(value.get("version", "")).strip(),
        origin=str(value.get("origin", "")).strip(),
        path=str(value.get("path", "")).strip(),
        tags=tuple(str(x).strip().lower() for x in tags if str(x).strip()),
        verified=value.get("verified") is True,
        enabled=value.get("enabled", True) is True,
        sha256=str(value.get("sha256", "")).strip().lower(),
    )
    if not record.name or not record.version or not record.origin or not record.path:
        raise SkillSelectionError("SKILL_RECORD_INCOMPLETE")
    return record


def select_skills(
    *,
    task_id: str,
    task: str,
    profile: str,
    catalog: Iterable[SkillRecord | Mapping[str, Any]],
    min_skills: int = 3,
    max_skills: int = 5,
) -> SkillSelection:
    task_id = task_id.strip()
    task = task.strip()
    profile = profile.strip().lower()
    if not task_id or not task:
        raise SkillSelectionError("TASK_ID_AND_TEXT_REQUIRED")
    if profile not in _ALLOWED_PROFILES:
        raise SkillSelectionError("UNKNOWN_PROFILE")
    if not (1 <= min_skills <= max_skills <= 5):
        raise SkillSelectionError("SKILL_COUNT_RANGE_INVALID")

    task_tokens = _tokens(task) | {profile}
    ranked: list[tuple[int, SkillRecord]] = []
    seen: set[str] = set()
    for raw in catalog:
        record = _coerce_record(raw)
        key = record.name.lower()
        if key in seen:
            raise SkillSelectionError("DUPLICATE_SKILL_NAME")
        seen.add(key)
        if not record.enabled or not record.verified:
            continue
        skill_tokens = _tokens(record.name) | _tokens(" ".join(record.tags))
        overlap = task_tokens & skill_tokens
        if not overlap:
            continue
        score = len(overlap) * 10
        if profile in skill_tokens:
            score += 5
        score += sum(2 for tag in record.tags if tag in task_tokens)
        ranked.append((score, record))

    ranked.sort(key=lambda item: (-item[0], item[1].name.lower(), item[1].version))
    selected = tuple(record for _, record in ranked[:max_skills])
    scores = tuple((record.name, score) for score, record in ranked[:max_skills])
    if len(selected) < min_skills:
        return SkillSelection(
            task_id=task_id,
            profile=profile,
            selected=selected,
            scores=scores,
            min_skills=min_skills,
            max_skills=max_skills,
            passed=False,
            reason=f"INSUFFICIENT_RELEVANT_VERIFIED_SKILLS:{len(selected)}<{min_skills}",
        )
    return SkillSelection(
        task_id=task_id,
        profile=profile,
        selected=selected,
        scores=scores,
        min_skills=min_skills,
        max_skills=max_skills,
        passed=True,
        reason="PASS_RELEVANT_VERIFIED_SKILLS",
    )
