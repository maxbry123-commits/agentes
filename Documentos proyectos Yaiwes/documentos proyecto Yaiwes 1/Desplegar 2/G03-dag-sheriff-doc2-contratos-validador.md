# G3 · DAG Y SHERIFF DETERMINISTA — Documento 2/4
**Bloques B3 (Contratos) + B4 (Validator + Sheriff determinista) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 2/13, líneas 838-1072, literal

---

## B3 · dag.py + sheriff.py (contratos) + policies.py

```python
# dag.py
from dataclasses import dataclass, field
from typing import Mapping

from .contracts import NodeDefinition


@dataclass(frozen=True)
class DAGDefinition:
    dag_id: str
    workflow_id: str
    version: int
    nodes: tuple[NodeDefinition, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)
```

El Sheriff no ejecuta — autoriza o rechaza:

```python
# sheriff.py
from dataclasses import dataclass
from typing import Mapping, Protocol

from .dag import DAGDefinition


@dataclass(frozen=True)
class SheriffDecision:
    allowed: bool
    reason: str
    violations: tuple[str, ...] = ()


class SheriffContract(Protocol):

    def inspect(
        self,
        dag: DAGDefinition,
        context: Mapping[str, object],
    ) -> SheriffDecision:
        ...
```

Las reglas no quedan hardcodeadas dentro del Sheriff — viven en políticas separadas:

```python
# policies.py
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowPolicy:
    allowed_groups: frozenset[str]
    allowed_roles: frozenset[str]
    max_nodes: int = 500
    max_priority: int = 100
    require_dependencies: bool = True
    require_sheriff: bool = True
```

Ejemplo real de política:

```python
backend_policy = WorkflowPolicy(
    allowed_groups=frozenset({"backend"}),
    allowed_roles=frozenset({
        "architecture",
        "backend_primary_executor",
        "backend_recovery",
        "backend_repair",
        "backend_final_repair",
    }),
)
```

---

## B4 · DAG Validator + Sheriff determinista (implementación real)

```python
from .errors import ContractViolationError


class DAGValidator:

    def validate(self, dag: DAGDefinition) -> None:
        self._validate_unique_nodes(dag)
        self._validate_dependencies(dag)
        self._validate_no_cycles(dag)

    def _validate_unique_nodes(self, dag: DAGDefinition) -> None:
        ids = [node.node_id for node in dag.nodes]
        if len(ids) != len(set(ids)):
            raise ContractViolationError("DAG contains duplicated node IDs")

    def _validate_dependencies(self, dag: DAGDefinition) -> None:
        node_ids = {node.node_id for node in dag.nodes}
        for node in dag.nodes:
            for dependency in node.dependencies:
                if dependency not in node_ids:
                    raise ContractViolationError(
                        f"Node '{node.node_id}' depends on unknown node '{dependency}'"
                    )

    def _validate_no_cycles(self, dag: DAGDefinition) -> None:
        graph = {node.node_id: node.dependencies for node in dag.nodes}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ContractViolationError(f"DAG cycle detected at '{node_id}'")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in graph[node_id]:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in graph:
            visit(node_id)
```
Esto garantiza que no se pueda introducir accidentalmente `A → B → C → A`.

```python
from typing import Mapping

from .dag import DAGDefinition
from .policies import WorkflowPolicy
from .sheriff import SheriffDecision


class DeterministicSheriff:

    def __init__(self, policy: WorkflowPolicy) -> None:
        self.policy = policy

    def inspect(self, dag: DAGDefinition, context: Mapping[str, object]) -> SheriffDecision:
        violations: list[str] = []
        group = context.get("group")

        if group not in self.policy.allowed_groups:
            violations.append(f"group '{group}' is not allowed")

        if len(dag.nodes) > self.policy.max_nodes:
            violations.append(f"DAG exceeds maximum nodes: {self.policy.max_nodes}")

        for node in dag.nodes:
            if node.role not in self.policy.allowed_roles:
                violations.append(f"role '{node.role}' is not allowed")

            if not 0 <= node.priority <= self.policy.max_priority:
                violations.append(f"invalid priority for node '{node.node_id}'")

            if (
                self.policy.require_dependencies
                and node.node_id != dag.nodes[0].node_id
                and not node.dependencies
            ):
                violations.append(f"node '{node.node_id}' has no dependency")

        if violations:
            return SheriffDecision(
                allowed=False,
                reason="DAG rejected by Sheriff",
                violations=tuple(violations),
            )

        return SheriffDecision(allowed=True, reason="DAG approved")
```

Flujo: `DAG → DAG Validator → OK? → [NO→rechazo | SÍ→Sheriff→policy→DENY/ALLOW]`. Ningún ejecutor recibe un DAG que no haya pasado ambas validaciones.

---

*Siguiente: Documento 3/4 — B5 (N/A) + B6 (tests + frontera Control Plane/Execution).*
