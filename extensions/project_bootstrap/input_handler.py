# -*- coding: utf-8 -*-
"""
Input Handler — chat / documento → InputBlock → clasificación → tareas
Fuente: PIPELINE 12 FULL §12
A4 — Implementación ejecutable (no stub)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class InputKind(str, Enum):
    CAMBIO = "cambio"
    MEJORA = "mejora"
    CORRECCION = "correccion"
    NUEVO_DOCUMENTO = "nuevo_documento"
    PRIORIDAD = "prioridad"
    OBJETIVO = "objetivo"
    TAREA = "tarea"
    DESCONOCIDO = "desconocido"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class InputBlock:
    """Lectura literal del input. Nunca se interpreta en la construcción."""
    id: str
    raw: str
    kind: InputKind
    priority: Priority
    source: str  # chat | document | system
    timestamp: float
    hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["priority"] = self.priority.value
        return d


@dataclass
class ClassificationResult:
    input_block: InputBlock
    should_pause: bool
    impact_targets: List[str]
    derived_tasks: List[Dict[str, Any]]
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "input_block": self.input_block.to_dict(),
            "should_pause": self.should_pause,
            "impact_targets": self.impact_targets,
            "derived_tasks": self.derived_tasks,
            "notes": self.notes,
        }


def _hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


_PATTERNS = [
    (InputKind.PRIORIDAD, re.compile(r"\b(urgente|prioridad\s*alta|critical|bloquear|pausar)\b", re.I), Priority.CRITICAL),
    (InputKind.CORRECCION, re.compile(r"\b(corregir|fix|bug|error|falla|arreglar)\b", re.I), Priority.HIGH),
    (InputKind.MEJORA, re.compile(r"\b(mejorar|optimizar|refactor|mejorar\s+100|upgrade)\b", re.I), Priority.MEDIUM),
    (InputKind.CAMBIO, re.compile(r"\b(cambiar|modificar|actualizar|reemplazar|update)\b", re.I), Priority.MEDIUM),
    (InputKind.NUEVO_DOCUMENTO, re.compile(r"\b(documento|archivo|\.md|\.yaml|\.json|nuevo\s+doc)\b", re.I), Priority.MEDIUM),
    (InputKind.OBJETIVO, re.compile(r"\b(objetivo|goal|meta|propósito|quiero|necesito)\b", re.I), Priority.HIGH),
    (InputKind.TAREA, re.compile(r"\b(tarea|task|paso|implementar|crear|construir)\b", re.I), Priority.MEDIUM),
]


def classify_raw(raw: str) -> tuple:
    text = (raw or "").strip()
    if not text:
        return InputKind.DESCONOCIDO, Priority.LOW
    for kind, pattern, prio in _PATTERNS:
        if pattern.search(text):
            return kind, prio
    return InputKind.DESCONOCIDO, Priority.LOW


def make_input_block(
    raw: str,
    source: str = "chat",
    force_kind: Optional[InputKind] = None,
    force_priority: Optional[Priority] = None,
) -> InputBlock:
    text = raw if raw is not None else ""
    kind, prio = classify_raw(text)
    if force_kind is not None:
        kind = force_kind
    if force_priority is not None:
        prio = force_priority
    return InputBlock(
        id=str(uuid.uuid4()),
        raw=text,
        kind=kind,
        priority=prio,
        source=source,
        timestamp=time.time(),
        hash=_hash(text),
        metadata={"length": len(text)},
    )


def map_impact(kind: InputKind) -> List[str]:
    mapping = {
        InputKind.OBJETIVO: ["extract_goal", "decompose_tasks", "PROJECT_PROFILE"],
        InputKind.TAREA: ["decompose_tasks", "TASKS"],
        InputKind.CAMBIO: ["build_architecture", "build_workflow", "TRACEABILITY"],
        InputKind.MEJORA: ["build_capabilities", "TRACEABILITY"],
        InputKind.CORRECCION: ["TRACEABILITY", "CHANGELOG"],
        InputKind.NUEVO_DOCUMENTO: ["normalizer", "PROJECT_PROFILE", "TRACEABILITY"],
        InputKind.PRIORIDAD: ["execution_plan", "PENDIENTES"],
        InputKind.DESCONOCIDO: ["TRACEABILITY"],
    }
    return mapping.get(kind, ["TRACEABILITY"])


def derive_tasks(block: InputBlock) -> List[Dict[str, Any]]:
    tasks = []
    base = {
        "status": "PENDING",
        "priority": block.priority.value,
        "source_input_id": block.id,
        "source_hash": block.hash,
    }
    if block.kind == InputKind.OBJETIVO:
        tasks.append({**base, "id": f"G-{block.id[:8]}", "title": f"Procesar objetivo: {block.raw[:80]}", "microflujo": "extract_goal"})
        tasks.append({**base, "id": f"T-{block.id[:8]}", "title": "Descomponer en tareas", "microflujo": "decompose_tasks"})
    elif block.kind == InputKind.NUEVO_DOCUMENTO:
        tasks.append({**base, "id": f"N-{block.id[:8]}", "title": "Normalizar documento nuevo", "microflujo": "normalizer"})
    elif block.kind == InputKind.PRIORIDAD:
        tasks.append({**base, "id": f"P-{block.id[:8]}", "title": "Reordenar por prioridad alta", "microflujo": "plan_and_select"})
    else:
        tasks.append({**base, "id": f"X-{block.id[:8]}", "title": f"Procesar {block.kind.value}: {block.raw[:60]}", "microflujo": "append_trace"})
    return tasks


def handle_input(
    raw: str,
    source: str = "chat",
    current_running: bool = False,
) -> ClassificationResult:
    block = make_input_block(raw, source=source)
    impact = map_impact(block.kind)
    should_pause = (
        current_running
        and block.priority in (Priority.CRITICAL, Priority.HIGH)
        and block.kind in (InputKind.PRIORIDAD, InputKind.CORRECCION, InputKind.OBJETIVO)
    )
    tasks = derive_tasks(block)
    notes = "PAUSAR proceso actual — prioridad alta detectada" if should_pause else ""
    return ClassificationResult(
        input_block=block,
        should_pause=should_pause,
        impact_targets=impact,
        derived_tasks=tasks,
        notes=notes,
    )


if __name__ == "__main__":
    samples = [
        "Necesito crear un sistema de login OAuth2",
        "Urgente: corregir el bug de autenticación",
        "Mejorar el pipeline de documentos 100 veces",
        "Aquí va un nuevo documento de arquitectura.md",
        "texto sin clasificar claro",
    ]
    for s in samples:
        r = handle_input(s, current_running=True)
        print("---")
        print("RAW:", s[:50])
        print("KIND:", r.input_block.kind.value, "PRIO:", r.input_block.priority.value)
        print("PAUSE:", r.should_pause, "IMPACT:", r.impact_targets)
        print("TASKS:", [t["id"] for t in r.derived_tasks])
