# G3 · DAG Y SHERIFF DETERMINISTA — Documento 3/4
**Bloques B5 (N/A) + B6 (Validación: tests + frontera) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 2/13, líneas 1296-1382, literal

---

## B5 · Loops

**N/A en este grupo.** Los loops se construyen en G6 (Long-Running Loop + Goals + Council), que consumirá este DAG ya validado como su base de ejecución.

---

## B6 · Validación — tests + frontera Control Plane / Execution

DAG válido:

```python
from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.dag import DAGValidator


def test_valid_dag() -> None:
    dag = DAGDefinition(
        dag_id="dag-001",
        workflow_id="wf-001",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="A", role="architecture"),
            NodeDefinition(
                node_id="b", name="B",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )

    DAGValidator().validate(dag)
```

Ciclo rechazado:

```python
import pytest

from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.dag import DAGValidator
from workflow_core.errors import ContractViolationError


def test_cycle_is_rejected() -> None:
    dag = DAGDefinition(
        dag_id="dag-cycle",
        workflow_id="wf-001",
        version=1,
        nodes=(
            NodeDefinition(
                node_id="a", name="A", role="architecture",
                dependencies=("b",),
            ),
            NodeDefinition(
                node_id="b", name="B",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )

    with pytest.raises(ContractViolationError):
        DAGValidator().validate(dag)
```

Frontera definida desde esta salida (regla que gobierna todo lo que viene después):

```
CONTROL PLANE
──────────────────────────────────
Goals · DAG · Policies · Sheriff
State · Patches · Checkpoints
──────────────────────────────────
              EXECUTION
```

Los agentes todavía no están aquí — llegan en G8 (Agent Registry + Universal Harness).

---

*Siguiente: Documento 4/4 — B7 (origen y contrato estricto de los cambios) + B8 (DAG Patch — modificación sin reconstruir).*
