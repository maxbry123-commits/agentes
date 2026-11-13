# plan_validator.py — Validador de Planes Multi-Capa

> **Archivo:** `plan_validator.py`  
> **Rol:** Validación estructural, semántica y de constraints antes de compilación  
> **Inspiración:** M-APPLE-OS (self-validation), PlanDB (pre/postconditions)

---

```python
"""
plan_validator.py
=================
Validador multi-capa de planes y grafos de objetivos.

Realiza validaciones estructurales, semánticas y de constraints antes de
permitir la compilación.

Inspirado en M-APPLE-OS (self-validation en cada paso) y PlanDB (pre/postconditions).

Uso:
    validator = PlanValidator()
    report = validator.validate_graph(my_graph)

    if report.is_valid:
        print("Plan válido")
    else:
        print(f"Errores: {report.errors}")
        if report.repairable:
            repaired = validator.auto_repair(my_graph, report)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Callable
from collections import defaultdict

from objective_graph import ObjectiveGraph, ObjectiveNode, EdgeType, NodeState


@dataclass
class ValidationIssue:
    """Un problema detectado durante la validación."""
    severity: str  # "error" | "warning" | "info"
    category: str  # "schema" | "cycle" | "dependency" | "precondition" | "resource" | "semantic"
    message: str
    node_id: Optional[str] = None
    edge_ids: Optional[List[tuple]] = None
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None


@dataclass
class ValidationReport:
    """Reporte completo de validación."""
    is_valid: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    infos: List[ValidationIssue] = field(default_factory=list)
    repairable: bool = False
    repair_actions: List[Dict[str, Any]] = field(default_factory=list)

    def add_issue(self, issue: ValidationIssue) -> None:
        if issue.severity == "error":
            self.errors.append(issue)
            self.is_valid = False
        elif issue.severity == "warning":
            self.warnings.append(issue)
        else:
            self.infos.append(issue)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "repairable": self.repairable,
            "errors": [self._issue_to_dict(e) for e in self.errors],
            "warnings": [self._issue_to_dict(w) for w in self.warnings],
            "infos": [self._issue_to_dict(i) for i in self.infos],
        }

    @staticmethod
    def _issue_to_dict(issue: ValidationIssue) -> Dict[str, Any]:
        return {
            "severity": issue.severity,
            "category": issue.category,
            "message": issue.message,
            "node_id": issue.node_id,
            "auto_fixable": issue.auto_fixable,
            "suggested_fix": issue.suggested_fix,
        }


class PlanValidator:
    """
    Validador de planes con múltiples capas de verificación.

    Capas:
    1. Estructural: integridad del grafo
    2. Semántico: coherencia de objetivos
    3. Dependencias: resolubilidad
    4. Precondiciones: factibilidad
    5. Ciclos: ausencia de ciclos
    6. Recursos: disponibilidad
    7. Constraints: cumplimiento de restricciones
    """

    def __init__(self):
        self._custom_validators: List[Callable[[ObjectiveGraph], List[ValidationIssue]]] = []

    def add_custom_validator(
        self,
        validator: Callable[[ObjectiveGraph], List[ValidationIssue]],
    ) -> None:
        """Añade un validador personalizado."""
        self._custom_validators.append(validator)

    def validate_graph(self, graph: ObjectiveGraph) -> ValidationReport:
        """
        Ejecuta todas las capas de validación sobre el grafo.

        Returns:
            ValidationReport con todos los issues encontrados.
        """
        report = ValidationReport()

        # Capa 1: Validación estructural
        self._validate_structure(graph, report)

        # Capa 2: Validación semántica
        self._validate_semantics(graph, report)

        # Capa 3: Validación de dependencias
        self._validate_dependency_resolution(graph, report)

        # Capa 4: Validación de precondiciones
        self._validate_preconditions(graph, report)

        # Capa 5: Detección de ciclos
        self._validate_cycles(graph, report)

        # Capa 6: Validación de recursos
        self._validate_resources(graph, report)

        # Capa 7: Validación de constraints
        self._validate_constraints(graph, report)

        # Capa 8: Validadores personalizados
        for validator in self._custom_validators:
            issues = validator(graph)
            for issue in issues:
                report.add_issue(issue)

        # Determinar si es auto-reparable
        report.repairable = all(e.auto_fixable for e in report.errors)
        if report.repairable:
            report.repair_actions = self._generate_repair_actions(graph, report)

        return report

    # ------------------------------------------------------------------
    # CAPAS DE VALIDACIÓN
    # ------------------------------------------------------------------

    def _validate_structure(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida la estructura del grafo."""
        # Verificar nodos huérfanos (sin conexiones)
        for node in graph.nodes.values():
            has_connections = (
                node.id in graph._adjacency or
                node.id in graph._reverse_adj or
                node.parent_id is not None or
                node.children_ids
            )
            if not has_connections and len(graph.nodes) > 1:
                report.add_issue(ValidationIssue(
                    severity="warning",
                    category="schema",
                    message=f"Nodo huérfano detectado: {node.id}",
                    node_id=node.id,
                    auto_fixable=True,
                    suggested_fix="Eliminar nodo o conectarlo al grafo",
                ))

        # Verificar consistencia de jerarquía
        for node in graph.nodes.values():
            if node.parent_id and node.parent_id not in graph.nodes:
                report.add_issue(ValidationIssue(
                    severity="error",
                    category="schema",
                    message=f"Nodo {node.id} referencia padre inexistente: {node.parent_id}",
                    node_id=node.id,
                    auto_fixable=True,
                    suggested_fix="Eliminar referencia de padre o crear nodo padre",
                ))

            for child_id in node.children_ids:
                if child_id not in graph.nodes:
                    report.add_issue(ValidationIssue(
                        severity="error",
                        category="schema",
                        message=f"Nodo {node.id} referencia hijo inexistente: {child_id}",
                        node_id=node.id,
                        auto_fixable=True,
                        suggested_fix="Eliminar referencia de hijo o crear nodo hijo",
                    ))

    def _validate_semantics(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida la semántica de los objetivos."""
        for node in graph.nodes.values():
            # Descripción vacía o muy corta
            if not node.description or len(node.description.strip()) < 5:
                report.add_issue(ValidationIssue(
                    severity="warning",
                    category="semantic",
                    message=f"Nodo {node.id} tiene descripción muy corta o vacía",
                    node_id=node.id,
                    auto_fixable=False,
                    suggested_fix="Añadir descripción detallada del objetivo",
                ))

            # Esfuerzo no razonable
            if node.estimated_effort > 1000:
                report.add_issue(ValidationIssue(
                    severity="warning",
                    category="semantic",
                    message=f"Nodo {node.id} tiene esfuerzo estimado muy alto ({node.estimated_effort})",
                    node_id=node.id,
                    auto_fixable=False,
                    suggested_fix="Descomponer en sub-tareas más pequeñas",
                ))

            # Objetivo sin postcondiciones
            if not node.postconditions and node.node_type in ("objective", "subgoal"):
                report.add_issue(ValidationIssue(
                    severity="warning",
                    category="semantic",
                    message=f"Nodo {node.id} no tiene postcondiciones definidas",
                    node_id=node.id,
                    auto_fixable=False,
                    suggested_fix="Definir criterios de éxito (postcondiciones)",
                ))

    def _validate_dependency_resolution(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida que todas las dependencias puedan resolverse."""
        for node in graph.nodes.values():
            deps = graph.get_dependencies(node.id)

            # Dependencia a nodo inexistente
            for edge in graph.edges:
                if edge.edge_type == EdgeType.DEPENDENCY:
                    if edge.source_id not in graph.nodes:
                        report.add_issue(ValidationIssue(
                            severity="error",
                            category="dependency",
                            message=f"Dependencia desde nodo inexistente: {edge.source_id}",
                            auto_fixable=True,
                            suggested_fix="Eliminar arista o crear nodo fuente",
                        ))

            # Dependencia circular indirecta (ya detectada en ciclos, pero verificamos aquí también)
            # Verificar que no hay dependencias a nodos en estado FAILED sin alternativa
            for dep in deps:
                if dep.state == NodeState.FAILED:
                    alts = graph.get_alternatives(dep.id)
                    if not alts:
                        report.add_issue(ValidationIssue(
                            severity="error",
                            category="dependency",
                            message=f"Nodo {node.id} depende de {dep.id} que ha fallado sin alternativas",
                            node_id=node.id,
                            auto_fixable=False,
                            suggested_fix="Añadir camino alternativo o replanificar",
                        ))

    def _validate_preconditions(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida la factibilidad de precondiciones."""
        for node in graph.nodes.values():
            for pre in node.preconditions:
                # Verificar que la precondición no es tautológicamente falsa
                if pre.lower() in ("false", "impossible", "never"):
                    report.add_issue(ValidationIssue(
                        severity="error",
                        category="precondition",
                        message=f"Nodo {node.id} tiene precondición imposible: {pre}",
                        node_id=node.id,
                        auto_fixable=False,
                        suggested_fix="Revisar y corregir la precondición",
                    ))

                # Verificar que la precondición puede ser satisfecha por algún nodo previo
                # (heurística simple: buscar postcondiciones que la satisfagan)
                can_be_satisfied = False
                deps = graph.get_dependencies(node.id)
                for dep in deps:
                    if any(pre in dep.postconditions for dep in deps):
                        can_be_satisfied = True
                        break

                if not can_be_satisfied and deps:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="precondition",
                        message=f"Precondición '{pre}' de {node.id} no es garantizada por dependencias",
                        node_id=node.id,
                        auto_fixable=False,
                        suggested_fix="Añadir nodo que produzca esta postcondición",
                    ))

    def _validate_cycles(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Detecta ciclos en el grafo de dependencias."""
        cycles = graph.detect_cycles()
        for cycle in cycles:
            report.add_issue(ValidationIssue(
                severity="error",
                category="cycle",
                message=f"Ciclo detectado: {' → '.join(cycle)}",
                auto_fixable=True,
                suggested_fix="Romper ciclo eliminando una dependencia",
            ))

    def _validate_resources(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida conflictos de recursos."""
        resource_usage: Dict[str, List[str]] = defaultdict(list)

        for node in graph.nodes.values():
            for res in node.required_resources:
                resource_usage[res].append(node.id)

        # Detectar recursos sobre-asignados en el mismo nivel paralelo
        levels = graph.parallel_levels()
        for level in levels:
            level_resources: Dict[str, List[str]] = defaultdict(list)
            for node_id in level:
                node = graph.nodes.get(node_id)
                if node:
                    for res in node.required_resources:
                        level_resources[res].append(node_id)

            for res, node_ids in level_resources.items():
                if len(node_ids) > 1:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="resource",
                        message=f"Recurso '{res}' solicitado por múltiples nodos paralelos: {node_ids}",
                        auto_fixable=False,
                        suggested_fix="Secuenciar tareas o aumentar capacidad del recurso",
                    ))

    def _validate_constraints(self, graph: ObjectiveGraph, report: ValidationReport) -> None:
        """Valida constraints del sistema."""
        # Verificar que no hay más de N niveles de anidamiento
        max_depth = 10
        for node in graph.nodes.values():
            depth = 0
            current = node
            while current.parent_id:
                depth += 1
                current = graph.nodes.get(current.parent_id)
                if depth > max_depth:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="semantic",
                        message=f"Nodo {node.id} excede profundidad máxima de anidamiento ({max_depth})",
                        node_id=node.id,
                        auto_fixable=False,
                        suggested_fix="Aplanar jerarquía o dividir en sub-grafos",
                    ))
                    break

        # Verificar que el grafo no excede tamaño máximo
        max_nodes = 1000
        if len(graph.nodes) > max_nodes:
            report.add_issue(ValidationIssue(
                severity="error",
                category="semantic",
                message=f"Grafo excede tamaño máximo: {len(graph.nodes)} > {max_nodes}",
                auto_fixable=False,
                suggested_fix="Dividir en sub-workflows o simplificar objetivo",
            ))

    # ------------------------------------------------------------------
    # AUTO-REPARACIÓN
    # ------------------------------------------------------------------

    def auto_repair(self, graph: ObjectiveGraph, report: ValidationReport) -> Optional[ObjectiveGraph]:
        """
        Intenta reparar automáticamente los errores auto-fixables del grafo.

        Returns:
            Nuevo grafo reparado, o None si no se pudo reparar.
        """
        if not report.repairable:
            return None

        # Crear copia del grafo para reparar
        repaired = ObjectiveGraph.from_dict(graph.to_dict())

        for action in report.repair_actions:
            action_type = action.get("type")

            if action_type == "remove_orphan":
                node_id = action["node_id"]
                if node_id in repaired.nodes:
                    repaired.remove_node(node_id)

            elif action_type == "remove_edge":
                source = action["source_id"]
                target = action["target_id"]
                repaired.edges = [e for e in repaired.edges 
                                 if not (e.source_id == source and e.target_id == target)]

            elif action_type == "add_missing_node":
                node_id = action["node_id"]
                # Crear nodo placeholder
                from objective_graph import ObjectiveNode
                placeholder = ObjectiveNode(
                    id=node_id,
                    description=f"Placeholder for {node_id}",
                    node_type="task",
                )
                repaired.add_node(placeholder)

        # Re-validar el grafo reparado
        new_report = self.validate_graph(repaired)
        if new_report.is_valid:
            return repaired

        return None

    def _generate_repair_actions(self, graph: ObjectiveGraph, report: ValidationReport) -> List[Dict[str, Any]]:
        """Genera acciones de reparación para los errores auto-fixables."""
        actions = []

        for issue in report.errors:
            if not issue.auto_fixable:
                continue

            if issue.category == "schema" and "huérfano" in issue.message:
                actions.append({
                    "type": "remove_orphan",
                    "node_id": issue.node_id,
                    "reason": issue.message,
                })

            elif issue.category == "cycle":
                # Encontrar la arista a romper (la última del ciclo)
                if issue.edge_ids:
                    actions.append({
                        "type": "remove_edge",
                        "source_id": issue.edge_ids[0][0],
                        "target_id": issue.edge_ids[0][1],
                        "reason": issue.message,
                    })

            elif issue.category == "schema" and "inexistente" in issue.message:
                # Extraer el ID del nodo faltante del mensaje
                actions.append({
                    "type": "add_missing_node",
                    "node_id": issue.node_id,
                    "reason": issue.message,
                })

        return actions

```
