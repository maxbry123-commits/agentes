# objective_runtime.py — Runtime de Ejecución Paralela

> **Archivo:** `objective_runtime.py`  
> **Rol:** Ejecución durable, paralela, con checkpointing y señales  
> **Inspiración:** Conductor (durable execution), Open-Multi-Agent (task DAG scheduling)

---

```python
"""
objective_runtime.py
====================
Runtime de ejecución con workers paralelos, checkpointing y señales.

Inspirado en Conductor (durable execution, polyglot workers) y
Open-Multi-Agent (task DAG scheduling, parallel execution).

Uso:
    runtime = ExecutionRuntime(worker_pool_size=4)
    result = await runtime.execute(
        exec_dag,
        checkpoint_callback=my_checkpoint_fn,
        signal_handler=my_signal_fn,
    )
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Coroutine

from plan_compiler import ExecutionDAG, ExecutionNode, ExecutionNodeType, ExecutionEdge

logger = logging.getLogger("objective_runtime")


class ExecutionStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class ExecutionResult:
    status: str  # "success" | "failed" | "cancelled"
    output: Any = None
    node_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    checkpoints_hit: int = 0
    parallel_tasks_executed: int = 0


@dataclass
class NodeExecutionState:
    node_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0


class WorkerPool:
    """
    Pool de workers para ejecución paralela.
    """

    def __init__(self, size: int):
        self.size = size
        self.semaphore = asyncio.Semaphore(size)
        self.active_tasks: Set[asyncio.Task] = set()

    async def execute(
        self,
        coro: Coroutine[Any, Any, Any],
    ) -> Any:
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.active_tasks.add(task)
            try:
                return await task
            finally:
                self.active_tasks.discard(task)

    def cancel_all(self) -> None:
        for task in self.active_tasks:
            task.cancel()


class ExecutionRuntime:
    """
    Runtime de ejecución durable y paralela.

    Características:
    - Ejecución por niveles topológicos (paralelismo automático)
    - Checkpointing entre niveles
    - Manejo de señales (pause, resume, cancel)
    - Retry con backoff exponencial
    - Observability completa (trazas por nodo)
    """

    def __init__(
        self,
        worker_pool_size: int = 4,
        max_retries: int = 3,
        checkpoint_interval: int = 1,
    ):
        self.worker_pool = WorkerPool(worker_pool_size)
        self.max_retries = max_retries
        self.checkpoint_interval = checkpoint_interval

        self._node_states: Dict[str, NodeExecutionState] = {}
        self._paused: bool = False
        self._cancelled: bool = False
        self._checkpoint_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._signal_handler: Optional[Callable[[str], Optional[str]]] = None

    async def execute(
        self,
        dag: ExecutionDAG,
        checkpoint_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        signal_handler: Optional[Callable[[str], Optional[str]]] = None,
        node_executor: Optional[Callable[[ExecutionNode], Coroutine[Any, Any, Any]]] = None,
    ) -> ExecutionResult:
        """
        Ejecuta el DAG de ejecución completo.
        """
        self._checkpoint_callback = checkpoint_callback
        self._signal_handler = signal_handler
        self._paused = False
        self._cancelled = False

        start_time = datetime.utcnow()
        self._node_states = {
            nid: NodeExecutionState(node_id=nid)
            for nid in dag.nodes
        }

        # Ejecutar por niveles
        for level_idx, level in enumerate(dag._levels):
            if self._cancelled:
                return ExecutionResult(
                    status="cancelled",
                    error_message="Ejecución cancelada por señal",
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )

            # Esperar si está pausado
            while self._paused:
                await asyncio.sleep(0.5)
                if self._cancelled:
                    return ExecutionResult(status="cancelled")

            # Ejecutar nivel en paralelo
            level_tasks = []
            for node_id in level:
                node = dag.get_node(node_id)
                if not node:
                    continue

                # Verificar precondiciones
                if not self._check_preconditions(node, dag):
                    continue

                # Ejecutar nodo
                coro = self._execute_node(node, dag, node_executor)
                task = self.worker_pool.execute(coro)
                level_tasks.append(task)

            # Esperar a que termine el nivel
            if level_tasks:
                try:
                    await asyncio.gather(*level_tasks, return_exceptions=True)
                except Exception as e:
                    logger.exception("Error en nivel de ejecución")
                    return ExecutionResult(
                        status="failed",
                        error_message=str(e),
                        duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    )

            # Checkpoint después del nivel
            if (level_idx + 1) % self.checkpoint_interval == 0:
                await self._save_checkpoint(dag, level_idx)

        # Evaluar resultado final
        failed_nodes = [
            s for s in self._node_states.values()
            if s.status == ExecutionStatus.FAILED
        ]

        duration = (datetime.utcnow() - start_time).total_seconds()

        if failed_nodes:
            return ExecutionResult(
                status="failed",
                error_message=f"Nodos fallidos: {[n.node_id for n in failed_nodes]}",
                node_results={nid: s.output for nid, s in self._node_states.items()},
                duration_seconds=duration,
            )

        return ExecutionResult(
            status="success",
            output=self._node_states.get(dag.end_nodes[0], NodeExecutionState("")).output if dag.end_nodes else None,
            node_results={nid: s.output for nid, s in self._node_states.items()},
            duration_seconds=duration,
            checkpoints_hit=len(dag._levels) // self.checkpoint_interval,
            parallel_tasks_executed=sum(
                1 for s in self._node_states.values()
                if s.status == ExecutionStatus.COMPLETED
            ),
        )

    async def _execute_node(
        self,
        node: ExecutionNode,
        dag: ExecutionDAG,
        node_executor: Optional[Callable[[ExecutionNode], Coroutine[Any, Any, Any]]],
    ) -> None:
        """Ejecuta un nodo individual con retry."""
        state = self._node_states[node.id]
        state.status = ExecutionStatus.RUNNING
        state.start_time = datetime.utcnow()

        for attempt in range(self.max_retries + 1):
            try:
                if node.node_type == ExecutionNodeType.CHECKPOINT:
                    # Los checkpoints no ejecutan lógica de negocio
                    state.output = {"checkpoint": True, "level": dag.get_level(node.id)}
                    state.status = ExecutionStatus.COMPLETED
                    break

                if node_executor:
                    result = await node_executor(node)
                else:
                    result = await self._default_executor(node)

                state.output = result
                state.status = ExecutionStatus.COMPLETED
                break

            except Exception as e:
                state.retry_count += 1
                logger.warning(f"Nodo {node.id} falló (intento {attempt + 1}): {e}")

                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    state.error = str(e)
                    state.status = ExecutionStatus.FAILED

        state.end_time = datetime.utcnow()

    async def _default_executor(self, node: ExecutionNode) -> Any:
        """Ejecutor por defecto (stub)."""
        # En implementación real, esto despacharía a herramientas/LLM
        await asyncio.sleep(0.1)  # Simular trabajo
        return {"executed": node.id, "action": node.action}

    def _check_preconditions(self, node: ExecutionNode, dag: ExecutionDAG) -> bool:
        """Verifica que los predecesores hayan completado."""
        preds = dag.get_predecessors(node.id)
        for pred in preds:
            pred_state = self._node_states.get(pred.id)
            if not pred_state or pred_state.status != ExecutionStatus.COMPLETED:
                return False
        return True

    async def _save_checkpoint(self, dag: ExecutionDAG, level_idx: int) -> None:
        """Guarda un checkpoint del estado actual."""
        if not self._checkpoint_callback:
            return

        checkpoint_data = {
            "level": level_idx,
            "node_states": {
                nid: {
                    "status": s.status.name,
                    "output": s.output,
                    "error": s.error,
                }
                for nid, s in self._node_states.items()
            },
        }

        try:
            self._checkpoint_callback(checkpoint_data)
        except Exception as e:
            logger.error(f"Error guardando checkpoint: {e}")

    # ------------------------------------------------------------------
    # SEÑALES DE CONTROL
    # ------------------------------------------------------------------

    def pause(self) -> None:
        """Pausa la ejecución (se detiene entre niveles)."""
        self._paused = True
        logger.info("Ejecución pausada")

    def resume(self) -> None:
        """Reanuda la ejecución pausada."""
        self._paused = False
        logger.info("Ejecución reanudada")

    def cancel(self) -> None:
        """Cancela la ejecución."""
        self._cancelled = True
        self.worker_pool.cancel_all()
        logger.info("Ejecución cancelada")

    async def resume_from_checkpoint(
        self,
        dag: ExecutionDAG,
        checkpoint_data: Dict[str, Any],
        **kwargs,
    ) -> ExecutionResult:
        """
        Reanuda ejecución desde un checkpoint.
        """
        # Restaurar estados de nodos completados
        node_states = checkpoint_data.get("node_states", {})
        for nid, data in node_states.items():
            if nid in self._node_states:
                self._node_states[nid].status = ExecutionStatus[data.get("status", "PENDING")]
                self._node_states[nid].output = data.get("output")

        # Continuar ejecución desde el nivel siguiente
        level_idx = checkpoint_data.get("level", 0)

        # Reconstruir niveles restantes
        remaining_levels = dag._levels[level_idx + 1:]

        # Ejecutar niveles restantes
        # (simplificado: en implementación real se reanuda el runtime)
        return await self.execute(dag, **kwargs)

```
