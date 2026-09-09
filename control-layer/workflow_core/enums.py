from enum import Enum


class WorkflowStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class EventType(str, Enum):
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    NODE_CREATED = "node.created"
    NODE_STARTED = "node.started"
    NODE_PASSED = "node.passed"
    NODE_FAILED = "node.failed"

    CHECKPOINT_CREATED = "checkpoint.created"
    RECOVERY_STARTED = "recovery.started"

    CHANGE_PROPOSED = "change.proposed"
    DAG_PATCHED = "dag.patched"
