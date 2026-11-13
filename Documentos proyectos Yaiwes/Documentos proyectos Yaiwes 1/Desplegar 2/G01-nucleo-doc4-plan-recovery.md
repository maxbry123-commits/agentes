# G1 · NÚCLEO DETERMINISTA — Documento 4/4
**Bloques B7 (Plan) + B8 (Recovery) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 1/13, líneas 242-624 + 718-791, literal

---

## B7 · Plan de despliegue (Modo A — el código ya existe, esto es orden de puesta en marcha)

Orden literal de la fuente: `enums → errors → contracts → events → state → state_machine → store → __init__ → tests`. Documentos 1-2-3 ya cubrieron enums/errors/contracts/state/state_machine/tests. Quedan `events.py`, `store.py`, `__init__.py` — se completan aquí:

```python
# events.py — fundamental para recuperación, auditoría, Hermes,
# observabilidad, memoria, y reconstrucción después de reinicio.

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping
from uuid import uuid4

from .enums import EventType


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    workflow_id: str
    sequence: int
    event_type: EventType
    timestamp: datetime
    payload: Mapping[str, object]

    @classmethod
    def create(
        cls,
        workflow_id: str,
        sequence: int,
        event_type: EventType,
        payload: Mapping[str, object],
    ) -> "WorkflowEvent":
        return cls(
            event_id=str(uuid4()),
            workflow_id=workflow_id,
            sequence=sequence,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload=dict(payload),
        )
```

```python
# store.py — almacenamiento en memoria para esta primera implementación.
# La interfaz queda preparada para sustituirse por SQLite/PostgreSQL
# (conecta directo con la Sección 5 de la Base de Datos externa del
# Memory Engine, Decisión 05 del checkpoint de topología).

from abc import ABC, abstractmethod

from .errors import DuplicateEventError
from .events import WorkflowEvent
from .state import WorkflowState


class WorkflowStore(ABC):

    @abstractmethod
    def save_state(self, state: WorkflowState) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_state(self, workflow_id: str) -> WorkflowState | None:
        raise NotImplementedError

    @abstractmethod
    def append_event(self, event: WorkflowEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def events(self, workflow_id: str) -> tuple[WorkflowEvent, ...]:
        raise NotImplementedError


class InMemoryWorkflowStore(WorkflowStore):

    def __init__(self) -> None:
        self._states: dict[str, WorkflowState] = {}
        self._events: dict[str, list[WorkflowEvent]] = {}
        self._event_ids: set[str] = set()

    def save_state(self, state: WorkflowState) -> None:
        self._states[state.definition.workflow_id] = state

    def load_state(self, workflow_id: str) -> WorkflowState | None:
        return self._states.get(workflow_id)

    def append_event(self, event: WorkflowEvent) -> None:
        if event.event_id in self._event_ids:
            raise DuplicateEventError(f"Event already exists: {event.event_id}")

        self._event_ids.add(event.event_id)
        self._events.setdefault(event.workflow_id, []).append(event)

    def events(self, workflow_id: str) -> tuple[WorkflowEvent, ...]:
        return tuple(self._events.get(workflow_id, []))
```

```python
# __init__.py
from .contracts import (
    Checkpoint, ChangeProposal, Failure, Goal,
    NodeDefinition, NodeRuntime, WorkflowDefinition,
)
from .enums import EventType, NodeStatus, WorkflowStatus
from .events import WorkflowEvent
from .state import WorkflowState
from .state_machine import WorkflowStateMachine
from .store import InMemoryWorkflowStore, WorkflowStore

__all__ = [
    "Checkpoint", "ChangeProposal", "Failure", "Goal",
    "NodeDefinition", "NodeRuntime", "WorkflowDefinition",
    "EventType", "NodeStatus", "WorkflowStatus",
    "WorkflowEvent", "WorkflowState", "WorkflowStateMachine",
    "WorkflowStore", "InMemoryWorkflowStore",
]
```

**Paquete completo — los 9 archivos de G1 ya cubiertos entre los 4 documentos:**
`pyproject.toml`(Doc1) · `enums.py·errors.py`(Doc2) · `contracts.py`(Doc2) · `state.py·state_machine.py`(Doc2) · `events.py·store.py·__init__.py`(este doc) · `test_state_machine.py`(Doc3)

---

## B8 · Recovery

**N/A en este grupo.** El Sistema de Recuperación completo (Failure/Recovery/Checkpoint/Watchdog/Resume) es G7, construido después de la Capa de Control (G4-G5). El Núcleo solo deja preparado el terreno: `Checkpoint` ya existe como contrato (`workflow_id, sequence, state_version, state_hash`), y `WorkflowStatus.RECOVERING` ya existe como estado válido — pero la lógica de recuperación en sí no se construye aquí.

---

## Cierre de G1

Propiedad conseguida: **mismo estado + misma transición = mismo resultado**, sin depender de LLM, agente, API, Temporal, GitHub, memoria, Docker, ni servidor — verificable por los 3 tests del Documento 3.

Prepara directamente: G3(DAG) recibe `contracts.py`+`state_machine.py` como base · G4-G5(Capa de Control) recibe todos los contratos para construir el Sheriff encima · G7(Recuperación) recibe `Checkpoint` y `WorkflowStatus.RECOVERING` ya definidos.

---

*G1 completo — 4/4 documentos. Siguiente en el orden confirmado: G2 — Research Engine.*
