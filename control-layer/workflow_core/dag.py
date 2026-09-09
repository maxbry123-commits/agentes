from dataclasses import dataclass, field
from typing import Mapping

from .contracts import NodeDefinition


@dataclass(frozen=True)
class DAGDefinition:
    dag_id: str
    workflow_id: str
    version: int
    nodes: tuple[NodeDefinition, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)
