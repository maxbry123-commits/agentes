"""Tests für den ActionPlan → WorkflowDefinition Adapter."""

from __future__ import annotations

from cognithor.core.workflow_adapter import action_plan_to_workflow
from cognithor.core.workflow_schema import NodeType, WorkflowDefinition
from cognithor.models import ActionPlan, PlannedAction


class TestActionPlanToWorkflow:
    def test_basic_conversion(self) -> None:
        """Einfacher Plan mit 2 Steps wird korrekt konvertiert."""
        plan = ActionPlan(
            goal="test",
            steps=[
                PlannedAction(tool="read_file", params={"path": "/a"}),
                PlannedAction(tool="write_file", params={"path": "/b"}),
            ],
        )
        wf = action_plan_to_workflow(plan)

        assert isinstance(wf, WorkflowDefinition)
        assert len(wf.nodes) == 2
        assert wf.nodes[0].id == "step_0"
        assert wf.nodes[0].type == NodeType.TOOL
        assert wf.nodes[0].tool_name == "read_file"
        assert wf.nodes[1].tool_name == "write_file"

    def test_dependencies_mapped(self) -> None:
        """depends_on Indizes werden zu Node-IDs konvertiert."""
        plan = ActionPlan(
            goal="test",
            steps=[
                PlannedAction(tool="a", params={}),
                PlannedAction(tool="b", params={}, depends_on=[0]),
                PlannedAction(tool="c", params={}, depends_on=[0, 1]),
            ],
        )
        wf = action_plan_to_workflow(plan)

        assert wf.nodes[0].depends_on == []
        assert wf.nodes[1].depends_on == ["step_0"]
        assert wf.nodes[2].depends_on == ["step_0", "step_1"]

    def test_max_parallel_passed(self) -> None:
        """max_parallel wird an WorkflowDefinition durchgereicht."""
        plan = ActionPlan(goal="test", steps=[PlannedAction(tool="a", params={})])
        wf = action_plan_to_workflow(plan, max_parallel=8)
        assert wf.max_parallel == 8

    def test_tool_params_preserved(self) -> None:
        """Tool-Parameter werden vollständig übernommen."""
        plan = ActionPlan(
            goal="test",
            steps=[
                PlannedAction(
                    tool="http_request",
                    params={"url": "https://api.com", "method": "POST", "body": "{}"},
                ),
            ],
        )
        wf = action_plan_to_workflow(plan)
        assert wf.nodes[0].tool_params["url"] == "https://api.com"
        assert wf.nodes[0].tool_params["method"] == "POST"

    def test_empty_plan(self) -> None:
        """Leerer Plan ergibt leere Workflow-Definition."""
        plan = ActionPlan(goal="empty", steps=[])
        wf = action_plan_to_workflow(plan)
        assert len(wf.nodes) == 0
        assert wf.name == "empty"
