"""MC07 · MemoryClassifier · no guardar todo · reglas deterministas."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class MemoryClass(str, Enum):
    DISCARD = "discard"
    TEMPORARY = "temporary"  # L0
    FACT = "fact"  # L1
    EXPERIENCE = "experience"  # L2
    KNOWLEDGE = "knowledge"  # L3
    PROCEDURE = "procedure"  # L4


@dataclass(frozen=True)
class ClassifyMemoryResult:
    klass: MemoryClass
    store: bool
    reasons: tuple[str, ...]


_NOISE = re.compile(
    r"^(ok|vale|gracias|hola|\.+|test)$",
    re.I,
)
_PROC = re.compile(r"\b(pasos?|procedure|receta|when:|steps?:|validat)\b", re.I)
_FACT = re.compile(r"\b(decidimos|es obligatorio|usamos|arquitectura|convenio)\b", re.I)
_EXP = re.compile(r"\b(error|fall[oó]|timeout|soluci[oó]n|fixeamos)\b", re.I)
_KNOW = re.compile(r"\b(concepto|regla|relaci[oó]n|definici[oó]n)\b", re.I)


def classify_memory(content: str, *, explicit: str | None = None) -> ClassifyMemoryResult:
    text = (content or "").strip()
    if not text or _NOISE.match(text):
        return ClassifyMemoryResult(MemoryClass.DISCARD, False, ("noise_or_empty",))

    if explicit:
        try:
            k = MemoryClass(explicit.lower())
            return ClassifyMemoryResult(k, k != MemoryClass.DISCARD, ("explicit",))
        except ValueError:
            pass

    if _PROC.search(text):
        return ClassifyMemoryResult(MemoryClass.PROCEDURE, True, ("keyword_procedure",))
    if _FACT.search(text):
        return ClassifyMemoryResult(MemoryClass.FACT, True, ("keyword_fact",))
    if _EXP.search(text):
        return ClassifyMemoryResult(MemoryClass.EXPERIENCE, True, ("keyword_experience",))
    if _KNOW.search(text):
        return ClassifyMemoryResult(MemoryClass.KNOWLEDGE, True, ("keyword_knowledge",))

    if len(text) < 20:
        return ClassifyMemoryResult(MemoryClass.TEMPORARY, True, ("short_temp",))

    return ClassifyMemoryResult(MemoryClass.TEMPORARY, True, ("default_temp",))
