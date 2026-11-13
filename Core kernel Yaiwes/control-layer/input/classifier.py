"""W05 · Hot-input classifier CORRECTION | UPDATE | NEW_TASK."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class InputKind(str, Enum):
    CORRECTION = "CORRECTION"
    UPDATE = "UPDATE"
    NEW_TASK = "NEW_TASK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ClassifiedInput:
    kind: InputKind
    confidence: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


_CORRECTION = re.compile(r"\b(correg|fix|error|bug|wrong|incorrecto)\w*", re.I)
_UPDATE = re.compile(r"\b(agrega|añade|update|actualiza|también|además)\w*", re.I)
_NEW = re.compile(r"\b(nuevo proyecto|otra tarea|new task|ahora analiza|cambia de tema)\w*", re.I)


def classify_hot_input(text: str) -> ClassifiedInput:
    t = (text or "").strip()
    if not t:
        return ClassifiedInput(InputKind.UNKNOWN, 0.0, ("empty",))
    if _NEW.search(t):
        return ClassifiedInput(InputKind.NEW_TASK, 0.9, ("keyword_new",))
    if _CORRECTION.search(t):
        return ClassifiedInput(InputKind.CORRECTION, 0.85, ("keyword_correction",))
    if _UPDATE.search(t):
        return ClassifiedInput(InputKind.UPDATE, 0.8, ("keyword_update",))
    # default: update context of current mission
    return ClassifiedInput(InputKind.UPDATE, 0.5, ("default_update",))
