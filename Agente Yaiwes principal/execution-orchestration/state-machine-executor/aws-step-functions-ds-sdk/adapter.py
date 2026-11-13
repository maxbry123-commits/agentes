from __future__ import annotations

from typing import Any


def graph_to_dict(branch: Any) -> dict[str, Any]:
    """Compile a Step Functions State/Chain into deterministic ASL dictionary form."""
    from stepfunctions.steps import Graph
    return Graph(branch).to_dict()


def graph_to_json(branch: Any, pretty: bool = False) -> str:
    """Compile a Step Functions State/Chain into ASL JSON."""
    from stepfunctions.steps import Graph
    return Graph(branch).to_json(pretty=pretty)


def workflow_factory(name: str, definition: Any, role: str, **kwargs: Any) -> Any:
    """Create a Workflow without importing boto3/stepfunctions at adapter import time."""
    from stepfunctions.workflow import Workflow
    return Workflow(name=name, definition=definition, role=role, **kwargs)
