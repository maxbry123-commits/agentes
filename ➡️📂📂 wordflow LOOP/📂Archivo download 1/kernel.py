"""
src/core/kernel.py
CORE_KERNEL_DETERMINISTA — T-001 (archivo 1/4)

Responsabilidad: Kernel orquestador. Une DAG engine + Event Bus + State
Machine. Scheduler de micro-misiones con prioridad. Bootstrap minimo de
MavisPool (la implementacion completa de paralelismo vive en T-013).

Dependencias (mismo nodo, entregadas en archivos 2-4 de este mismo T-001):
    src.core.event_bus.EventBus
    src.core.dag_engine.DAGEngine
    src.core.state_machine.StateMachine, NodeState

No requiere secretos. No hace I/O de red. Determinista: mismo input +
mismo estado -> mismo hash de idempotencia -> mismo output.
"""

from __future__ import annotations

import hashlib
import heapq
import itertools
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger("pecp.core.kernel")

DEFAULT_MISSION_PRIORITY: int = 5  # 1 = mas urgente, 9 = menos urgente

# --------------------------------------------------------------------------
# Excepciones
# --------------------------------------------------------------------------


class KernelError(Exception):
    """Error generico e irrecuperable del kernel."""


class IdempotencyViolation(KernelError):
    """Se detecto una divergencia de output para el mismo input_hash."""


class NodeNotRegisteredError(KernelError):
    """Se intento ejecutar un node_id no registrado en el kernel."""


# --------------------------------------------------------------------------
# Micro-mision
# --------------------------------------------------------------------------


