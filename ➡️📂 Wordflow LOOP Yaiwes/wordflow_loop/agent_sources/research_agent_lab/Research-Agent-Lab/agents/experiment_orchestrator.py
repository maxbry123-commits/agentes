from __future__ import annotations
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from agents.code_writer import CodeWriterAgent
from agents.autonomous_experiment import AutonomousExperimentAgent
from agents.auto_debugger import AutoDebuggerAgent


class ExperimentOrchestratorAgent(Agent):
    name = "experiment_orchestrator"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        enable_experiments = bool(context.settings.get("enable_experiments"))
        if not enable_experiments:
            state.values["experiment_results"] = []
            return AgentResult(notes=["orchestrator: skipped (enable_experiments=False)"], values={"experiment_results": []})

        plans = state.values.get("experiment_plans", []) or []
        if not plans:
            state.values["experiment_results"] = []
            return AgentResult(notes=["orchestrator: no experiment plans"], values={"experiment_results": []})

        all_patches: list[dict] = []
        all_results: list[dict] = []
        all_debug_ids: list[str] = []
        total_debug_rounds = 0
        max_debug_attempts = int(context.settings.get("max_debug_attempts", 3))

        cw = CodeWriterAgent()
        ae = AutonomousExperimentAgent()
        ad = AutoDebuggerAgent()

        state.values["code_patches_by_experiment_id"] = state.values.get("code_patches_by_experiment_id", {})
        state.values["pending_fixes_by_experiment_id"] = state.values.get("pending_fixes_by_experiment_id", {})
        state.values["last_debug_records_by_experiment_id"] = state.values.get("last_debug_records_by_experiment_id", {})

        for plan in plans:
            if not isinstance(plan, dict):
                continue
            experiment_id = plan.get("experiment_id", "unknown")

            # Clear per-experiment stale state from previous runs
            state.values["pending_fixes_by_experiment_id"].pop(experiment_id, None)
            state.values["last_debug_records_by_experiment_id"].pop(experiment_id, None)

            for attempt in range(max_debug_attempts + 1):
                state.values["orchestrator_attempt"] = attempt

                # Step A: CodeWriter
                state.values["experiment_plans"] = [plan]
                cw.run(state, context)

                patches = state.values.get("code_patches_by_experiment_id", {})
                patch = patches.get(experiment_id, {})
                if patch.get("status") == "blocked":
                    all_patches.append(patch)
                    break

                # Step B: AutonomousExperiment
                ae_results = ae.run_single_plan(state, context, plan, patch, attempt)
                all_results.extend(ae_results)

                # Step C: Check results
                failed = [r for r in ae_results if r.get("status") in ("error", "failed")]
                if not failed:
                    all_patches.append(patch)
                    break

                if attempt >= max_debug_attempts:
                    all_patches.append(patch)
                    break

                # Step D: AutoDebugger
                ad.run(state, context)
                records = state.values.get("last_debug_records_by_experiment_id", {})
                record = records.get(experiment_id, {})
                if record.get("fix_file_contents"):
                    state.values.setdefault("pending_fixes_by_experiment_id", {})[experiment_id] = record["fix_file_contents"]
                    total_debug_rounds += 1
                    all_debug_ids.append(record.get("record_id", ""))
                else:
                    all_patches.append(patch)
                    break

        # Restore plans and write final state
        state.values["experiment_plans"] = plans
        state.values["experiment_results"] = all_results
        state.values["all_code_patches"] = all_patches
        state.values["all_experiment_results"] = all_results
        state.values["orchestrator_summary"] = {
            "total_plans": len(plans),
            "total_patches": len(all_patches),
            "total_results": len(all_results),
            "debug_rounds": total_debug_rounds,
        }

        return AgentResult(
            notes=[f"orchestrator: {len(plans)} plans, {len(all_results)} results, {total_debug_rounds} debug rounds"],
            artifacts={
                "code_patches": [p.get("patch_id", "") for p in all_patches if p.get("patch_id")],
                "experiment_results": [r.get("result_id", "") for r in all_results if r.get("result_id")],
                "auto_debug_records": all_debug_ids,
            },
            values={
                "experiment_results": all_results,
                "all_code_patches": all_patches,
                "all_experiment_results": all_results,
                "orchestrator_summary": state.values["orchestrator_summary"],
            },
        )
