# objective_engine.py — Motor Principal del Objective Engine v2

> **Archivo:** `objective_engine.py`  
> **Rol:** Orquestador del pipeline completo  
> **Dependencias:** Todos los sub-módulos del kernel

---

```python
"""
objective_engine.py
===================
Motor principal del Objective Engine v2.

Este módulo orquesta todo el pipeline: descubrimiento, normalización,
evidence, grafo, validación, compilación, ejecución, evaluación y recuperación.

Integra todos los sub-módulos del kernel de objetivos.

Uso:
    engine = ObjectiveEngine(llm_client=my_llm)
    result = await engine.run(
        root_objective="Implementar módulo de memoria",
        context={"spec": "...", "constraints": [...]}
    )
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

# Sub-módulos del kernel (se asumen en el mismo package)
from objective_graph import ObjectiveGraph, ObjectiveNode, EdgeType
from plan_compiler import PlanCompiler, ExecutionDAG, ExecutionNode
from plan_validator import PlanValidator, ValidationReport
from objective_memory import ObjectiveMemory, StrategyRecord
from objective_runtime import ExecutionRuntime, ExecutionResult, WorkerPool
from objective_recovery import RecoveryEngine, FailureClassification, AdaptationStrategy

logger = logging.getLogger("objective_engine")


# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================

class EngineState(Enum):
    """Estados posibles del motor."""
    IDLE = auto()
    DISCOVERING = auto()
    NORMALIZING = auto()
    BUILDING_GRAPH = auto()
    VALIDATING = auto()
    COMPILING = auto()
    EXECUTING = auto()
    OBSERVING = auto()
    EVALUATING = auto()
    RECOVERING = auto()
    REPLANNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class ObjectiveUrgency(Enum):
    """Niveles de urgencia para objetivos."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EvidenceItem:
    """Una pieza de evidence que respalda un objetivo."""
    source: str
    content: str
    confidence: float = 1.0  # 0.0 - 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectiveDescriptor:
    """
    Descriptor estructurado de un objetivo.

    Este es el objeto que sale del Objective Discovery + Normalizer.
    """
    identity: str
    description: str
    evidence: List[EvidenceItem] = field(default_factory=list)
    confidence: float = 0.0
    value: float = 0.0          # Valor esperado del objetivo
    urgency: ObjectiveUrgency = ObjectiveUrgency.MEDIUM
    effort_estimate: float = 0.0  # Horas/puntos estimados
    constraints: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    state: str = "pending"
    progress: float = 0.0
    attempts: int = 0
    observations: List[str] = field(default_factory=list)
    provenance: str = "discovery"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity,
            "description": self.description,
            "evidence": [json.dumps(e, default=str) for e in self.evidence],
            "confidence": self.confidence,
            "value": self.value,
            "urgency": self.urgency.name,
            "effort_estimate": self.effort_estimate,
            "constraints": self.constraints,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "dependencies": self.dependencies,
            "alternatives": self.alternatives,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "state": self.state,
            "progress": self.progress,
            "attempts": self.attempts,
            "observations": self.observations,
            "provenance": self.provenance,
            "metadata": self.metadata,
        }


@dataclass
class EngineResult:
    """Resultado completo de una ejecución del motor."""
    success: bool
    root_objective: Optional[ObjectiveDescriptor] = None
    execution_dag: Optional[ExecutionDAG] = None
    execution_result: Optional[ExecutionResult] = None
    validation_report: Optional[ValidationReport] = None
    failure_classification: Optional[FailureClassification] = None
    adaptation_strategy: Optional[AdaptationStrategy] = None
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    strategy_record: Optional[StrategyRecord] = None
    final_output: Any = None
    error_message: Optional[str] = None


# ============================================================================
# MOTOR PRINCIPAL
# ============================================================================

class ObjectiveEngine:
    """
    Motor de objetivos v2.

    Pipeline completo:
        DISCOVER → NORMALIZE → EVIDENCE → GRAPH → VALIDATE → COMPILE →
        EXECUTE → OBSERVE → EVALUATE → [SUCCESS|RECOVERY → REPLAN] → MEMORY
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_replan_attempts: int = 3,
        checkpoint_interval: int = 1,
        worker_pool_size: int = 4,
        memory_persistence_path: Optional[str] = None,
    ):
        self.llm_client = llm_client
        self.max_replan_attempts = max_replan_attempts
        self.checkpoint_interval = checkpoint_interval
        self.state = EngineState.IDLE
        self._audit_log: List[Dict[str, Any]] = []
        self._checkpoints: List[Dict[str, Any]] = []

        # Sub-sistemas
        self.graph_builder = ObjectiveGraph()
        self.validator = PlanValidator()
        self.compiler = PlanCompiler()
        self.memory = ObjectiveMemory(persistence_path=memory_persistence_path)
        self.runtime = ExecutionRuntime(worker_pool_size=worker_pool_size)
        self.recovery = RecoveryEngine()

        logger.info("ObjectiveEngine v2 inicializado")

    # ------------------------------------------------------------------
    # API PÚBLICA PRINCIPAL
    # ------------------------------------------------------------------

    async def run(
        self,
        root_objective: str,
        context: Optional[Dict[str, Any]] = None,
        evidence_items: Optional[List[EvidenceItem]] = None,
        auto_execute: bool = True,
    ) -> EngineResult:
        """
        Ejecuta el pipeline completo sobre un objetivo raíz.

        Args:
            root_objective: Descripción en lenguaje natural del objetivo.
            context: Contexto adicional (especificaciones, constraints, etc.).
            evidence_items: Evidence pre-existente.
            auto_execute: Si True, ejecuta inmediatamente. Si False, solo planifica.

        Returns:
            EngineResult con todo el resultado de la ejecución.
        """
        self._audit_log = []
        self._checkpoints = []
        self.state = EngineState.DISCOVERING

        try:
            # PASO 1: Discovery + Normalization
            objective = await self._discover_and_normalize(
                root_objective, context, evidence_items
            )
            self._log("DISCOVER", {"objective_id": objective.identity})

            # PASO 2: Evidence Engine
            objective = await self._gather_evidence(objective, context)
            self._log("EVIDENCE", {"evidence_count": len(objective.evidence)})

            # PASO 3: Build Objective Graph
            self.state = EngineState.BUILDING_GRAPH
            graph = await self._build_graph(objective, context)
            self._log("GRAPH", {"nodes": len(graph.nodes), "edges": len(graph.edges)})

            # PASO 4: Plan Validation
            self.state = EngineState.VALIDATING
            validation = self.validator.validate_graph(graph)
            self._log("VALIDATE", {"valid": validation.is_valid, "errors": validation.errors})

            if not validation.is_valid:
                return await self._handle_validation_failure(objective, graph, validation)

            # PASO 5: Plan Compilation
            self.state = EngineState.COMPILING
            exec_dag = self.compiler.compile(graph)
            self._log("COMPILE", {"dag_nodes": len(exec_dag.nodes)})

            if not auto_execute:
                return EngineResult(
                    success=True,
                    root_objective=objective,
                    execution_dag=exec_dag,
                    validation_report=validation,
                    audit_log=self._audit_log,
                )

            # PASO 6: Execution
            self.state = EngineState.EXECUTING
            exec_result = await self._execute_with_recovery(exec_dag, objective)
            self._log("EXECUTE", {"status": exec_result.status})

            # PASO 7: Evaluation
            self.state = EngineState.EVALUATING
            eval_success = await self._evaluate_result(objective, exec_result)
            self._log("EVALUATE", {"success": eval_success})

            # PASO 8: Memory (Strategy Learning)
            strategy = await self._record_strategy(objective, exec_dag, exec_result, eval_success)

            self.state = EngineState.COMPLETED if eval_success else EngineState.FAILED

            return EngineResult(
                success=eval_success,
                root_objective=objective,
                execution_dag=exec_dag,
                execution_result=exec_result,
                validation_report=validation,
                checkpoints=self._checkpoints,
                audit_log=self._audit_log,
                strategy_record=strategy,
                final_output=exec_result.output if exec_result else None,
                error_message=None if eval_success else exec_result.error_message,
            )

        except Exception as e:
            logger.exception("ObjectiveEngine falló en ejecución")
            self.state = EngineState.FAILED
            self._log("FATAL", {"error": str(e)})
            return EngineResult(
                success=False,
                audit_log=self._audit_log,
                checkpoints=self._checkpoints,
                error_message=str(e),
            )

    async def replan(
        self,
        failed_result: EngineResult,
        new_evidence: Optional[List[EvidenceItem]] = None,
    ) -> EngineResult:
        """
        Replanifica desde un resultado fallido.

        Usa la información del fallo para generar una nueva estrategia.
        """
        if failed_result.attempts and failed_result.attempts >= self.max_replan_attempts:
            raise RuntimeError(f"Máximo de reintentos ({self.max_replan_attempts}) alcanzado")

        self.state = EngineState.REPLANNING
        self._log("REPLAN", {"previous_error": failed_result.error_message})

        # Recuperar el objetivo original
        objective = failed_result.root_objective
        if objective is None:
            raise ValueError("No hay objetivo para replanificar")

        objective.attempts += 1

        # Inyectar nueva evidence si existe
        if new_evidence:
            objective.evidence.extend(new_evidence)

        # Usar el Gap Analyzer para entender qué falló
        gap_analysis = self.recovery.analyze_gap(failed_result)

        # Modificar el objetivo o el contexto basado en el análisis
        objective.observations.append(f"Gap analysis: {gap_analysis}")

        # Re-ejecutar el pipeline completo
        return await self.run(
            root_objective=objective.description,
            context={"replan": True, "gap_analysis": gap_analysis, "previous_audit": self._audit_log},
        )

    # ------------------------------------------------------------------
    # MÉTODOS INTERNOS
    # ------------------------------------------------------------------

    async def _discover_and_normalize(
        self,
        description: str,
        context: Optional[Dict[str, Any]],
        evidence_items: Optional[List[EvidenceItem]],
    ) -> ObjectiveDescriptor:
        """Descubre y normaliza el objetivo en un descriptor estructurado."""

        # Si hay LLM, usarlo para enriquecer la descripción
        if self.llm_client:
            enriched = await self._llm_enrich_objective(description, context)
        else:
            enriched = {"description": description, "confidence": 0.5}

        objective = ObjectiveDescriptor(
            identity=self._generate_id("obj"),
            description=enriched.get("description", description),
            confidence=enriched.get("confidence", 0.5),
            value=enriched.get("value", 0.0),
            urgency=ObjectiveUrgency[enriched.get("urgency", "MEDIUM")],
            effort_estimate=enriched.get("effort", 0.0),
            constraints=enriched.get("constraints", []),
            preconditions=enriched.get("preconditions", []),
            postconditions=enriched.get("postconditions", []),
            provenance="discovery_llm" if self.llm_client else "discovery_basic",
        )

        if evidence_items:
            objective.evidence.extend(evidence_items)

        return objective

    async def _gather_evidence(
        self,
        objective: ObjectiveDescriptor,
        context: Optional[Dict[str, Any]],
    ) -> ObjectiveDescriptor:
        """Recopila evidence adicional para el objetivo."""
        # Buscar en memoria objetivos similares
        similar = self.memory.find_similar(objective.description, top_k=3)
        for rec in similar:
            objective.evidence.append(EvidenceItem(
                source="objective_memory",
                content=f"Estrategia previa: {rec.strategy} (score: {rec.success_score})",
                confidence=rec.success_score,
                metadata={"strategy_id": rec.id},
            ))

        # Aquí se podrían añadir búsquedas web, RAG, etc.
        return objective

    async def _build_graph(
        self,
        objective: ObjectiveDescriptor,
        context: Optional[Dict[str, Any]],
    ) -> ObjectiveGraph:
        """Construye el grafo de objetivos a partir del descriptor."""
        # Crear nodo raíz
        root_node = ObjectiveNode(
            id=objective.identity,
            description=objective.description,
            node_type="objective",
            urgency=objective.urgency.value,
            preconditions=objective.preconditions,
            postconditions=objective.postconditions,
            metadata=objective.to_dict(),
        )
        self.graph_builder.add_node(root_node)

        # Si hay LLM, descomponer en sub-objetivos
        if self.llm_client and context and context.get("auto_decompose", True):
            sub_objectives = await self._llm_decompose(objective, context)
            for sub in sub_objectives:
                sub_node = ObjectiveNode(
                    id=sub["id"],
                    description=sub["description"],
                    node_type="subgoal",
                    parent_id=root_node.id,
                    urgency=sub.get("urgency", 3),
                    preconditions=sub.get("preconditions", []),
                    postconditions=sub.get("postconditions", []),
                )
                self.graph_builder.add_node(sub_node)
                self.graph_builder.add_edge(root_node.id, sub_node.id, EdgeType.DECOMPOSITION)

                # Dependencias entre sub-objetivos
                for dep_id in sub.get("depends_on", []):
                    self.graph_builder.add_edge(dep_id, sub_node.id, EdgeType.DEPENDENCY)

                # Tareas dentro del sub-objetivo
                for task in sub.get("tasks", []):
                    task_node = ObjectiveNode(
                        id=task["id"],
                        description=task["description"],
                        node_type="task",
                        parent_id=sub_node.id,
                        preconditions=task.get("preconditions", []),
                        postconditions=task.get("postconditions", []),
                    )
                    self.graph_builder.add_node(task_node)
                    self.graph_builder.add_edge(sub_node.id, task_node.id, EdgeType.DECOMPOSITION)

        return self.graph_builder

    async def _execute_with_recovery(
        self,
        exec_dag: ExecutionDAG,
        objective: ObjectiveDescriptor,
    ) -> ExecutionResult:
        """Ejecuta el DAG con manejo de fallos y recuperación."""
        attempt = 0
        while attempt <= self.max_replan_attempts:
            result = await self.runtime.execute(
                exec_dag,
                checkpoint_callback=self._on_checkpoint,
            )

            if result.status == "success":
                return result

            # Clasificar el fallo
            classification = self.recovery.classify_failure(result, objective)
            self._log("FAILURE_CLASSIFIED", {
                "type": classification.failure_type,
                "confidence": classification.confidence,
            })

            if classification.failure_type == "transient":
                # Retry simple
                attempt += 1
                self._log("RETRY", {"attempt": attempt})
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue

            elif classification.failure_type == "bad_plan":
                # Replanificación local
                self._log("LOCAL_REPLAN", {"node": classification.affected_node})
                exec_dag = self.recovery.local_replan(exec_dag, classification)
                attempt += 1
                continue

            elif classification.failure_type == "bad_input":
                # Solicitar nueva evidence
                self._log("REQUEST_EVIDENCE", {"reason": classification.reason})
                # En un sistema real, esto pausaría y esperaría input
                raise RuntimeError(f"Evidence insuficiente: {classification.reason}")

            elif classification.failure_type == "no_path":
                # Estrategia alternativa
                self._log("ALTERNATIVE_STRATEGY", {"reason": classification.reason})
                exec_dag = self.recovery.rebuild_subgraph(exec_dag, classification)
                attempt += 1
                continue

            else:
                break

        return result

    async def _evaluate_result(
        self,
        objective: ObjectiveDescriptor,
        exec_result: ExecutionResult,
    ) -> bool:
        """Evalúa si el resultado cumple las postcondiciones del objetivo."""
        if exec_result.status != "success":
            return False

        # Verificar postcondiciones
        for post in objective.postconditions:
            # En un sistema real, esto ejecutaría verificadores específicos
            if not self._check_condition(post, exec_result.output):
                logger.warning(f"Postcondición fallida: {post}")
                return False

        return True

    async def _record_strategy(
        self,
        objective: ObjectiveDescriptor,
        exec_dag: ExecutionDAG,
        exec_result: ExecutionResult,
        success: bool,
    ) -> StrategyRecord:
        """Registra la estrategia en memoria para aprendizaje futuro."""
        record = StrategyRecord(
            id=self._generate_id("strat"),
            objective_description=objective.description,
            strategy={"dag_structure": exec_dag.to_dict()},
            result={"status": exec_result.status, "output_summary": str(exec_result.output)[:500]},
            success=success,
            lesson=exec_result.error_message if not success else "Ejecución exitosa",
            success_score=1.0 if success else 0.0,
            timestamp=datetime.utcnow(),
        )
        self.memory.store(record)
        return record

    async def _handle_validation_failure(
        self,
        objective: ObjectiveDescriptor,
        graph: ObjectiveGraph,
        validation: ValidationReport,
    ) -> EngineResult:
        """Maneja el caso donde el grafo no pasa validación."""
        self.state = EngineState.FAILED
        self._log("VALIDATION_FAILED", {"errors": validation.errors})

        # Intentar auto-reparar el grafo si es posible
        if validation.repairable:
            self._log("AUTO_REPAIR", {"attempt": True})
            repaired = self.validator.auto_repair(graph, validation)
            if repaired:
                # Re-validar
                validation = self.validator.validate_graph(repaired)
                if validation.is_valid:
                    self._log("AUTO_REPAIR_SUCCESS", {})
                    # Continuar con el grafo reparado
                    exec_dag = self.compiler.compile(repaired)
                    exec_result = await self._execute_with_recovery(exec_dag, objective)
                    # ... (simplificado)

        return EngineResult(
            success=False,
            root_objective=objective,
            validation_report=validation,
            audit_log=self._audit_log,
            error_message=f"Validación fallida: {validation.errors}",
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _log(self, event: str, data: Dict[str, Any]) -> None:
        """Registra un evento en el audit log."""
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "state": self.state.name,
            "data": data,
        })

    def _on_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """Callback para guardar checkpoints durante ejecución."""
        checkpoint_data["saved_at"] = datetime.utcnow().isoformat()
        self._checkpoints.append(checkpoint_data)
        logger.debug(f"Checkpoint guardado: {checkpoint_data.get('node_id')}")

    def _generate_id(self, prefix: str) -> str:
        """Genera un ID único."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _check_condition(self, condition: str, output: Any) -> bool:
        """Verifica una condición contra un output. (Stub)"""
        # En implementación real, esto usaría un DSL de condiciones
        return True

    async def _llm_enrich_objective(
        self,
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Usa el LLM para enriquecer el objetivo. (Stub)"""
        # En implementación real, prompt estructurado al LLM
        return {
            "description": description,
            "confidence": 0.8,
            "urgency": "MEDIUM",
        }

    async def _llm_decompose(
        self,
        objective: ObjectiveDescriptor,
        context: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Usa el LLM para descomponer el objetivo. (Stub)"""
        # En implementación real, prompt estructurado al LLM
        return []

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado actual del motor."""
        return {
            "state": self.state.name,
            "audit_events": len(self._audit_log),
            "checkpoints": len(self._checkpoints),
            "memory_strategies": len(self.memory.records),
        }

    def export_audit(self, path: str) -> None:
        """Exporta el audit log a JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._audit_log, f, indent=2, default=str)

    def export_checkpoints(self, path: str) -> None:
        """Exporta los checkpoints a JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._checkpoints, f, indent=2, default=str)

```
