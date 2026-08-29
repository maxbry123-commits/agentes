# objective_recovery.py — Motor de Recuperación y Adaptación

> **Archivo:** `objective_recovery.py`  
> **Rol:** Failure classifier, gap analyzer, adaptation strategies  
> **Inspiración:** M-APPLE-OS (compensation + replanning), Conductor (saga pattern)

---

```python
"""
objective_recovery.py
=====================
Motor de recuperación ante fallos con clasificación inteligente y adaptación.

Inspirado en M-APPLE-OS (local compensation + global replanning + rollback),
Conductor (saga pattern + compensation) y el Failure Classifier del documento.

Uso:
    recovery = RecoveryEngine()

    # Clasificar un fallo
    classification = recovery.classify_failure(exec_result, objective)

    # Decidir estrategia de adaptación
    if classification.failure_type == "bad_plan":
        new_dag = recovery.local_replan(exec_dag, classification)
    elif classification.failure_type == "no_path":
        new_dag = recovery.rebuild_subgraph(exec_dag, classification)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable

from objective_engine import ObjectiveDescriptor, EngineResult
from plan_compiler import ExecutionDAG, ExecutionNode, ExecutionNodeType
from objective_graph import ObjectiveGraph, ObjectiveNode, EdgeType, NodeState


class FailureType(Enum):
    TRANSIENT = auto()      # Fallo temporal (timeout, rate limit) -> retry
    BAD_PLAN = auto()       # El plan era incorrecto -> replan local
    BAD_INPUT = auto()      # Faltan datos/evidence -> solicitar input
    NO_PATH = auto()        # No hay camino viable -> estrategia alternativa
    RESOURCE_EXHAUSTED = auto()  # Sin recursos -> escalar/esperar
    UNKNOWN = auto()        # No clasificable -> escalar a humano


@dataclass
class FailureClassification:
    failure_type: FailureType
    confidence: float  # 0.0 - 1.0
    affected_node: Optional[str] = None
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_action: Optional[str] = None


@dataclass
class AdaptationStrategy:
    strategy_type: str  # "retry" | "replan" | "request_evidence" | "alternative" | "escalate"
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_success_probability: float = 0.5


@dataclass
class GapAnalysis:
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    gaps: List[str] = field(default_factory=list)
    severity: str = "medium"  # "low" | "medium" | "high" | "critical"


class RecoveryEngine:
    """
    Motor de recuperación y adaptación.

    Implementa el pipeline:
        FAIL -> FAILURE CLASSIFIER -> [RETRY | REPLAN | REQUEST | ALTERNATIVE]
    """

    def __init__(
        self,
        llm_classifier: Optional[Callable[[Dict[str, Any]], FailureClassification]] = None,
    ):
        self.llm_classifier = llm_classifier
        self._heuristic_rules: List[Callable[[EngineResult], Optional[FailureClassification]]] = []
        self._register_default_heuristics()

    def _register_default_heuristics(self) -> None:
        """Registra reglas heurísticas de clasificación por defecto."""

        def transient_timeout(result: EngineResult) -> Optional[FailureClassification]:
            err = (result.execution_result.error_message or "").lower()
            if any(k in err for k in ["timeout", "connection", "rate limit", "503", "429"]):
                return FailureClassification(
                    failure_type=FailureType.TRANSIENT,
                    confidence=0.9,
                    reason="Error de conectividad/tiempo de espera",
                    suggested_action="retry_with_backoff",
                )
            return None

        def bad_plan_error(result: EngineResult) -> Optional[FailureClassification]:
            err = (result.execution_result.error_message or "").lower()
            if any(k in err for k in ["not found", "invalid", "cannot", "unable to", "no such"]):
                return FailureClassification(
                    failure_type=FailureType.BAD_PLAN,
                    confidence=0.7,
                    reason="El plan no produjo el resultado esperado",
                    suggested_action="replan_affected_subgraph",
                )
            return None

        def resource_exhausted(result: EngineResult) -> Optional[FailureClassification]:
            err = (result.execution_result.error_message or "").lower()
            if any(k in err for k in ["out of memory", "disk full", "quota exceeded", "too many requests"]):
                return FailureClassification(
                    failure_type=FailureType.RESOURCE_EXHAUSTED,
                    confidence=0.85,
                    reason="Recursos agotados",
                    suggested_action="scale_or_wait",
                )
            return None

        self._heuristic_rules.extend([transient_timeout, bad_plan_error, resource_exhausted])

    # ------------------------------------------------------------------
    # CLASIFICACIÓN DE FALLAS
    # ------------------------------------------------------------------

    def classify_failure(
        self,
        exec_result: Any,
        objective: ObjectiveDescriptor,
    ) -> FailureClassification:
        """
        Clasifica un fallo usando heurísticas y (opcionalmente) LLM.

        Pipeline:
            1. Aplicar reglas heurísticas rápidas
            2. Si no hay match, usar LLM classifier
            3. Si todo falla, clasificar como UNKNOWN
        """
        result = EngineResult(
            success=False,
            execution_result=exec_result,
            root_objective=objective,
        )

        # 1. Heurísticas
        for rule in self._heuristic_rules:
            classification = rule(result)
            if classification:
                return classification

        # 2. LLM classifier
        if self.llm_classifier:
            try:
                return self.llm_classifier({
                    "error_message": exec_result.error_message,
                    "objective": objective.description,
                    "postconditions": objective.postconditions,
                    "node_results": exec_result.node_results,
                })
            except Exception:
                pass

        # 3. Fallback: UNKNOWN
        return FailureClassification(
            failure_type=FailureType.UNKNOWN,
            confidence=0.5,
            reason="No se pudo clasificar el fallo automáticamente",
            suggested_action="escalate_to_human",
        )

    # ------------------------------------------------------------------
    # ANÁLISIS DE BRECHAS (Gap Analyzer)
    # ------------------------------------------------------------------

    def analyze_gap(self, failed_result: EngineResult) -> GapAnalysis:
        """
        Analiza la brecha entre el estado esperado y el actual.

        Útil para entender qué postcondiciones no se cumplieron.
        """
        objective = failed_result.root_objective
        if not objective:
            return GapAnalysis(
                expected_state={},
                actual_state={},
                gaps=["No hay objetivo de referencia"],
                severity="critical",
            )

        expected = {
            "postconditions": objective.postconditions,
            "progress": 1.0,
            "state": "completed",
        }

        actual = {
            "postconditions": [],  # En implementación real, verificar cuáles se cumplieron
            "progress": objective.progress,
            "state": objective.state,
        }

        gaps = []
        for post in objective.postconditions:
            # Simplificación: en implementación real se evaluaría cada postcondición
            gaps.append(f"Postcondición no verificada: {post}")

        severity = "critical" if len(gaps) > len(objective.postconditions) / 2 else "medium"

        return GapAnalysis(
            expected_state=expected,
            actual_state=actual,
            gaps=gaps,
            severity=severity,
        )

    # ------------------------------------------------------------------
    # ESTRATEGIAS DE ADAPTACIÓN
    # ------------------------------------------------------------------

    def decide_adaptation(
        self,
        classification: FailureClassification,
        gap: GapAnalysis,
    ) -> AdaptationStrategy:
        """
        Decide la estrategia de adaptación basada en la clasificación.
        """
        strategies = {
            FailureType.TRANSIENT: AdaptationStrategy(
                strategy_type="retry",
                description="Reintentar con backoff exponencial",
                parameters={"max_retries": 3, "backoff_base": 2},
                estimated_success_probability=0.8,
            ),
            FailureType.BAD_PLAN: AdaptationStrategy(
                strategy_type="replan",
                description="Replanificar el subgrafo afectado",
                parameters={"scope": "local", "preserve_completed": True},
                estimated_success_probability=0.6,
            ),
            FailureType.BAD_INPUT: AdaptationStrategy(
                strategy_type="request_evidence",
                description="Solicitar evidence adicional al usuario o al entorno",
                parameters={"request_type": "clarification", "blocking": True},
                estimated_success_probability=0.7,
            ),
            FailureType.NO_PATH: AdaptationStrategy(
                strategy_type="alternative",
                description="Construir subgrafo con estrategia alternativa",
                parameters={"strategy_source": "memory_or_llm"},
                estimated_success_probability=0.5,
            ),
            FailureType.RESOURCE_EXHAUSTED: AdaptationStrategy(
                strategy_type="escalate",
                description="Escalar recursos o esperar a disponibilidad",
                parameters={"action": "scale_or_wait"},
                estimated_success_probability=0.4,
            ),
            FailureType.UNKNOWN: AdaptationStrategy(
                strategy_type="escalate",
                description="Escalar a supervisión humana",
                parameters={"urgency": "high"},
                estimated_success_probability=0.2,
            ),
        }

        return strategies.get(
            classification.failure_type,
            AdaptationStrategy(
                strategy_type="escalate",
                description="Estrategia desconocida, escalar",
                estimated_success_probability=0.1,
            ),
        )

    # ------------------------------------------------------------------
    # REPLANIFICACIÓN
    # ------------------------------------------------------------------

    def local_replan(
        self,
        exec_dag: ExecutionDAG,
        classification: FailureClassification,
    ) -> ExecutionDAG:
        """
        Replanificación local: modifica solo el subgrafo afectado.

        Mantiene todo lo que ya funcionó, solo reconstruye desde el nodo fallido.
        """
        affected_node = classification.affected_node
        if not affected_node:
            # Si no sabemos qué nodo falló, no podemos hacer local replan
            return exec_dag

        # En implementación real:
        # 1. Identificar el subgrafo desde el nodo afectado
        # 2. Solicitar al LLM un nuevo subplan
        # 3. Reemplazar el subgrafo antiguo con el nuevo
        # 4. Revalidar el DAG resultante

        # Stub: retornar el mismo DAG (en producción se modificaría)
        return exec_dag

    def rebuild_subgraph(
        self,
        exec_dag: ExecutionDAG,
        classification: FailureClassification,
    ) -> ExecutionDAG:
        """
        Reconstrucción completa de un subgrafo con estrategia alternativa.

        Usado cuando no hay camino viable con el enfoque actual.
        """
        # En implementación real:
        # 1. Marcar el subgrafo actual como inválido
        # 2. Consultar ObjectiveMemory por estrategias alternativas
        # 3. Generar nuevo subgrafo con la estrategia alternativa
        # 4. Reconectar dependencias

        return exec_dag

    def rollback_to_checkpoint(
        self,
        exec_dag: ExecutionDAG,
        checkpoint_data: Dict[str, Any],
    ) -> ExecutionDAG:
        """
        Rollback a un estado previo válido.

        Inspirado en M-APPLE-OS y Conductor (saga pattern).
        """
        # En implementación real:
        # 1. Identificar el último checkpoint válido
        # 2. Ejecutar compensaciones en orden inverso
        # 3. Restaurar estado
        # 4. Retornar DAG al punto de checkpoint

        return exec_dag

```
