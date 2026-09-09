from dataclasses import dataclass, replace
from typing import Mapping

from .contracts import NodeRuntime, WorkflowDefinition
from .enums import NodeStatus, WorkflowStatus


@dataclass(frozen=True)
class WorkflowState:
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.CREATED
    version: int = 0
    sequence: int = 0
    nodes: Mapping[str, NodeRuntime] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.nodes is None:
            object.__setattr__(
                self,
                "nodes",
                {
                    node.node_id: NodeRuntime(node_id=node.node_id)
                    for node in self.definition.nodes
                },
            )

    def with_status(self, status: WorkflowStatus) -> "WorkflowState":
        return replace(self, status=status, version=self.version + 1)

    def with_node(self, runtime: NodeRuntime) -> "WorkflowState":
        updated = dict(self.nodes)
        updated[runtime.node_id] = runtime
        return replace(self, nodes=updated, version=self.version + 1)

    def next_sequence(self) -> "WorkflowState":
        return replace(self, sequence=self.sequence + 1)

    def node(self, node_id: str) -> NodeRuntime:
        return self.nodes[node_id]

    def all_nodes_passed(self) -> bool:
        return all(
            node.status == NodeStatus.PASSED
            for node in self.nodes.values()
        )
