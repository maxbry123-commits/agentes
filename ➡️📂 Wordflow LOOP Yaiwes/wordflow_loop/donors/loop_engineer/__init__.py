"""Loop Contract Core for loop-engineer.

This package is intentionally small and stdlib-first: it validates the portable
repo-OS loop contract that the Claude Code plugin scaffolds and the verifier
scripts consume.
"""

from .paths import LoopPaths, resolve_loop_paths
from .contract import TERMINAL_STATES, VALIDATION_MODES, doctor_report, validate_contract
from .events import EVENT_SCHEMA_ID, EVENT_TYPES, EventStore, SQLiteEventStore, validate_event
from .plan import PLAN_SCHEMA_ID, TASK_KINDS, validate_plan
from .reducer import reduce_events

__all__ = [
    "EVENT_SCHEMA_ID",
    "EVENT_TYPES",
    "EventStore",
    "LoopPaths",
    "PLAN_SCHEMA_ID",
    "SQLiteEventStore",
    "TASK_KINDS",
    "TERMINAL_STATES",
    "VALIDATION_MODES",
    "doctor_report",
    "resolve_loop_paths",
    "reduce_events",
    "validate_contract",
    "validate_event",
    "validate_plan",
]
