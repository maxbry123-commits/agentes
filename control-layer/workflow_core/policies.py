from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowPolicy:
    allowed_groups: frozenset[str]
    allowed_roles: frozenset[str]
    max_nodes: int = 500
    max_priority: int = 100
    require_dependencies: bool = True
    require_sheriff: bool = True
