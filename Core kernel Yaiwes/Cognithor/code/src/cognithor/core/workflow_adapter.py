"""Adapter: ActionPlan → WorkflowDefinition.

Bridges the PGE-style ActionPlan/PlannedAction model with the
WorkflowEngine's WorkflowDefinition/WorkflowNode schema, allowing
the DAG WorkflowEngine to execute standard PGE action plans.

Usage::

    from cognithor.core.workflow_adapter import action_plan_to_workflow

    workflow = action_plan_to_workflow(plan)
    run = await engine.execute(workflow)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cognithor.core.workflow_schema import (
    NodeType,
    WorkflowDefinition,
    WorkflowNode,
)

if TYPE_CHECKING:
    from cognithor.models import ActionPlan


def action_plan_to_workflow(
    plan: ActionPlan,
    *,
    max_parallel: int = 4,
    global_timeout_seconds: int = 600,
) -> WorkflowDefinition:
    """Convert an ActionPlan to a WorkflowDefinition for the DAG engine.

    Each PlannedAction becomes a WorkflowNode of type TOOL.
    ``depends_on`` indices are mapped to node ID strings.

    Args:
        plan: The PGE action plan to convert.
        max_parallel: Max parallel concurrent nodes.
        global_timeout_seconds: Overall workflow timeout.

    Returns:
        WorkflowDefinition ready for WorkflowEngine.execute().
    """
    nodes: list[WorkflowNode] = []
    for i, step in enumerate(plan.steps):
        node_id = f"step_{i}"
        deps = [f"step_{d}" for d in (step.depends_on or [])]
        node = WorkflowNode(
            id=node_id,
            type=NodeType.TOOL,
            name=step.tool,
            description=f"PGE step {i}: {step.tool}",
            tool_name=step.tool,
            tool_params={k: v for k, v in step.params.items() if k != "_timeout"},
            depends_on=deps,
            timeout_seconds=step.params.get("_timeout", 60),
        )
        nodes.append(node)

    return WorkflowDefinition(
        name=plan.goal or "PGE ActionPlan",
        description=f"Auto-converted from ActionPlan: {plan.goal}",
        nodes=nodes,
        max_parallel=max_parallel,
        global_timeout_seconds=global_timeout_seconds,
    )
