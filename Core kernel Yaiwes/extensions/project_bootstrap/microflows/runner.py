# -*- coding: utf-8 -*-
"""
Micro-flujos deterministas de plantillas de documentos.
Fuente: PIPELINE 12 FULL §13
A3 — Implementación ejecutable (no stub)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class GoalStruct:
    objective: str
    success_criteria: str
    failure_criteria: str
    verb: str
    hash: str
    timestamp: float
    emoji: str = "🎯"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TaskItem:
    id: str
    title: str
    status: str  # PENDING | RUNNING | DONE
    priority: str  # CRITICAL | HIGH | MEDIUM | LOW
    depends_on: List[str] = field(default_factory=list)
    parent_goal_hash: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def _hash(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


# ---------- extract_goal ----------

_ACTION_VERBS = {
    "crear", "construir", "implementar", "modificar", "analizar", "instalar",
    "configurar", "desplegar", "validar", "reparar", "auditar", "documentar",
    "integrar", "migrar", "actualizar", "eliminar", "probar", "ejecutar",
    "diseñar", "definir", "extraer", "generar", "registrar", "publicar",
}


def extract_goal(raw_input: str, **kwargs) -> GoalStruct:
    """
    PASO 1-5 extract_goal (determinista).
    Extrae meta, verbo, criterios. Formato: [Verbo] + [Objeto] + [Restricción]
    """
    text = (raw_input or "").strip()
    if not text:
        raise ValueError("extract_goal: input vacío")

    lower = text.lower()
    verb = "procesar"
    tokens = re.findall(r"[a-záéíóúñü]+", lower)
    for v in sorted(_ACTION_VERBS, key=len, reverse=True):
        if v in tokens:
            verb = v
            break

    # Criterios por defecto si no se detectan
    success = "objetivo cumplido con evidencia"
    failure = "no completar en el número de iteraciones permitido"
    if "éxito" in lower or "success" in lower:
        m = re.search(r"(?:éxito|success)[:\s]+(.+?)(?:\.|$)", text, re.I)
        if m:
            success = m.group(1).strip()
    if "fallo" in lower or "failure" in lower:
        m = re.search(r"(?:fallo|failure)[:\s]+(.+?)(?:\.|$)", text, re.I)
        if m:
            failure = m.group(1).strip()

    objective = f"{verb.capitalize()} — {text[:120]}"
    h = _hash({"objective": objective, "verb": verb, "ts": time.time()})
    return GoalStruct(
        objective=objective,
        success_criteria=success,
        failure_criteria=failure,
        verb=verb,
        hash=h,
        timestamp=time.time(),
    )


# ---------- decompose_tasks ----------

def decompose_tasks(goal: GoalStruct, max_steps: int = 8, **kwargs) -> List[TaskItem]:
    """
    Descompone goal en pasos atómicos.
    Prioridad y dependencias lineales por defecto.
    """
    if not goal or not goal.objective:
        raise ValueError("decompose_tasks: goal vacío")

    # Heurística simple: dividir por puntuación / "y" / comas
    parts = re.split(r"[.;]|\by\b|,", goal.objective)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]
    if not parts:
        parts = [goal.objective]

    parts = parts[:max_steps]
    tasks: List[TaskItem] = []
    prev_id = None
    priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    for i, part in enumerate(parts):
        tid = f"T{i+1:03d}"
        tasks.append(TaskItem(
            id=tid,
            title=part[:100],
            status="PENDING",
            priority=priorities[min(i, len(priorities) - 1)],
            depends_on=[prev_id] if prev_id else [],
            parent_goal_hash=goal.hash,
        ))
        prev_id = tid
    return tasks


# ---------- build_profile (simplificado ejecutable) ----------

def build_profile(raw_docs: str = "", goal: Optional[GoalStruct] = None, **kwargs) -> Dict[str, Any]:
    """Genera estructura de PROJECT_PROFILE.md."""
    purpose = goal.objective if goal else "proyecto sin objetivo declarado"
    return {
        "document": "PROJECT_PROFILE.md",
        "proposito": purpose,
        "alcance": kwargs.get("alcance", "por definir"),
        "entradas": kwargs.get("entradas", ["input_block"]),
        "salidas": kwargs.get("salidas", ["project_model"]),
        "restricciones": kwargs.get("restricciones", []),
        "hash": _hash({"proposito": purpose}),
        "timestamp": time.time(),
    }


def build_architecture(components: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    """Genera estructura de ARCHITECTURE.md."""
    comps = components or ["controllers", "services", "repositories", "models"]
    return {
        "document": "ARCHITECTURE.md",
        "capas": comps,
        "mermaid": "graph LR\n  Controller --> Service --> Repository --> Model",
        "hash": _hash({"capas": comps}),
        "timestamp": time.time(),
    }


def build_workflow(fases: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    """Genera estructura de WORKFLOW.md."""
    fases = fases or ["analisis", "implementacion", "test", "deploy"]
    workflow = {
        "fases": {
            f: {"entrada": "prev", "salida": "next", "herramientas": []}
            for f in fases
        }
    }
    return {
        "document": "WORKFLOW.md",
        "workflow": workflow,
        "hash": _hash(workflow),
        "timestamp": time.time(),
    }


def build_pipeline(**kwargs) -> Dict[str, Any]:
    return {
        "document": "PIPELINE.md",
        "pipelines": kwargs.get("pipelines", {}),
        "hash": _hash(kwargs.get("pipelines", {})),
        "timestamp": time.time(),
    }


def build_capabilities(exports: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    caps = []
    for name in (exports or []):
        caps.append({
            "capability_id": name,
            "inputs": {},
            "outputs": {},
            "entrypoint": name,
        })
    return {
        "document": "CAPABILITIES.md",
        "capabilities": caps,
        "hash": _hash(caps),
        "timestamp": time.time(),
    }


def append_trace(decision: str, reason: str = "", source: str = "", commit: str = "", **kwargs) -> Dict[str, Any]:
    entry = {
        "timestamp": time.time(),
        "decision": decision,
        "reason": reason,
        "source": source,
        "commit": commit,
    }
    return {
        "document": "TRACEABILITY.md",
        "entry": entry,
        "hash": _hash(entry),
    }


# Registry de microflujos
MICROFLUJOS: Dict[str, Callable] = {
    "extract_goal": extract_goal,
    "decompose_tasks": decompose_tasks,
    "build_profile": build_profile,
    "build_architecture": build_architecture,
    "build_workflow": build_workflow,
    "build_pipeline": build_pipeline,
    "build_capabilities": build_capabilities,
    "append_trace": append_trace,
}


def run_microflujo(name: str, **kwargs) -> Any:
    if name not in MICROFLUJOS:
        raise KeyError(f"Microflujo desconocido: {name}. Disponibles: {list(MICROFLUJOS)}")
    return MICROFLUJOS[name](**kwargs)


if __name__ == "__main__":
    g = extract_goal("Crear un sistema de autenticación OAuth2 con Google y GitHub")
    print("GOAL:", g.to_dict())
    tasks = decompose_tasks(g)
    print("TASKS:", [t.to_dict() for t in tasks])
    print("PROFILE:", build_profile(goal=g))
    print("OK — microflows loaded:", list(MICROFLUJOS.keys()))
