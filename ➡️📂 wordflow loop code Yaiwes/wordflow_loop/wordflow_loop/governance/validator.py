from __future__ import annotations

from ..contracts import NodeContract


def check(node: NodeContract, completed_nodes: set[str]) -> list[str]:
    errors: list[str] = []
    missing = [dep for dep in node.depends_on if dep not in completed_nodes]
    if missing:
        errors.append("missing_dependencies:" + ",".join(missing))
    overlap = set(node.allowed_actions) & set(node.forbidden_actions)
    if overlap:
        errors.append("action_allow_deny_conflict:" + ",".join(sorted(overlap)))
    if node.mutation and not node.allowed_actions:
        errors.append("mutation_without_allowed_actions")
    return errors
