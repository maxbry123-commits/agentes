# objective_graph.py — Grafo Compuesto de Objetivos

> **Archivo:** `objective_graph.py`  
> **Rol:** Modelo de datos y análisis del grafo de objetivos  
> **Inspiración:** PlanDB compound graph, Open-Sable goal hierarchy

---

```python
"""
objective_graph.py
==================
Grafo compuesto de objetivos con jerarquía, dependencias cruzadas y caminos alternativos.

Inspirado en PlanDB (compound graph) y Open-Sable (goal hierarchy).

Uso:
    graph = ObjectiveGraph()
    graph.add_node(ObjectiveNode(id="root", description="Build app", node_type="objective"))
    graph.add_node(ObjectiveNode(id="backend", description="API", node_type="subgoal", parent_id="root"))
    graph.add_edge("root", "backend", EdgeType.DECOMPOSITION)
    graph.add_edge("backend", "frontend", EdgeType.DEPENDENCY)

    # Detectar ciclos
    cycles = graph.detect_cycles()

    # Calcular critical path
    cp = graph.critical_path()

    # Obtener tareas listas para ejecución (sin dependencias pendientes)
    ready = graph.ready_nodes()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, deque


class EdgeType(Enum):
    """Tipos de aristas en el grafo compuesto."""
    DECOMPOSITION = auto()      # Padre → Hijo (jerarquía)
    DEPENDENCY = auto()         # A → B (B depende de A)
    ALTERNATIVE = auto()        # A ↔ B (caminos alternativos)
    SEQUENTIAL = auto()         # A → B (orden secuencial implícito)


class NodeState(Enum):
    """Estados de un nodo en el grafo."""
    PENDING = auto()
    READY = auto()          # Todas las dependencias satisfechas
    RUNNING = auto()
    BLOCKED = auto()        # Tiene dependencias no satisfechas
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()        # Camino alternativo no elegido


@dataclass
class ObjectiveNode:
    """
    Nodo en el grafo de objetivos.

    Puede representar: objetivo raíz, sub-objetivo, tarea, milestone, etc.
    """
    id: str
    description: str
    node_type: str = "task"  # objective | subgoal | task | milestone | checkpoint

    # Jerarquía
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # Estado
    state: NodeState = NodeState.PENDING
    progress: float = 0.0  # 0.0 - 1.0

    # Planificación
    estimated_effort: float = 1.0  # Unidades de esfuerzo (horas, story points)
    urgency: int = 3  # 1 (CRITICAL) - 5 (OPTIONAL)
    priority_score: float = 0.0  # Calculado: urgency / effort

    # Condiciones
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)

    # Recursos
    required_resources: List[str] = field(default_factory=list)
    assigned_worker: Optional[str] = None

    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat())

    def __post_init__(self):
        if self.priority_score == 0.0 and self.urgency > 0 and self.estimated_effort > 0:
            self.priority_score = (6 - self.urgency) / self.estimated_effort

    def is_ready(self, completed_ids: Set[str]) -> bool:
        """Verifica si todas las precondiciones/dependencias están satisfechas."""
        # En una implementación real, evaluaría las precondiciones contra el estado del mundo
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "node_type": self.node_type,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "state": self.state.name,
            "progress": self.progress,
            "estimated_effort": self.estimated_effort,
            "urgency": self.urgency,
            "priority_score": self.priority_score,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "required_resources": self.required_resources,
            "assigned_worker": self.assigned_worker,
            "metadata": self.metadata,
        }


@dataclass
class ObjectiveEdge:
    """Arista en el grafo de objetivos."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0  # Para cálculo de critical path
    metadata: Dict[str, Any] = field(default_factory=dict)


class ObjectiveGraph:
    """
    Grafo compuesto de objetivos.

    Combina:
    - Jerarquía (containment): padres contienen hijos
    - Dependencias (flow): aristas entre nodos a cualquier nivel
    - Alternativas: caminos opcionales
    """

    def __init__(self):
        self.nodes: Dict[str, ObjectiveNode] = {}
        self.edges: List[ObjectiveEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)  # source -> [targets]
        self._reverse_adj: Dict[str, List[str]] = defaultdict(list)  # target -> [sources]
        self._edge_types: Dict[Tuple[str, str], EdgeType] = {}

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN
    # ------------------------------------------------------------------

    def add_node(self, node: ObjectiveNode) -> ObjectiveNode:
        """Añade un nodo al grafo."""
        if node.id in self.nodes:
            raise ValueError(f"Nodo {node.id} ya existe")
        self.nodes[node.id] = node
        return node

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType, weight: float = 1.0) -> ObjectiveEdge:
        """Añade una arista al grafo."""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Ambos nodos deben existir en el grafo")

        edge = ObjectiveEdge(source_id, target_id, edge_type, weight)
        self.edges.append(edge)
        self._adjacency[source_id].append(target_id)
        self._reverse_adj[target_id].append(source_id)
        self._edge_types[(source_id, target_id)] = edge_type
        return edge

    def remove_node(self, node_id: str) -> None:
        """Elimina un nodo y todas sus aristas."""
        if node_id not in self.nodes:
            return
        del self.nodes[node_id]

        # Limpiar aristas
        self.edges = [e for e in self.edges if e.source_id != node_id and e.target_id != node_id]

        # Limpiar adjacency
        if node_id in self._adjacency:
            del self._adjacency[node_id]
        for src, targets in self._adjacency.items():
            if node_id in targets:
                targets.remove(node_id)

        if node_id in self._reverse_adj:
            del self._reverse_adj[node_id]
        for tgt, sources in self._reverse_adj.items():
            if node_id in sources:
                sources.remove(node_id)

    # ------------------------------------------------------------------
    # CONSULTAS
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> Optional[ObjectiveNode]:
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[ObjectiveNode]:
        """Devuelve los hijos directos (por descomposición)."""
        return [self.nodes[cid] for cid in self.nodes[node_id].children_ids if cid in self.nodes]

    def get_dependencies(self, node_id: str) -> List[ObjectiveNode]:
        """Devuelve los nodos de los que depende (aristas entrantes de tipo DEPENDENCY)."""
        deps = []
        for src in self._reverse_adj.get(node_id, []):
            if self._edge_types.get((src, node_id)) == EdgeType.DEPENDENCY:
                deps.append(self.nodes[src])
        return deps

    def get_dependents(self, node_id: str) -> List[ObjectiveNode]:
        """Devuelve los nodos que dependen de este (aristas salientes de tipo DEPENDENCY)."""
        deps = []
        for tgt in self._adjacency.get(node_id, []):
            if self._edge_types.get((node_id, tgt)) == EdgeType.DEPENDENCY:
                deps.append(self.nodes[tgt])
        return deps

    def get_alternatives(self, node_id: str) -> List[ObjectiveNode]:
        """Devuelve los nodos alternativos."""
        alts = []
        for tgt in self._adjacency.get(node_id, []):
            if self._edge_types.get((node_id, tgt)) == EdgeType.ALTERNATIVE:
                alts.append(self.nodes[tgt])
        return alts

    def ready_nodes(self) -> List[ObjectiveNode]:
        """
        Devuelve los nodos listos para ejecución.

        Un nodo está listo cuando:
        - Su estado es PENDING
        - Todas sus dependencias (aristas DEPENDENCY entrantes) están COMPLETED
        - Todas sus precondiciones están satisfechas
        """
        ready = []
        completed_ids = {nid for nid, n in self.nodes.items() if n.state == NodeState.COMPLETED}

        for node in self.nodes.values():
            if node.state != NodeState.PENDING:
                continue

            # Verificar dependencias
            deps = self.get_dependencies(node.id)
            if all(d.state == NodeState.COMPLETED for d in deps):
                ready.append(node)

        # Ordenar por priority_score descendente
        ready.sort(key=lambda n: n.priority_score, reverse=True)
        return ready

    def blocked_nodes(self) -> List[ObjectiveNode]:
        """Devuelve los nodos bloqueados por dependencias no satisfechas."""
        blocked = []
        for node in self.nodes.values():
            if node.state == NodeState.PENDING:
                deps = self.get_dependencies(node.id)
                if any(d.state != NodeState.COMPLETED for d in deps):
                    blocked.append(node)
        return blocked

    # ------------------------------------------------------------------
    # ANÁLISIS DE GRAFO
    # ------------------------------------------------------------------

    def detect_cycles(self) -> List[List[str]]:
        """
        Detecta ciclos en el grafo de dependencias usando DFS.

        Returns:
            Lista de ciclos encontrados (cada ciclo es una lista de IDs).
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id: str) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for tgt in self._adjacency.get(node_id, []):
                if self._edge_types.get((node_id, tgt)) != EdgeType.DEPENDENCY:
                    continue
                if tgt not in visited:
                    dfs(tgt)
                elif tgt in rec_stack:
                    # Ciclo encontrado
                    cycle_start = path.index(tgt)
                    cycle = path[cycle_start:] + [tgt]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)

        return cycles

    def topological_sort(self) -> List[str]:
        """
        Orden topológico del grafo de dependencias.

        Returns:
            Lista de IDs en orden de ejecución válido.
        Raises:
            ValueError: Si hay ciclos en el grafo.
        """
        cycles = self.detect_cycles()
        if cycles:
            raise ValueError(f"Ciclos detectados: {cycles}")

        # Kahn's algorithm
        in_degree = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            if edge.edge_type == EdgeType.DEPENDENCY:
                in_degree[edge.target_id] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for tgt in self._adjacency.get(node_id, []):
                if self._edge_types.get((node_id, tgt)) == EdgeType.DEPENDENCY:
                    in_degree[tgt] -= 1
                    if in_degree[tgt] == 0:
                        queue.append(tgt)

        if len(result) != len(self.nodes):
            raise ValueError("Orden topológico incompleto — posible ciclo no detectado")

        return result

    def critical_path(self) -> Tuple[List[str], float]:
        """
        Calcula el critical path usando el algoritmo de longest path en DAG.

        Returns:
            (path, total_duration): Lista de IDs en el critical path y duración total.
        """
        topo = self.topological_sort()

        # Distancia máxima desde el inicio
        dist = {nid: 0.0 for nid in self.nodes}
        pred = {nid: None for nid in self.nodes}

        for node_id in topo:
            node = self.nodes[node_id]
            duration = node.estimated_effort

            for tgt in self._adjacency.get(node_id, []):
                if self._edge_types.get((node_id, tgt)) == EdgeType.DEPENDENCY:
                    edge_weight = next((e.weight for e in self.edges 
                                       if e.source_id == node_id and e.target_id == tgt), 1.0)
                    new_dist = dist[node_id] + duration + edge_weight
                    if new_dist > dist[tgt]:
                        dist[tgt] = new_dist
                        pred[tgt] = node_id

        # Encontrar el nodo final con mayor distancia
        end_node = max(dist, key=dist.get)
        max_duration = dist[end_node]

        # Reconstruir el path
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = pred[current]
        path.reverse()

        return path, max_duration

    def parallel_levels(self) -> List[List[str]]:
        """
        Agrupa nodos en niveles donde cada nivel puede ejecutarse en paralelo.

        Returns:
            Lista de listas de IDs, donde cada lista interna es un nivel paralelo.
        """
        topo = self.topological_sort()
        levels = []
        assigned = set()

        while len(assigned) < len(self.nodes):
            level = []
            for node_id in topo:
                if node_id in assigned:
                    continue
                deps = self.get_dependencies(node_id)
                if all(d.id in assigned for d in deps):
                    level.append(node_id)

            if not level:
                raise ValueError("No se pueden asignar niveles — posible ciclo")

            levels.append(level)
            assigned.update(level)

        return levels

    def bottleneck_analysis(self) -> Dict[str, Any]:
        """
        Análisis de cuellos de botella.

        Returns:
            Dict con: critical_path, max_parallelism, blocked_count, etc.
        """
        cp, cp_duration = self.critical_path()
        levels = self.parallel_levels()
        max_parallel = max(len(l) for l in levels) if levels else 0
        blocked = self.blocked_nodes()
        ready = self.ready_nodes()

        return {
            "critical_path": cp,
            "critical_path_duration": cp_duration,
            "parallel_levels": levels,
            "max_parallelism": max_parallel,
            "total_nodes": len(self.nodes),
            "ready_nodes": [n.id for n in ready],
            "blocked_nodes": [n.id for n in blocked],
            "bottleneck_score": len(blocked) / len(self.nodes) if self.nodes else 0,
        }

    # ------------------------------------------------------------------
    # MUTACIÓN / EVOLUCIÓN
    # ------------------------------------------------------------------

    def split_node(self, node_id: str, sub_nodes: List[ObjectiveNode]) -> None:
        """
        Divide un nodo en sub-nodos (como `plandb split`).

        El nodo original se mantiene como contenedor; los sub-nodos se añaden
        como hijos y heredan las dependencias del nodo original.
        """
        parent = self.nodes.get(node_id)
        if not parent:
            raise ValueError(f"Nodo {node_id} no existe")

        for sub in sub_nodes:
            sub.parent_id = node_id
            self.add_node(sub)
            parent.children_ids.append(sub.id)
            self.add_edge(node_id, sub.id, EdgeType.DECOMPOSITION)

        # Las dependencias del nodo original ahora son dependencias del último sub-nodo
        # (o se distribuyen según lógica de negocio)

    def pivot_subtree(self, node_id: str, new_subtree: ObjectiveGraph) -> None:
        """
        Reemplaza un sub-árbol completo (como `plandb pivot`).

        Útil cuando un enfoque falla y se necesita una estrategia alternativa.
        """
        # Guardar dependencias entrantes y salientes del nodo
        incoming_deps = self.get_dependencies(node_id)
        outgoing_deps = self.get_dependents(node_id)

        # Eliminar el sub-árbol antiguo
        self._remove_subtree(node_id)

        # Añadir el nuevo sub-árbol
        for node in new_subtree.nodes.values():
            self.add_node(node)
        for edge in new_subtree.edges:
            self.add_edge(edge.source_id, edge.target_id, edge.edge_type, edge.weight)

        # Reconectar dependencias
        for dep in incoming_deps:
            self.add_edge(dep.id, node_id, EdgeType.DEPENDENCY)
        for dep in outgoing_deps:
            self.add_edge(node_id, dep.id, EdgeType.DEPENDENCY)

    def _remove_subtree(self, node_id: str) -> None:
        """Elimina recursivamente un nodo y todos sus descendientes."""
        to_remove = [node_id]
        queue = deque([node_id])

        while queue:
            current = queue.popleft()
            for child in self.nodes.get(current, ObjectiveNode("")).children_ids:
                if child in self.nodes and child not in to_remove:
                    to_remove.append(child)
                    queue.append(child)

        for nid in to_remove:
            self.remove_node(nid)

    # ------------------------------------------------------------------
    # SERIALIZACIÓN
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.edge_type.name,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ObjectiveGraph:
        graph = cls()
        for nid, ndata in data.get("nodes", {}).items():
            node = ObjectiveNode(
                id=ndata["id"],
                description=ndata["description"],
                node_type=ndata.get("node_type", "task"),
                parent_id=ndata.get("parent_id"),
                children_ids=ndata.get("children_ids", []),
                state=NodeState[ndata.get("state", "PENDING")],
                progress=ndata.get("progress", 0.0),
                estimated_effort=ndata.get("estimated_effort", 1.0),
                urgency=ndata.get("urgency", 3),
                preconditions=ndata.get("preconditions", []),
                postconditions=ndata.get("postconditions", []),
                required_resources=ndata.get("required_resources", []),
                assigned_worker=ndata.get("assigned_worker"),
                metadata=ndata.get("metadata", {}),
            )
            graph.add_node(node)

        for edata in data.get("edges", []):
            graph.add_edge(
                edata["source"],
                edata["target"],
                EdgeType[edata["type"]],
                edata.get("weight", 1.0),
            )

        return graph

```
