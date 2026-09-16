"""
src/core/dag_engine.py
CORE_KERNEL_DETERMINISTA — T-001 (archivo 3/4)

Responsabilidad: Orden topologico deterministico, deteccion de ciclos y
un generador async de "batches" de nodos listos (ejecucion por eventos)
sobre un dag_manifest. Usa graphlib.TopologicalSorter (stdlib) como
motor base, con desempate alfabetico explicito para garantizar E15
(mismo input -> mismo output) independientemente del orden interno de
iteracion de graphlib.

Contrato de manifest esperado (dag_manifest.schema.json):
{
  "nodes": {
    "<node_id>": {
      "payload": {...},               # opcional
      "depends_on": ["<node_id>", ...]  # opcional, default []
    },
    ...
  }
}

No requiere secretos. No hace I/O de red. Determinista.
"""

from __future__ import annotations

import graphlib
from typing import Any, AsyncIterator, Dict, List, Optional, Set

# --------------------------------------------------------------------------
# Excepciones
# --------------------------------------------------------------------------


class DAGEngineError(Exception):
    """Error generico del motor de DAG."""


class ManifestValidationError(DAGEngineError):
    """El dag_manifest no cumple el schema minimo esperado."""


class CycleDetectedError(DAGEngineError):
    """Se detecto un ciclo en el grafo de dependencias."""

    def __init__(self, cycle: List[str]) -> None:
        """Guarda el ciclo detectado para diagnostico."""
        self.cycle = cycle
        super().__init__(f"ciclo detectado: {' -> '.join(cycle)}")


# --------------------------------------------------------------------------
# DAGEngine
# --------------------------------------------------------------------------


class DAGEngine:
    """Motor determinista de orden topologico sobre un dag_manifest."""

    def validate_manifest(self, manifest: Dict[str, Any]) -> None:
        """Valida la forma minima del manifest. Lanza si es invalido."""
        if not isinstance(manifest, dict) or "nodes" not in manifest:
            raise ManifestValidationError("manifest debe contener 'nodes'")
        nodes = manifest["nodes"]
        if not isinstance(nodes, dict) or not nodes:
            raise ManifestValidationError("'nodes' debe ser un dict no vacio")
        self._validate_node_entries(nodes)

    def _validate_node_entries(self, nodes: Dict[str, Any]) -> None:
        """Valida cada entrada de nodo y que sus dependencias existan."""
        for node_id, spec in nodes.items():
            if not isinstance(spec, dict):
                raise ManifestValidationError(
                    f"nodo '{node_id}' debe mapear a un dict"
                )
            for dep in spec.get("depends_on", []):
                if dep not in nodes:
                    raise ManifestValidationError(
                        f"nodo '{node_id}' depende de '{dep}' inexistente"
                    )

    def _build_predecessors(
        self, manifest: Dict[str, Any]
    ) -> Dict[str, Set[str]]:
        """Construye {node_id: {predecessores}} para graphlib."""
        nodes = manifest["nodes"]
        return {
            node_id: set(spec.get("depends_on", []))
            for node_id, spec in nodes.items()
        }

    def _new_sorter(
        self, manifest: Dict[str, Any]
    ) -> "graphlib.TopologicalSorter[str]":
        """Valida el manifest y prepara un TopologicalSorter listo para usar."""
        self.validate_manifest(manifest)
        graph = self._build_predecessors(manifest)
        sorter: "graphlib.TopologicalSorter[str]" = graphlib.TopologicalSorter(
            graph
        )
        try:
            sorter.prepare()
        except graphlib.CycleError as exc:
            cycle = list(exc.args[1]) if len(exc.args) > 1 else []
            raise CycleDetectedError(cycle) from exc
        return sorter

    def topological_order(self, manifest: Dict[str, Any]) -> List[str]:
        """Retorna el orden topologico completo, determinista por nivel."""
        sorter = self._new_sorter(manifest)
        order: List[str] = []
        while sorter.is_active():
            ready = sorted(sorter.get_ready())
            order.extend(ready)
            sorter.done(*ready)
        return order

    def detect_cycle(self, manifest: Dict[str, Any]) -> Optional[List[str]]:
        """Retorna la lista de nodos en ciclo, o None si el DAG es aciclico."""
        try:
            self._new_sorter(manifest)
        except CycleDetectedError as exc:
            return exc.cycle
        return None

    async def iter_ready_batches(
        self, manifest: Dict[str, Any]
    ) -> AsyncIterator[List[str]]:
        """Genera batches de nodos listos, nivel a nivel (ejecucion por eventos).

        Cada batch es la lista (ordenada alfabeticamente) de node_id que
        pueden ejecutarse en paralelo dado el estado actual del DAG. El
        caller debe consumir el generador completo; internamente se
        cede el control del event loop entre batches via `asyncio.sleep(0)`
        equivalente (aqui usamos un yield puro, sin bloquear).
        """
        sorter = self._new_sorter(manifest)
        while sorter.is_active():
            ready = sorted(sorter.get_ready())
            if not ready:
                break
            yield ready
            sorter.done(*ready)
