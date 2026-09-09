from dataclasses import dataclass, replace
from typing import Mapping

from .contracts import NodeDefinition
from .dag import DAGDefinition
from .errors import VersionConflictError


@dataclass(frozen=True)
class DAGPatch:
    patch_id: str
    base_version: int
    add_nodes: tuple[NodeDefinition, ...] = ()
    remove_nodes: tuple[str, ...] = ()
    replace_nodes: tuple[NodeDefinition, ...] = ()
    metadata_updates: Mapping[str, str] = ()


class DAGPatchEngine:

    def apply(self, dag: DAGDefinition, patch: DAGPatch) -> DAGDefinition:

        if patch.base_version != dag.version:
            raise VersionConflictError(
                f"Patch based on version {patch.base_version}, "
                f"current version is {dag.version}"
            )

        nodes = {node.node_id: node for node in dag.nodes}

        for node_id in patch.remove_nodes:
            nodes.pop(node_id, None)

        for node in patch.replace_nodes:
            nodes[node.node_id] = node

        for node in patch.add_nodes:
            if node.node_id in nodes:
                raise VersionConflictError(f"Node already exists: {node.node_id}")
            nodes[node.node_id] = node

        metadata = dict(dag.metadata)
        metadata.update(dict(patch.metadata_updates))

        return replace(
            dag,
            version=dag.version + 1,
            nodes=tuple(nodes.values()),
            metadata=metadata,
        )