@dataclass(order=False, frozen=True)
class MicroMission:
    """Unidad minima de trabajo agendable por el scheduler."""

    mission_id: str
    node_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = DEFAULT_MISSION_PRIORITY
    created_at: float = field(default_factory=time.time)

    def content_hash(self) -> str:
        """Hash deterministico del contenido (para idempotencia)."""
        raw = json.dumps(
            {"node_id": self.node_id, "payload": self.payload},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


# --------------------------------------------------------------------------
# Scheduler de micro-misiones (heap por prioridad, FIFO estable)
# --------------------------------------------------------------------------


class PriorityMissionScheduler:
    """Cola de prioridad estable (empate -> orden de llegada)."""

    def __init__(self) -> None:
        """Inicializa el heap interno y el contador de secuencia FIFO."""
        self._heap: list = []
        self._counter = itertools.count()

    def push(self, mission: MicroMission) -> None:
        """Encola una mision. Empates de prioridad se resuelven FIFO."""
        seq = next(self._counter)
        heapq.heappush(self._heap, (mission.priority, seq, mission))

    def pop(self) -> Optional[MicroMission]:
        """Extrae la mision de mayor prioridad, o None si esta vacia."""
        if not self._heap:
            return None
        _, _, mission = heapq.heappop(self._heap)
        return mission

    def __len__(self) -> int:
        """Cantidad de misiones pendientes en la cola."""
        return len(self._heap)

    def is_empty(self) -> bool:
        """True si no hay misiones pendientes."""
        return len(self._heap) == 0


# --------------------------------------------------------------------------
# MavisPool bootstrap (placeholder deterministico; implementacion completa
# de ejecucion paralela 100x se entrega en T-013 mavis_parallel.py)
# --------------------------------------------------------------------------


@dataclass
class MavisPoolBootstrap:
    """Registro deterministico de la configuracion inicial del pool.

    No ejecuta workers reales; solo valida y congela la configuracion
    que T-013 consumira. Evita que el kernel dependa de T-013.
    """

    max_workers: int = 8
    queue_size: int = 256
    ready: bool = False

    def bootstrap(self) -> Dict[str, Any]:
        """Valida y congela la configuracion. Lanza KernelError si invalida."""
        if self.max_workers <= 0:
            raise KernelError("max_workers debe ser > 0")
        if self.queue_size <= 0:
            raise KernelError("queue_size debe ser > 0")
        self.ready = True
        return {
            "max_workers": self.max_workers,
            "queue_size": self.queue_size,
            "ready": self.ready,
        }


# --------------------------------------------------------------------------
# Kernel
# --------------------------------------------------------------------------


NodeHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Kernel:
    """Orquestador determinista del runtime PECP-MAXBRY-100x.

    Ata event_bus + dag_engine + state_machine. No contiene logica de
    negocio de los nodos: solo orquesta su ejecucion respetando el DAG,
    idempotencia y trazabilidad de eventos.
    """

    def __init__(
        self,
        event_bus: Any,
        dag_engine: Any,
        state_machine: Any,
        mavis_pool: Optional[MavisPoolBootstrap] = None,
    ) -> None:
        """Inyecta las dependencias del kernel (event bus, DAG, state machine)."""
        self._event_bus = event_bus
        self._dag_engine = dag_engine
        self._state_machine = state_machine
        self._mavis_pool = mavis_pool or MavisPoolBootstrap()
        self._handlers: Dict[str, NodeHandler] = {}
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}
        self._scheduler = PriorityMissionScheduler()

    # ---- registro ---------------------------------------------------

    def register_node(
        self,
        node_id: str,
        handler: NodeHandler,
        priority: int = DEFAULT_MISSION_PRIORITY,
    ) -> None:
        """Registra el handler async de un nodo del DAG."""
        if not node_id:
            raise KernelError("node_id vacio")
        self._handlers[node_id] = handler
        logger.debug("nodo registrado node_id=%s priority=%s", node_id, priority)

    def bootstrap(self) -> Dict[str, Any]:
        """Inicializa MavisPool. Debe llamarse antes de run()."""
        return self._mavis_pool.bootstrap()

    # ---- idempotencia -------------------------------------------------

    @staticmethod
    def compute_input_hash(node_id: str, payload: Dict[str, Any]) -> str:
        """Hash deterministico sha256 de (node_id, payload) para idempotencia."""
        raw = json.dumps(
            {"node_id": node_id, "payload": payload},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _check_idempotency(
        self, input_hash: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        cached = self._idempotency_cache.get(input_hash)
        if cached is None:
            self._idempotency_cache[input_hash] = result
            return result
        if cached != result:
            raise IdempotencyViolation(
                f"input_hash={input_hash} produjo outputs distintos"
            )
        return cached

    # ---- ejecucion de un nodo ------------------------------------------

    async def run_node(
        self, node_id: str, payload: Dict[str, Any], mission_id: str
    ) -> Dict[str, Any]:
        """Ejecuta un nodo respetando idempotencia y emite eventos."""
        if node_id not in self._handlers:
            raise NodeNotRegisteredError(node_id)

        input_hash = self.compute_input_hash(node_id, payload)
        cached = await self._try_cache_hit(node_id, mission_id, input_hash)
        if cached is not None:
            return cached

        return await self._execute_and_track(
            node_id, payload, mission_id, input_hash
        )

    async def _try_cache_hit(
        self, node_id: str, mission_id: str, input_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Si input_hash ya fue procesado, emite evento y retorna cache."""
        if input_hash not in self._idempotency_cache:
            return None
        logger.info("cache_hit node_id=%s input_hash=%s", node_id, input_hash)
        await self._emit(
            "node.cache_hit", node_id, mission_id, {"input_hash": input_hash}
        )
        return self._idempotency_cache[input_hash]

    async def _execute_and_track(
        self,
        node_id: str,
        payload: Dict[str, Any],
        mission_id: str,
        input_hash: str,
    ) -> Dict[str, Any]:
        """Corre el handler real, gestiona transiciones y eventos."""
        await self._state_machine.transition(node_id, "RUNNING")
        await self._emit("node.start", node_id, mission_id, {})

        try:
            handler = self._handlers[node_id]
            result = await handler(payload)
        except Exception as exc:  # noqa: BLE001 - frontera de error controlada
            await self._state_machine.transition(node_id, "FAILED")
            await self._emit(
                "node.failed", node_id, mission_id, {"error": str(exc)}
            )
            raise KernelError(f"nodo {node_id} fallo: {exc}") from exc

        result = self._check_idempotency(input_hash, result)
        await self._state_machine.transition(node_id, "DONE")
        await self._emit(
            "node.done", node_id, mission_id, {"input_hash": input_hash}
        )
        return result

    async def _emit(
        self, event_name: str, node_id: str, mission_id: str, data: Dict[str, Any]
    ) -> None:
        await self._event_bus.publish(
            event_name,
            {
                "evento": event_name,
                "nodo_id": node_id,
                "mission_id": mission_id,
                "timestamp": time.time(),
                **data,
            },
        )

    # ---- ejecucion completa del DAG ------------------------------------

    async def run(self, dag_manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Ejecuta todos los nodos del manifest en orden topologico."""
        order = self._dag_engine.topological_order(dag_manifest)
        results: Dict[str, Dict[str, Any]] = {}
        for node_id in order:
            payload = dag_manifest["nodes"][node_id].get("payload", {})
            mission = MicroMission(
                mission_id=f"m-{node_id}", node_id=node_id, payload=payload
            )
            self._scheduler.push(mission)

        while not self._scheduler.is_empty():
            mission = self._scheduler.pop()
            assert mission is not None
            results[mission.node_id] = await self.run_node(
                mission.node_id, mission.payload, mission.mission_id
            )
        return results

    # ---- checkpoint / status --------------------------------------------

    def checkpoint(self) -> Dict[str, Any]:
        """Snapshot deterministico del estado interno del kernel."""
        return {
            "registered_nodes": sorted(self._handlers.keys()),
            "idempotency_entries": len(self._idempotency_cache),
            "mavis_pool": {
                "max_workers": self._mavis_pool.max_workers,
                "ready": self._mavis_pool.ready,
            },
        }

    def status(self) -> Dict[str, Any]:
        """Resumen ligero del estado runtime (para monitoreo/health-check)."""
        return {
            "nodes_registered": len(self._handlers),
            "pending_missions": len(self._scheduler),
            "cache_size": len(self._idempotency_cache),
        }
