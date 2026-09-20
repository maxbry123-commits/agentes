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
