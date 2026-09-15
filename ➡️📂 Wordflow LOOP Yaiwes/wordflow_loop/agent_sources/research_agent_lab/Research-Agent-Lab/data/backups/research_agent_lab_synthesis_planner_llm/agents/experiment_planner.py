from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.experiment_plan import ExperimentPlan


class ExperimentPlannerAgent(Agent):
    name = "experiment_planner"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        opportunity = state.values.get("opportunities", [{}])[0]
        codebase_report = state.values.get("codebase_report", {})
        allowed_files = codebase_report.get("suggested_first_patch_files") or state.topic.allowed_auto_edit()
        plan = ExperimentPlan(
            name=opportunity.get("title", f"First experiment for {state.topic.topic_name}"),
            hypothesis=opportunity.get("hypothesis", ""),
            baseline=self._baseline_hint(state),
            modification=opportunity.get("technical_strategy", ""),
            files_to_change=allowed_files,
            dataset=str(state.topic.current_status.get("dataset", "")),
            training_config={
                "mode": "smoke-first",
                "epochs": state.topic.current_status.get("default_epochs", "to_confirm"),
                "batch_size": state.topic.current_status.get("default_batch_size", "to_confirm"),
            },
            metrics=state.topic.experiment_metrics,
            ablation_studies=[
                "baseline unchanged",
                "minimal modification enabled",
                "modification disabled with same config",
            ],
            acceptance_criteria={
                "must_run": True,
                "requires_human_approval_before_code_edit": True,
                "metric_check": "compare against baseline on the same split",
                "no_data_leakage": True,
            },
            rollback_plan="keep changes as a reviewable patch; do not auto-commit",
        )
        context.artifact_store.save_json(state.run_id, "experiment_plans", plan.experiment_id, plan)
        state.values["experiment_plans"] = [asdict(plan)]
        return AgentResult(
            notes=["created controlled experiment plan"],
            artifacts={"experiment_plans": [plan.experiment_id]},
            values={"experiment_plan_count": 1},
        )

    def _baseline_hint(self, state: ResearchState) -> str:
        baselines = state.topic.current_status.get("baseline_methods", [])
        if isinstance(baselines, list) and baselines:
            return ", ".join(str(item) for item in baselines)
        return str(state.topic.current_status.get("baseline", "current baseline"))
