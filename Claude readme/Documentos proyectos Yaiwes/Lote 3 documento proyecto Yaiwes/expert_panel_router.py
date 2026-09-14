"""
expert_panel_router.py
-----------------------
Parte DETERMINISTA del kernel (0% LLM aquí).
Responsabilidad única: dado un texto de tarea, decidir CUÁLES módulos de
razonamiento (archivos .yaml en reasoning_modules/) aplican, sin ejecutar
ninguno todavía. No contiene el texto de los módulos como código — solo
los lee de disco.

Nota de nombre de archivo: el nombre original "expert-panel-router.py"
(con guiones) NO es importable en Python. Este archivo usa guion bajo
a propósito para poder hacer `from expert_panel_router import ...`
sin que el import se rompa (el mismo error que encontramos en la
auditoría forense de kernel-principal).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

try:
    import yaml  # PyYAML
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Falta PyYAML. Instala con: pip install pyyaml"
    ) from exc


DEFAULT_BANK_PATH = Path("reasoning_kernel/decision_on_demand/reasoning_modules")


@dataclass(frozen=True)
class ModuloRazonamiento:
    artifact_id: str
    descripcion: str
    fase_uso: str
    max_tokens: int
    ruta: Path


def cargar_banco(bank_path: Path = DEFAULT_BANK_PATH) -> list[ModuloRazonamiento]:
    """Lee TODOS los .yaml de la carpeta. Añadir un módulo nuevo = agregar
    un archivo aquí. Esta función no cambia cuando el banco crece."""
    modulos: list[ModuloRazonamiento] = []
    if not bank_path.exists():
        return modulos

    for archivo in sorted(bank_path.glob("*.yaml")):
        try:
            ficha = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # ficha corrupta: se ignora, no rompe el resto del banco

        cog = (ficha or {}).get("cognicion", {})
        if not cog.get("descripcion") or not ficha.get("artifact_id"):
            continue  # no pasa el mínimo del schema v2.0: se descarta

        modulos.append(
            ModuloRazonamiento(
                artifact_id=ficha["artifact_id"],
                descripcion=cog["descripcion"],
                fase_uso=cog.get("fase_uso", "implement"),
                max_tokens=cog.get("presupuesto", {}).get("max_tokens", 400),
                ruta=archivo,
            )
        )
    return modulos


def _score_heuristico(tarea: str, modulo: ModuloRazonamiento) -> float:
    """SELECT por defecto: solapamiento de palabras clave (barato, 0% LLM).
    Se puede sustituir por un ranker basado en embeddings o en LLM sin
    tocar el resto del router — ver `select_modulos(ranker=...)`.
    """
    palabras_tarea = set(re.findall(r"\w+", tarea.lower()))
    palabras_modulo = set(re.findall(r"\w+", modulo.descripcion.lower()))
    if not palabras_tarea or not palabras_modulo:
        return 0.0
    interseccion = palabras_tarea & palabras_modulo
    return len(interseccion) / len(palabras_modulo)


RankerFn = Callable[[str, list[ModuloRazonamiento]], list[tuple[ModuloRazonamiento, float]]]


def _ranker_por_defecto(
    tarea: str, modulos: list[ModuloRazonamiento]
) -> list[tuple[ModuloRazonamiento, float]]:
    return sorted(
        ((m, _score_heuristico(tarea, m)) for m in modulos),
        key=lambda par: par[1],
        reverse=True,
    )


def select_modulos(
    tarea: str,
    bank_path: Path = DEFAULT_BANK_PATH,
    top_k: int = 6,
    ranker: Optional[RankerFn] = None,
) -> list[ModuloRazonamiento]:
    """Paso SELECT. Determinista por defecto (heurística de palabras).
    Si más adelante quieres que el SELECT lo haga un LLM o un modelo de
    embeddings, pasa tu propia función en `ranker=` — el resto del kernel
    no se entera del cambio.
    """
    modulos = cargar_banco(bank_path)
    if not modulos:
        return []
    ranking = (ranker or _ranker_por_defecto)(tarea, modulos)
    return [m for m, score in ranking[:top_k] if score > 0] or [
        m for m, _ in ranking[:top_k]
    ]
