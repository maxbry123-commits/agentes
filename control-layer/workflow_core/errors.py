class WorkflowError(Exception):
    """Base error for deterministic workflow operations."""


class InvalidTransitionError(WorkflowError):
    """Raised when a state transition is not allowed."""


class ContractViolationError(WorkflowError):
    """Raised when a workflow contract is invalid."""


class DuplicateEventError(WorkflowError):
    """Raised when an event with an existing ID is inserted."""


class VersionConflictError(WorkflowError):
    """Raised when optimistic state versioning detects stale state."""
