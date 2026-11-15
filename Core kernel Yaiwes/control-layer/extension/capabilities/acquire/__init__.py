"""acquire · generic autonomous acquisition motor for OpenClaw kernel.

Phase 0: infrastructure only (queue, checkpoint, lock, journal, memory ops,
stop_policy, run_loop skeleton). Zero network. Zero project-specific logic.
"""

from .schema import (
    SCHEMA_VERSION,
    TERMINAL_STATUSES,
    TASK_STATUSES,
    MissionStatus,
    QueueEntry,
    Checkpoint,
    MemoryOps,
    JournalEvent,
    StopPolicy,
)

__all__ = [
    "SCHEMA_VERSION",
    "TERMINAL_STATUSES",
    "TASK_STATUSES",
    "MissionStatus",
    "QueueEntry",
    "Checkpoint",
    "MemoryOps",
    "JournalEvent",
    "StopPolicy",
]
