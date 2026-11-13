"""Dispatcher táctico de Comand Center para activar el ejecutor SEALS existente.

Flujo autorizado:
    inventario -> PENDING_STEP1 -> límites -> seals_core/ejecutor.py::ejecutar_tarea

Este módulo no implementa un ejecutor alternativo, no modifica seals_core y no
contiene credenciales.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

from idempotencia import (
    STATE_PATH,
    contar_disparos_ultima_hora,
    registrar_disparo,
    registrar_sha_procesado,
    sha_ya_procesado,
)

SCHEMA = "comand-center.trigger-engine/v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "Core kernel Yaiwes" / "CORE-KERNEL-COMPONENT-INVENTORY.json"
CONFIG_PATH = Path(__file__).with_name("config_disparo.json")
SEALS_CORE_DIR = REPO_ROOT / "Seals team YAIWES" / "seals_core"
EJECUTOR_PATH = SEALS_CORE_DIR / "ejecutor.py"
LLAMADAS_LLM_ESTIMADAS_POR_STEP1 = 1

Ejecutor = Callable[[dict[str, Any]], dict[str, Any]]


def cargar_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    requeridos = {
        "max_disparos_por_hora": 20,
        "requiere_sha_no_procesado": True,
        "presupuesto_maximo_llamadas_llm_por_ciclo": 200,
        "si_limite_excedido": "PAUSAR_Y_REGISTRAR_GAP_NO_DETENER_PROYECTO",
    }
    if config != requeridos:
        raise ValueError("CONFIG_DISPARO_NO_COINCIDE_CON_CONTRATO_FIJO")
    return config


def cargar_inventario(inventory_path: Path = INVENTORY_PATH) -> dict[str, Any]:
    inventario = json.loads(inventory_path.read_text(encoding="utf-8"))
    componentes = inventario.get("components")
    if not isinstance(componentes, list):
        raise ValueError("INVENTARIO_SIN_COMPONENTS")
    return inventario


def nodos_pending_step1(inventario: dict[str, Any]) -> list[dict[str, Any]]:
    """Devuelve únicamente nodos del inventario que siguen en PENDING_STEP1."""
    return [
        nodo
        for nodo in inventario["components"]
        if isinstance(nodo, dict) and nodo.get("wall_status") == "PENDING_STEP1"
    ]


def cargar_ejecutor_existente() -> Ejecutor:
    """Carga exactamente seals_core/ejecutor.py sin modificarlo ni copiarlo."""
    if not EJECUTOR_PATH.is_file():
        raise FileNotFoundError(f"EJECUTOR_NO_ENCONTRADO:{EJECUTOR_PATH}")
    seals_path = str(SEALS_CORE_DIR)
    if seals_path not in sys.path:
        sys.path.insert(0, seals_path)
    spec = importlib.util.spec_from_file_location("yaiwes_seals_ejecutor", EJECUTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("NO_SE_PUDO_CARGAR_SPEC_EJECUTOR")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    ejecutar = getattr(modulo, "ejecutar_tarea", None)
    if not callable(ejecutar):
        raise RuntimeError("EJECUTOR_SIN_FUNCION_EJECUTAR_TAREA")
    return ejecutar


def tarea_desde_nodo(nodo: dict[str, Any]) -> dict[str, Any]:
    """Adapta un registro PENDING_STEP1 al contrato ya existente de ejecutar_tarea."""
    nombre = str(nodo.get("name") or nodo.get("component_id") or "").strip()
    if not nombre:
        raise ValueError("NODO_PENDING_STEP1_SIN_NOMBRE")
    path = str(nodo.get("path") or "").strip()
    wall_node_id = nodo.get("wall_node_id")
    descripcion = (
        f"STEP1 del componente inventariado {nombre}. "
        f"wall_node_id={wall_node_id}; path={path}; "
        f"function_source={nodo.get('function_source')}; "
        "evaluar el componente sin decidir arquitectura ni modificar el inventario."
    )
    return {
        "tipo": "evaluar_componente",
        "nombre": nombre,
        "url": path,
        "descripcion": descripcion,
    }


def ejecutar_ciclo(
    commit_sha: str,
    *,
    ejecutor: Ejecutor | None = None,
    inventory_path: Path = INVENTORY_PATH,
    config_path: Path = CONFIG_PATH,
    state_path: Path = STATE_PATH,
) -> dict[str, Any]:
    """Ejecuta un ciclo acotado de disparos para un único commit SHA."""
    sha = commit_sha.strip()
    if not sha:
        raise ValueError("COMMIT_SHA_VACIO")

    config = cargar_config(config_path)
    if config["requiere_sha_no_procesado"] and sha_ya_procesado(sha, state_path):
        return {
            "schema": SCHEMA,
            "commit_sha": sha,
            "status": "SKIP_SHA_YA_PROCESADO",
            "disparos": 0,
            "gaps": [],
            "resultados": [],
        }

    inventario = cargar_inventario(inventory_path)
    pendientes = nodos_pending_step1(inventario)
    usados_ultima_hora = contar_disparos_ultima_hora(state_path)
    cupo_horario = max(0, config["max_disparos_por_hora"] - usados_ultima_hora)
    cupo_presupuesto = (
        config["presupuesto_maximo_llamadas_llm_por_ciclo"]
        // LLAMADAS_LLM_ESTIMADAS_POR_STEP1
    )
    limite_ciclo = min(len(pendientes), cupo_horario, cupo_presupuesto)

    gaps: list[dict[str, Any]] = []
    resultados: list[dict[str, Any]] = []

    if pendientes and limite_ciclo == 0:
        gaps.append(
            {
                "tipo": "LIMITE_EXCEDIDO",
                "accion": config["si_limite_excedido"],
                "pendientes": len(pendientes),
                "disparos_ultima_hora": usados_ultima_hora,
            }
        )
        return {
            "schema": SCHEMA,
            "commit_sha": sha,
            "status": "PAUSADO_LIMITE",
            "disparos": 0,
            "pendientes_totales": len(pendientes),
            "gaps": gaps,
            "resultados": resultados,
        }

    run = ejecutor or cargar_ejecutor_existente()

    # Bucle deliberadamente acotado por limite_ciclo; nunca procesa más del cupo.
    for nodo in pendientes[:limite_ciclo]:
        component_id = str(nodo.get("component_id") or nodo.get("name") or nodo.get("wall_node_id"))
        registrar_disparo(sha, component_id, state_path)
        try:
            resultado = run(tarea_desde_nodo(nodo))
            resultados.append(
                {
                    "wall_node_id": nodo.get("wall_node_id"),
                    "component_id": component_id,
                    "resultado": resultado,
                }
            )
        except Exception as exc:  # continuar otros nodos: no detener el proyecto
            gaps.append(
                {
                    "tipo": "EJECUCION_GAP",
                    "wall_node_id": nodo.get("wall_node_id"),
                    "component_id": component_id,
                    "error": f"{type(exc).__name__}: {exc}",
                    "accion": "REGISTRAR_GAP_Y_CONTINUAR",
                }
            )

    if len(pendientes) > limite_ciclo:
        gaps.append(
            {
                "tipo": "LIMITE_EXCEDIDO",
                "accion": config["si_limite_excedido"],
                "pendientes_no_disparados_en_este_ciclo": len(pendientes) - limite_ciclo,
            }
        )

    registrar_sha_procesado(sha, state_path)
    status = "CICLO_COMPLETO" if not gaps else "CICLO_CERRADO_CON_GAPS"
    return {
        "schema": SCHEMA,
        "commit_sha": sha,
        "status": status,
        "inventario_component_count": inventario.get("component_count"),
        "pendientes_totales": len(pendientes),
        "disparos": len(resultados) + sum(1 for gap in gaps if gap.get("tipo") == "EJECUCION_GAP"),
        "presupuesto_llm_estimado_usado": limite_ciclo * LLAMADAS_LLM_ESTIMADAS_POR_STEP1,
        "gaps": gaps,
        "resultados": resultados,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatcher acotado del Comand Center YAIWES")
    parser.add_argument("commit_sha", help="SHA del push que originó el ciclo")
    args = parser.parse_args()
    resultado = ejecutar_ciclo(args.commit_sha)
    print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
