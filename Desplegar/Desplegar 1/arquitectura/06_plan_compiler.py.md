# plan_compiler.py — Compilador de Planes

> **Archivo:** `plan_compiler.py`  
> **Rol:** Convierte ObjectiveGraph → ExecutionDAG determinista e inmutable  
> **Inspiración:** Agentspan (plan→compile→execute), Conductor (separación orquestación/implementación)

---

```python
"""
plan_compiler.py
================
Compilador de planes: convierte un ObjectiveGraph en un ExecutionDAG determinista.

Inspirado en Agentspan (plan → compile → deterministic execution) y Conductor
(separación de orquestación e implementación).

Pipeline de compilación:
    ObjectiveGraph
        ↓
    [1] SCHEMA VALIDATION (estructura del grafo)
    [2] OBJECTIVE VALIDATION (coherencia de objetivos)
    [3] DEPENDENCY VALIDATION (completitud de dependencias)
    [4] PRECONDITION VALIDATION (factibilidad de precondiciones)
    [5] CYCLE DETECTION (usando DFS)
    [6] RESOURCE VALIDATION (disponibilidad de recursos)
    [7] TOPOLOGICAL SORT + NIVELACIÓN
    [8] DAG COMPILER (generación de ExecutionDAG inmutable)
        ↓
    ExecutionDAG (listo para ejecución determinista)

Uso:
    compiler = PlanCompiler()
    exec_dag = compiler.compile(objective_graph)

    # El ExecutionDAG es inmutable después de la compilación
    # El runtime solo puede ejecutar, no modificar
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Callable
from collections import defaultdict

from objective_graph import ObjectiveGraph, ObjectiveNode, ObjectiveEdge, EdgeType, NodeState


class ExecutionNodeType(Enum):
    """Tipos de nodo en el DAG de ejecución."""
    TASK = auto()           # Tarea ejecutable
    GATEWAY = auto()        # Punto de decisión (if/else)
    PARALLEL = auto()       # Inicio de sección paralela
    JOIN = auto()           # Sincronización de paralelos
    CHECKPOINT = auto()     # Punto de persistencia
    SIGNAL = auto()         # Espera de señal externa


@dataclass(frozen=True)
class ExecutionNode:
    """
    Nodo inmutable en el DAG de ejecución.

    Una vez compilado, no puede modificarse. Garantiza determinismo.
    """
    id: str
    source_node_id: str  # Referencia al nodo original en ObjectiveGraph
    node_type: ExecutionNodeType

    # Ejecución
    action: Optional[str] = None  # Identificador de la acción a ejecutar
    action_config: Dict[str, Any] = field(default_factory=dict)

    # Condiciones compiladas
    preconditions: Tuple[str, ...] = field(default_factory=tuple)
    postconditions: Tuple[str, ...] = field(default_factory=tuple)

    # Recursos
    required_resources: Tuple[str, ...] = field(default_factory=tuple)
    estimated_duration: float = 1.0

    # Paralelismo
    parallel_group: Optional[str] = None  # ID del grupo paralelo

    # Metadata inmutable
    metadata: Tuple[tuple, ...] = field(default_factory=tuple)  # frozen dict as tuple of tuples

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "node_type": self.node_type.name,
            "action": self.action,
            "action_config": self.action_config,
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "required_resources": list(self.required_resources),
            "estimated_duration": self.estimated_duration,
            "parallel_group": self.parallel_group,
        }


@dataclass(frozen=True)
class ExecutionEdge:
    """Arista inmutable en el DAG de ejecución."""
    source_id: str
    target_id: str
    condition: Optional[str] = None  # Condición para activar esta arista (gateways)
    weight: float = 1.0


@dataclass
class ExecutionDAG:
    """
    DAG de ejecución inmutable y determinista.

    Propiedades garantizadas:
    - Acíclico (validado en compilación)
    - Conexo (todos los nodos alcanzables desde el inicio)
    - Determinista (mismo input = mismo grafo)
    - Inmutable (no se modifica en runtime)
    """
    nodes: Dict[str, ExecutionNode] = field(default_factory=dict)
    edges: List[ExecutionEdge] = field(default_factory=list)
    start_nodes: List[str] = field(default_factory=list)
    end_nodes: List[str] = field(default_factory=list)

    # Estructuras derivadas (pre-computadas para eficiencia)
    _adjacency: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    _reverse_adj: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    _levels: List[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if not self._adjacency:
            for edge in self.edges:
                self._adjacency[edge.source_id].append(edge.target_id)
                self._reverse_adj[edge.target_id].append(edge.source_id)

    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        return self.nodes.get(node_id)

    def get_successors(self, node_id: str) -> List[ExecutionNode]:
        return [self.nodes[tid] for tid in self._adjacency.get(node_id, []) if tid in self.nodes]

    def get_predecessors(self, node_id: str) -> List[ExecutionNode]:
        return [self.nodes[sid] for sid in self._reverse_adj.get(node_id, []) if sid in self.nodes]

    def is_start_node(self, node_id: str) -> bool:
        return node_id in self.start_nodes

    def is_end_node(self, node_id: str) -> bool:
        return node_id in self.end_nodes

    def get_level(self, node_id: str) -> int:
        """Devuelve el nivel topológico del nodo."""
        for i, level in enumerate(self._levels):
            if node_id in level:
                return i
        return -1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "condition": e.condition,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
            "start_nodes": self.start_nodes,
            "end_nodes": self.end_nodes,
            "levels": self._levels,
        }


# ============================================================================
# COMPILADOR
# ============================================================================

class CompilationError(Exception):
    """Error durante la compilación del plan."""
    pass


class PlanCompiler:
    """
    Compilador de planes: ObjectiveGraph → ExecutionDAG.

    Realiza múltiples pasos de validación antes de generar el DAG final.
    """

    def __init__(
        self,
        resource_checker: Optional[Callable[[Set[str]], bool]] = None,
        condition_checker: Optional[Callable[[str], bool]] = None,
    ):
        self.resource_checker = resource_checker
        self.condition_checker = condition_checker
        self._validation_hooks: List[Callable[[ObjectiveGraph], List[str]]] = []

    def add_validation_hook(self, hook: Callable[[ObjectiveGraph], List[str]]) -> None:
        """Añade un hook de validación personalizado."""
        self._validation_hooks.append(hook)

    def compile(self, graph: ObjectiveGraph) -> ExecutionDAG:
        """
        Compila un ObjectiveGraph en un ExecutionDAG.

        Args:
            graph: El grafo de objetivos a compilar.

        Returns:
            ExecutionDAG inmutable y validado.

        Raises:
            CompilationError: Si alguna validación falla.
        """
        errors = []

        # [1] SCHEMA VALIDATION
        schema_errors = self._validate_schema(graph)
        errors.extend(schema_errors)

        # [2] OBJECTIVE VALIDATION
        obj_errors = self._validate_objectives(graph)
        errors.extend(obj_errors)

        # [3] DEPENDENCY VALIDATION
        dep_errors = self._validate_dependencies(graph)
        errors.extend(dep_errors)

        # [4] PRECONDITION VALIDATION
        pre_errors = self._validate_preconditions(graph)
        errors.extend(pre_errors)

        # [5] CYCLE DETECTION
        cycles = graph.detect_cycles()
        if cycles:
            errors.append(f"Ciclos detectados: {cycles}")

        # [6] RESOURCE VALIDATION
        if self.resource_checker:
            resource_errors = self._validate_resources(graph)
            errors.extend(resource_errors)

        # [7] VALIDATION HOOKS PERSONALIZADOS
        for hook in self._validation_hooks:
            hook_errors = hook(graph)
            errors.extend(hook_errors)

        if errors:
            raise CompilationError(f"Compilación fallida con {len(errors)} errores: {errors}")

        # [8] DAG COMPILATION
        return self._build_execution_dag(graph)

    # ------------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------------

    def _validate_schema(self, graph: ObjectiveGraph) -> List[str]:
        """Valida la estructura básica del grafo."""
        errors = []

        # Todos los nodos deben tener ID único
        ids = [n.id for n in graph.nodes.values()]
        if len(ids) != len(set(ids)):
            errors.append("IDs de nodos duplicados detectados")

        # Todas las aristas deben referenciar nodos existentes
        for edge in graph.edges:
            if edge.source_id not in graph.nodes:
                errors.append(f"Arista referencia nodo inexistente: {edge.source_id}")
            if edge.target_id not in graph.nodes:
                errors.append(f"Arista referencia nodo inexistente: {edge.target_id}")

        # Debe haber al menos un nodo raíz (sin padre)
        roots = [n for n in graph.nodes.values() if n.parent_id is None]
        if len(roots) == 0:
            errors.append("No hay nodos raíz en el grafo")
        if len(roots) > 1:
            errors.append(f"Múltiples nodos raíz detectados: {[r.id for r in roots]}")

        return errors

    def _validate_objectives(self, graph: ObjectiveGraph) -> List[str]:
        """Valida la coherencia de los objetivos."""
        errors = []

        for node in graph.nodes.values():
            # Descripción no vacía
            if not node.description or not node.description.strip():
                errors.append(f"Nodo {node.id} tiene descripción vacía")

            # Esfuerzo positivo
            if node.estimated_effort <= 0:
                errors.append(f"Nodo {node.id} tiene esfuerzo no positivo: {node.estimated_effort}")

            # Urgencia válida
            if not 1 <= node.urgency <= 5:
                errors.append(f"Nodo {node.id} tiene urgencia inválida: {node.urgency}")

        return errors

    def _validate_dependencies(self, graph: ObjectiveGraph) -> List[str]:
        """Valida que todas las dependencias sean resolubles."""
        errors = []

        for node in graph.nodes.values():
            deps = graph.get_dependencies(node.id)
            for dep in deps:
                # Verificar que no hay dependencia circular directa
                reverse_deps = graph.get_dependencies(dep.id)
                if node in reverse_deps:
                    errors.append(f"Dependencia circular directa: {node.id} ↔ {dep.id}")

        return errors

    def _validate_preconditions(self, graph: ObjectiveGraph) -> List[str]:
        """Valida que las precondiciones sean factibles."""
        errors = []

        if self.condition_checker:
            for node in graph.nodes.values():
                for pre in node.preconditions:
                    if not self.condition_checker(pre):
                        errors.append(f"Precondición no satisfacible para {node.id}: {pre}")

        return errors

    def _validate_resources(self, graph: ObjectiveGraph) -> List[str]:
        """Valida disponibilidad de recursos."""
        errors = []

        if self.resource_checker:
            all_resources = set()
            for node in graph.nodes.values():
                all_resources.update(node.required_resources)

            if not self.resource_checker(all_resources):
                errors.append(f"Recursos no disponibles: {all_resources}")

        return errors

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DEL DAG
    # ------------------------------------------------------------------

    def _build_execution_dag(self, graph: ObjectiveGraph) -> ExecutionDAG:
        """Construye el ExecutionDAG a partir del grafo validado."""
        exec_nodes: Dict[str, ExecutionNode] = {}
        exec_edges: List[ExecutionEdge] = []

        # Mapeo: objective_node_id → execution_node_id
        node_mapping: Dict[str, str] = {}

        # [A] Crear nodos de ejecución
        for obj_node in graph.nodes.values():
            exec_id = f"exec_{obj_node.id}"
            node_mapping[obj_node.id] = exec_id

            # Determinar tipo de nodo de ejecución
            exec_type = self._determine_execution_type(obj_node, graph)

            # Determinar grupo paralelo
            parallel_group = self._determine_parallel_group(obj_node, graph)

            exec_node = ExecutionNode(
                id=exec_id,
                source_node_id=obj_node.id,
                node_type=exec_type,
                action=obj_node.node_type,  # La acción es el tipo de nodo original
                action_config={
                    "description": obj_node.description,
                    "original_type": obj_node.node_type,
                },
                preconditions=tuple(obj_node.preconditions),
                postconditions=tuple(obj_node.postconditions),
                required_resources=tuple(obj_node.required_resources),
                estimated_duration=obj_node.estimated_effort,
                parallel_group=parallel_group,
                metadata=tuple((k, str(v)) for k, v in obj_node.metadata.items()),
            )
            exec_nodes[exec_id] = exec_node

        # [B] Crear aristas de ejecución
        for obj_edge in graph.edges:
            if obj_edge.edge_type == EdgeType.DEPENDENCY:
                src_exec = node_mapping.get(obj_edge.source_id)
                tgt_exec = node_mapping.get(obj_edge.target_id)
                if src_exec and tgt_exec:
                    exec_edges.append(ExecutionEdge(
                        source_id=src_exec,
                        target_id=tgt_exec,
                        weight=obj_edge.weight,
                    ))
            elif obj_edge.edge_type == EdgeType.SEQUENTIAL:
                src_exec = node_mapping.get(obj_edge.source_id)
                tgt_exec = node_mapping.get(obj_edge.target_id)
                if src_exec and tgt_exec:
                    exec_edges.append(ExecutionEdge(
                        source_id=src_exec,
                        target_id=tgt_exec,
                    ))
            elif obj_edge.edge_type == EdgeType.ALTERNATIVE:
                # Las alternativas se manejan como gateways condicionales
                src_exec = node_mapping.get(obj_edge.source_id)
                tgt_exec = node_mapping.get(obj_edge.target_id)
                if src_exec and tgt_exec:
                    exec_edges.append(ExecutionEdge(
                        source_id=src_exec,
                        target_id=tgt_exec,
                        condition=f"alternative_{obj_edge.source_id}",
                    ))

        # [C] Detectar nodos de inicio y fin
        start_nodes = [nid for nid in exec_nodes if not exec_nodes[nid].get_predecessors()]
        if not start_nodes:
            # Si no hay nodos sin predecesores, usar los nodos raíz del grafo original
            start_nodes = [node_mapping[n.id] for n in graph.nodes.values() if n.parent_id is None]

        end_nodes = [nid for nid in exec_nodes if not exec_nodes[nid].get_successors()]

        # [D] Calcular niveles topológicos para paralelismo
        levels = self._compute_levels(exec_nodes, exec_edges)

        # [E] Añadir checkpoints automáticos después de cada nivel
        exec_nodes, exec_edges, levels = self._inject_checkpoints(
            exec_nodes, exec_edges, levels
        )

        return ExecutionDAG(
            nodes=exec_nodes,
            edges=exec_edges,
            start_nodes=start_nodes,
            end_nodes=end_nodes,
            _levels=levels,
        )

    def _determine_execution_type(self, node: ObjectiveNode, graph: ObjectiveGraph) -> ExecutionNodeType:
        """Determina el tipo de nodo de ejecución basado en el nodo original."""
        # Si tiene alternativas, es un gateway
        alts = graph.get_alternatives(node.id)
        if alts:
            return ExecutionNodeType.GATEWAY

        # Si tiene múltiples dependencias entrantes, es un join
        deps = graph.get_dependencies(node.id)
        if len(deps) > 1:
            return ExecutionNodeType.JOIN

        # Si tiene múltiples hijos sin dependencias entre ellos, es paralelo
        children = graph.get_children(node.id)
        if len(children) > 1:
            return ExecutionNodeType.PARALLEL

        # Por defecto, es una tarea
        return ExecutionNodeType.TASK

    def _determine_parallel_group(self, node: ObjectiveNode, graph: ObjectiveGraph) -> Optional[str]:
        """Determina si el nodo pertenece a un grupo paralelo."""
        parent = graph.get_node(node.parent_id) if node.parent_id else None
        if parent:
            siblings = graph.get_children(parent.id)
            if len(siblings) > 1:
                # Verificar si los hermanos no tienen dependencias entre sí
                sibling_ids = {s.id for s in siblings}
                for s in siblings:
                    deps = graph.get_dependencies(s.id)
                    if any(d.id in sibling_ids for d in deps):
                        return None  # Hay dependencias, no son paralelos puros
                return f"parallel_{parent.id}"
        return None

    def _compute_levels(
        self,
        nodes: Dict[str, ExecutionNode],
        edges: List[ExecutionEdge],
    ) -> List[List[str]]:
        """Calcula los niveles topológicos para ejecución paralela."""
        in_degree = {nid: 0 for nid in nodes}
        adj = defaultdict(list)

        for edge in edges:
            adj[edge.source_id].append(edge.target_id)
            in_degree[edge.target_id] += 1

        levels = []
        current_level = [nid for nid, deg in in_degree.items() if deg == 0]

        while current_level:
            levels.append(current_level)
            next_level = []
            for nid in current_level:
                for tgt in adj[nid]:
                    in_degree[tgt] -= 1
                    if in_degree[tgt] == 0:
                        next_level.append(tgt)
            current_level = next_level

        return levels

    def _inject_checkpoints(
        self,
        nodes: Dict[str, ExecutionNode],
        edges: List[ExecutionEdge],
        levels: List[List[str]],
    ) -> tuple:
        """Inyecta nodos de checkpoint entre niveles."""
        new_nodes = dict(nodes)
        new_edges = list(edges)
        new_levels = []

        for i, level in enumerate(levels):
            new_levels.append(level)

            # Añadir checkpoint después de cada nivel (excepto el último)
            if i < len(levels) - 1:
                cp_id = f"checkpoint_level_{i}"
                cp_node = ExecutionNode(
                    id=cp_id,
                    source_node_id="system",
                    node_type=ExecutionNodeType.CHECKPOINT,
                    action="checkpoint",
                    estimated_duration=0.1,
                )
                new_nodes[cp_id] = cp_node

                # Conectar todos los nodos del nivel actual al checkpoint
                for nid in level:
                    new_edges.append(ExecutionEdge(source_id=nid, target_id=cp_id))

                # Conectar el checkpoint a todos los nodos del siguiente nivel
                next_level = levels[i + 1]
                for nid in next_level:
                    new_edges.append(ExecutionEdge(source_id=cp_id, target_id=nid))

                new_levels.append([cp_id])

        return new_nodes, new_edges, new_levels

```
