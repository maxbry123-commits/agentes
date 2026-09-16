from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.experiment_decision import ExperimentDecision


class ExperimentDecisionAgent(Agent):
    name = "experiment_decision"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        results = state.values.get("experiment_results") or []
        plans = state.values.get("experiment_plans", [{}])

        if not results:
            experiment_id = plans[0].get("experiment_id", "unknown") if plans else "unknown"
            decision = ExperimentDecision(
                experiment_id=experiment_id,
                action="hold",
                reason="no experiment results to evaluate",
                suggestion="run AutonomousExperimentAgent to execute smoke tests",
                notes=["no results found in state"],
            )
            context.artifact_store.save_json(state.run_id, "experiment_decisions", decision.decision_id, decision)
            state.values["experiment_decision"] = asdict(decision)
            state.values["experiment_decisions"] = {experiment_id: asdict(decision)}
            return AgentResult(
                notes=[f"decision: action={decision.action}, reason={decision.reason[:120]}"],
                artifacts={"experiment_decisions": [decision.decision_id]},
                values={
                    "experiment_decision": asdict(decision),
                    "experiment_decisions": {experiment_id: asdict(decision)},
                },
            )

        # Group results by experiment_id for per-node decisions
        results_by_exp: dict[str, list[dict]] = {}
        for r in results:
            if isinstance(r, dict):
                eid = r.get("experiment_id", "unknown")
                results_by_exp.setdefault(eid, []).append(r)

        all_decisions: dict[str, dict] = {}
        all_decision_ids: list[str] = []
        first_decision: dict | None = None

        for exp_id, exp_results in results_by_exp.items():
            result_ids = [r.get("result_id", "") for r in exp_results if isinstance(r, dict)]
            decision = self._decide(exp_id, exp_results, result_ids)
            decision_dict = asdict(decision)
            all_decisions[exp_id] = decision_dict
            all_decision_ids.append(decision.decision_id)
            if first_decision is None:
                first_decision = decision_dict
            context.artifact_store.save_json(state.run_id, "experiment_decisions", decision.decision_id, decision)

        if first_decision is None:
            first_decision = {}

        summary = state.values.get("orchestrator_summary")
        if isinstance(summary, dict) and first_decision:
            debug_rounds = summary.get("debug_rounds", 0)
            if debug_rounds > 0:
                first_decision["notes"] = first_decision.get("notes", []) + [
                    f"orchestrator: {debug_rounds} debug round(s) used"
                ]

        state.values["experiment_decision"] = first_decision
        state.values["experiment_decisions"] = all_decisions

        action_summary = ", ".join(
            f"{eid}={d.get('action', '?')}" for eid, d in all_decisions.items()
        )
        return AgentResult(
            notes=[f"decisions: {action_summary}"],
            artifacts={"experiment_decisions": all_decision_ids},
            values={
                "experiment_decision": first_decision,
                "experiment_decisions": all_decisions,
            },
        )

    def _decide(
        self,
        experiment_id: str,
        results: list[dict],
        result_ids: list[str],
    ) -> ExperimentDecision:
        statuses = [r.get("status", "unknown") for r in results if isinstance(r, dict)]
        errors = [r for r in results if r.get("status") == "error"]
        failures = [r for r in results if r.get("status") == "failed"]
        passed = [r for r in results if r.get("status") == "passed"]
        unparsed = [r for r in results if r.get("status") == "unparsed"]

        if errors:
            return ExperimentDecision(
                experiment_id=experiment_id,
                action="investigate",
                reason=f"{len(errors)} smoke command(s) returned errors",
                based_on_result_ids=result_ids,
                suggestion="Check error_message in each ExperimentResult; fix environment or config before retry",
                notes=[_result_summary(results)],
            )

        if failures:
            return ExperimentDecision(
                experiment_id=experiment_id,
                action="rollback",
                reason=f"{len(failures)} smoke run(s) detected failure signals",
                based_on_result_ids=result_ids,
                suggestion="Review log_tail in failed results; revert changes and re-plan before retry",
                notes=[_result_summary(results)],
            )

        # Check unparsed before passed: a single unparsed result should prevent
        # a blind "continue" even when other commands in the same experiment passed.
        if unparsed:
            return ExperimentDecision(
                experiment_id=experiment_id,
                action="investigate",
                reason=f"{len(unparsed)} result(s) could not be parsed",
                based_on_result_ids=result_ids,
                suggestion="Check log_tail manually; the output format may not match expected metric patterns",
                notes=[_result_summary(results)],
            )

        if passed:
            metrics_note = ", ".join(
                f"{k}={v}" for r in passed for k, v in sorted(r.get("metrics", {}).items())
            )
            return ExperimentDecision(
                experiment_id=experiment_id,
                action="continue",
                reason=f"all {len(passed)} smoke command(s) passed",
                based_on_result_ids=result_ids,
                suggestion=(
                    "Smoke tests passed. Consider full-training eval with same config, "
                    "then compare metrics against baseline before declaring improvement."
                ),
                notes=[metrics_note] if metrics_note else [],
            )

        return ExperimentDecision(
            experiment_id=experiment_id,
            action="hold",
            reason="unexpected result statuses",
            based_on_result_ids=result_ids,
            suggestion="Review all experiment results manually",
            notes=[_result_summary(results)],
        )


def _result_summary(results: list[dict]) -> str:
    parts: list[str] = []
    for r in results:
        if not isinstance(r, dict):
            continue
        s = r.get("status", "?")
        m = r.get("metrics", {})
        if m:
            parts.append(f"{s}: {m}")
        else:
            parts.append(s)
    return "; ".join(parts)
