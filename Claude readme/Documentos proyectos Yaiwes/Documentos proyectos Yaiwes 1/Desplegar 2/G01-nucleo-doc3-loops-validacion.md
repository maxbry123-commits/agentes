# G1 · NÚCLEO DETERMINISTA — Documento 3/4
**Bloques B5 (Loops) + B6 (Tribunal/Validación) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 1/13, líneas 627-716, literal

---

## B5 · Loops

**N/A en este grupo.** Los 11 Loops (Long-Running Loop Engine) se activan a partir de G6. El Núcleo no ejecuta ningún loop — es la base sobre la que el motor de loops correrá más adelante. No se rellena con contenido inventado.

---

## B6 · Validación — tests reales (literal)

```python
# tests/test_state_machine.py

from workflow_core import (
    Goal,
    NodeDefinition,
    NodeStatus,
    WorkflowDefinition,
    WorkflowState,
    WorkflowStateMachine,
    WorkflowStatus,
)


def make_state() -> WorkflowState:
    definition = WorkflowDefinition(
        workflow_id="wf-001",
        name="test workflow",
        group="backend",
        goals=(
            Goal(
                goal_id="goal-001",
                description="Build backend",
            ),
        ),
        nodes=(
            NodeDefinition(
                node_id="node-001",
                name="Architecture",
                role="architecture",
            ),
            NodeDefinition(
                node_id="node-002",
                name="Execution",
                role="backend_primary_executor",
                dependencies=("node-001",),
            ),
        ),
    )

    return WorkflowState(definition=definition)


def test_workflow_transition() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_workflow(state, WorkflowStatus.READY)

    assert state.status == WorkflowStatus.READY


def test_node_transition() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_node(state, "node-001", NodeStatus.READY)

    assert state.node("node-001").status == NodeStatus.READY


def test_invalid_transition_is_rejected() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_workflow(state, WorkflowStatus.READY)
    state = machine.transition_workflow(state, WorkflowStatus.RUNNING)

    assert state.status == WorkflowStatus.RUNNING
```

**Criterio de aceptación de este bloque (regla transversal, ver `REGLAS-TRANSVERSALES.md`):** mismo input 100 veces → mismo resultado. Estos 3 tests son la primera evidencia verificable por máquina de esa propiedad — no hay LLM, agente, API, Temporal, GitHub, memoria, Docker ni servidor involucrado en ninguno de los tres.

---

*Siguiente: Documento 4/4 — B7 (Plan, con `events.py`/`store.py`/`__init__.py` restantes) + B8 (N/A).*
