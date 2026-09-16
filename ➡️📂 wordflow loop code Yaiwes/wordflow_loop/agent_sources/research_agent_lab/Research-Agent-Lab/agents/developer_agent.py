from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.code_task import CodeTask
from tools.project_safety import ProjectSafetyPolicy


class DeveloperAgent(Agent):
    name = "developer_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plan = state.values.get("experiment_plans", [{}])[0]
        codebase = state.topic.codebase
        safety = ProjectSafetyPolicy.from_topic(state.topic)
        task = CodeTask(
            title=f"Implement plan: {plan.get('name', state.topic.topic_name)}",
            experiment_id=plan.get("experiment_id", ""),
            repository_path=str(codebase.get("repo_path", "")),
            allowed_paths=state.topic.allowed_auto_edit(),
            protected_paths=state.topic.protected_files(),
            proposed_files=plan.get("files_to_change", []),
            implementation_notes=[
                f"Goal: {plan.get('hypothesis', '')}",
                f"Change: {plan.get('modification', '')}",
                f"Files: {', '.join(plan.get('files_to_change', []))}",
                f"Baseline: {plan.get('baseline', '')}",
                "Read target repository before editing.",
                "Generate a narrow patch for one experiment only.",
                "Run the configured smoke test before full training.",
                "Create file backups before editing a non-git project copy.",
                "Keep long training and destructive cleanup behind human approval.",
            ],
            requires_human_approval=not bool(codebase.get("copy_can_modify", False)),
            dry_run_first=True,
            backup_required=safety.backup_required,
            safety_policy=safety.to_dict(),
        )
        context.artifact_store.save_json(state.run_id, "code_tasks", task.task_id, task)
        state.values["code_tasks"] = [asdict(task)]
        developer_mode = "explore_enabled" if codebase.get("exploration_mode") == "high" else "plan_only"
        return AgentResult(
            notes=[f"created developer task; mode={developer_mode}"],
            artifacts={"code_tasks": [task.task_id]},
            values={"developer_mode": developer_mode},
        )
