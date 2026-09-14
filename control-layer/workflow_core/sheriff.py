from dataclasses import dataclass
from typing import Mapping, Protocol

from .dag import DAGDefinition
from .policies import WorkflowPolicy


@dataclass(frozen=True)
class SheriffDecision:
    allowed: bool
    reason: str
    violations: tuple[str, ...] = ()


class SheriffContract(Protocol):

    def inspect(
        self,
        dag: DAGDefinition,
        context: Mapping[str, object],
    ) -> SheriffDecision:
        ...


class DeterministicSheriff:

    def __init__(self, policy: WorkflowPolicy) -> None:
        self.policy = policy

    def inspect(self, dag: DAGDefinition, context: Mapping[str, object]) -> SheriffDecision:
        violations: list[str] = []
        group = context.get("group")

        if group not in self.policy.allowed_groups:
            violations.append(f"group '{group}' is not allowed")

        if len(dag.nodes) > self.policy.max_nodes:
            violations.append(f"DAG exceeds maximum nodes: {self.policy.max_nodes}")

        for node in dag.nodes:
            if node.role not in self.policy.allowed_roles:
                violations.append(f"role '{node.role}' is not allowed")

            if not 0 <= node.priority <= self.policy.max_priority:
                violations.append(f"invalid priority for node '{node.node_id}'")

            if (
                self.policy.require_dependencies
                and node.node_id != dag.nodes[0].node_id
                and not node.dependencies
            ):
                violations.append(f"node '{node.node_id}' has no dependency")

        if violations:
            return SheriffDecision(
                allowed=False,
                reason="DAG rejected by Sheriff",
                violations=tuple(violations),
            )

        return SheriffDecision(allowed=True, reason="DAG approved")
