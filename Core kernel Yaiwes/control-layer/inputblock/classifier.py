"""InputClassifier · CORRECTION | UPDATE | NEW_TASK · 0% LLM.

Reglas deterministas por prefijos / keywords. Protege GOAL_LOCK:
- CORRECTION → misma mission (rebuild input)
- UPDATE → misma mission (patch estado)
- NEW_TASK → nueva mission en cola (no mezcla con la activa)
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class InputKind(str, Enum):
    CORRECTION = "CORRECTION"
    UPDATE = "UPDATE"
    NEW_TASK = "NEW_TASK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ClassifyResult:
    kind: InputKind
    confidence: float  # 0-1 heurística de reglas, no LLM
    same_mission: bool
    reasons: tuple[str, ...]
    normalized_hint: str  # etiqueta corta para logs

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


# Prefijos explícitos (prioridad máxima)
_PREFIX_CORRECTION = re.compile(
    r"^\s*(CORRECTION|CORRECCI[OÓ]N|FIX|HOTFIX|CORR)\s*[:\-]",
    re.I | re.M,
)
_PREFIX_UPDATE = re.compile(
    r"^\s*(UPDATE|ACTUALIZA|PATCH|DELTA)\s*[:\-]",
    re.I | re.M,
)
_PREFIX_NEW = re.compile(
    r"^\s*(NEW[_\s-]?TASK|NUEVA[_\s-]?TAREA|NEW[_\s-]?MISSION|NUEVA[_\s-]?MISI[OÓ]N)\s*[:\-]",
    re.I | re.M,
)

# Keywords de apoyo (si no hay prefijo)
_KW_CORRECTION = re.compile(
    r"\b(corrige|corregir|estaba\s+mal|error\s+en|fix\s+this|wrong|bug)\b",
    re.I,
)
_KW_UPDATE = re.compile(
    r"\b(actualiza|añade\s+a\s+la\s+misión|agrega\s+al\s+plan|modifica\s+el\s+paso|update\s+step)\b",
    re.I,
)
_KW_NEW = re.compile(
    r"\b(nueva\s+tarea|nuevo\s+proyecto|empieza\s+de\s+cero|from\s+scratch|otra\s+misión)\b",
    re.I,
)


def classify(
    content: str,
    *,
    explicit_kind: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> ClassifyResult:
    """Clasifica input. explicit_kind en meta gana si es válido."""
    text = content if isinstance(content, str) else str(content)
    meta = dict(meta or {})
    reasons: list[str] = []

    # 1) explícito por argumento o meta
    raw_ex = explicit_kind or meta.get("kind") or meta.get("input_kind")
    if raw_ex:
        try:
            kind = InputKind(str(raw_ex).strip().upper())
            if kind != InputKind.UNKNOWN:
                return ClassifyResult(
                    kind=kind,
                    confidence=1.0,
                    same_mission=kind != InputKind.NEW_TASK,
                    reasons=("explicit_kind",),
                    normalized_hint=kind.value,
                )
        except ValueError:
            reasons.append("invalid_explicit_kind")

    # 2) prefijos
    if _PREFIX_CORRECTION.search(text):
        return ClassifyResult(
            kind=InputKind.CORRECTION,
            confidence=0.95,
            same_mission=True,
            reasons=("prefix_correction",),
            normalized_hint="CORRECTION",
        )
    if _PREFIX_UPDATE.search(text):
        return ClassifyResult(
            kind=InputKind.UPDATE,
            confidence=0.95,
            same_mission=True,
            reasons=("prefix_update",),
            normalized_hint="UPDATE",
        )
    if _PREFIX_NEW.search(text):
        return ClassifyResult(
            kind=InputKind.NEW_TASK,
            confidence=0.95,
            same_mission=False,
            reasons=("prefix_new_task",),
            normalized_hint="NEW_TASK",
        )

    # 3) keywords
    scores = {
        InputKind.CORRECTION: 1.0 if _KW_CORRECTION.search(text) else 0.0,
        InputKind.UPDATE: 1.0 if _KW_UPDATE.search(text) else 0.0,
        InputKind.NEW_TASK: 1.0 if _KW_NEW.search(text) else 0.0,
    }
    best = max(scores, key=lambda k: scores[k])
    if scores[best] > 0:
        return ClassifyResult(
            kind=best,
            confidence=0.7,
            same_mission=best != InputKind.NEW_TASK,
            reasons=("keyword_" + best.value.lower(),),
            normalized_hint=best.value,
        )

    # 4) default: si hay mission activa en meta → UPDATE suave; si no → NEW_TASK
    if meta.get("active_mission_id"):
        return ClassifyResult(
            kind=InputKind.UPDATE,
            confidence=0.4,
            same_mission=True,
            reasons=("default_with_active_mission",),
            normalized_hint="UPDATE",
        )

    return ClassifyResult(
        kind=InputKind.NEW_TASK,
        confidence=0.4,
        same_mission=False,
        reasons=("default_no_active_mission",),
        normalized_hint="NEW_TASK",
    )


def classify_block_content(
    content: str,
    *,
    mission_id: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> ClassifyResult:
    m = dict(meta or {})
    if mission_id:
        m.setdefault("active_mission_id", mission_id)
    return classify(content, meta=m)
