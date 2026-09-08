from __future__ import annotations


NON_TERMINAL_STATES = (
    "intake",
    "plan",
    "critique-plan",
    "queue-tasks",
    "execute-task",
    "verify",
    "repair",
    "replan",
    "approval-wait",
)
TERMINAL_MARKER = "terminal"
ALL_STATES = NON_TERMINAL_STATES + (TERMINAL_MARKER,)


_ACTIVE_EDGES = (
    ("intake", "plan"),
    ("plan", "critique-plan"),
    ("critique-plan", "queue-tasks"),
    ("queue-tasks", "execute-task"),
    ("execute-task", "verify"),
    ("verify", "execute-task"),
    ("verify", "repair"),
    ("repair", "verify"),
    ("repair", "replan"),
    ("replan", "queue-tasks"),
)
_APPROVAL_RESUME_TARGETS = (
    "plan",
    "critique-plan",
    "queue-tasks",
    "execute-task",
    "verify",
    "repair",
    "replan",
)


def legal_targets(state: object) -> tuple[str, ...]:
    """Return canonical state-changing targets in canonical vocabulary order."""
    if state not in ALL_STATES or state == TERMINAL_MARKER:
        return ()

    def is_target(candidate: str) -> bool:
        if candidate == state:
            return False
        if candidate == TERMINAL_MARKER:
            return True
        if candidate == "approval-wait" and state != "intake":
            return True
        if state == "approval-wait" and candidate in _APPROVAL_RESUME_TARGETS:
            return True
        return (state, candidate) in _ACTIVE_EDGES

    return tuple(candidate for candidate in ALL_STATES if is_target(candidate))


def is_legal_transition(old: object, new: object) -> bool:
    """Check known-state adjacency; unknown endpoints deliberately fail open."""
    if old not in ALL_STATES or new not in ALL_STATES:
        return True
    if old == new:
        return True
    return new in legal_targets(old)
