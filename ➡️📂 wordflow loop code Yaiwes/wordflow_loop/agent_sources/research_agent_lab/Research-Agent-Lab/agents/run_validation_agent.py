from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from tools.run_artifact_validator import report_to_dict, validate_run_dir


class RunValidationAgent(Agent):
    name = "run_validation_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        run_dir = context.artifact_store.run_dir(state.run_id)
        report = validate_run_dir(
            run_dir,
            expect_completed=False,
            settings=context.settings,
        )
        payload = report_to_dict(report)
        context.artifact_store.save_json(
            state.run_id,
            "run_validations",
            report.validation_id,
            payload,
        )
        state.values["run_validation"] = payload
        state.values["run_validation_status"] = report.status
        state.values["run_validation_score"] = report.score
        return AgentResult(
            notes=[f"run validation status={report.status} score={report.score}"],
            artifacts={"run_validations": [report.validation_id]},
            values={
                "run_validation": payload,
                "run_validation_status": report.status,
                "run_validation_score": report.score,
            },
        )
