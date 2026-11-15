from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.review_result import ReviewResult


class ReviewerAgent(Agent):
    name = "reviewer_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        findings: list[str] = []
        required_actions: list[str] = []
        residual_risk: list[str] = []

        self._check_evidence(state, findings, required_actions, residual_risk)
        self._check_llm_budget(state, context, findings, required_actions)
        self._check_experiment_plans(state, findings, required_actions, residual_risk)
        self._check_developer_mode(state, findings, required_actions)
        self._check_literature(state, findings, required_actions, residual_risk)
        self._check_experiment_results(state, findings, required_actions, residual_risk)
        self._check_experiment_decision(state, findings, required_actions, residual_risk)
        self._check_experiment_tree(state, context, findings, required_actions, residual_risk)
        self._report_tree(state, context, findings)

        status = "needs_human_review" if required_actions else "pass"
        review = ReviewResult(
            status=status,
            findings=findings,
            required_actions=required_actions,
            residual_risk=residual_risk,
        )
        context.artifact_store.save_json(state.run_id, "reviews", review.review_id, review)
        state.values["review_status"] = status
        state.values["review"] = asdict(review)
        return AgentResult(
            notes=[f"review completed with status={status}"],
            artifacts={"reviews": [review.review_id]},
            values={"review_status": status},
        )

    # ---- existing checks ----

    def _check_evidence(self, state: ResearchState, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        if state.values.get("unsupported_evidence_count", 0):
            findings.append("Some evidence records were unsupported.")
            required_actions.append("Re-run with full text parsing or remove unsupported claims.")
        if state.values.get("synthesis_evidence_warnings"):
            findings.append("Synthesis report contains evidence warnings.")
            residual_risk.extend(str(item) for item in state.values.get("synthesis_evidence_warnings", []))
        if state.values.get("selected_paper_count", 0) and not state.values.get("selected_context_count", 0):
            residual_risk.append("No selected paper contexts were saved for traceable LLM prompts.")

    def _check_llm_budget(self, state: ResearchState, context: AgentContext, findings: list[str], required_actions: list[str]) -> None:
        call_budget = context.settings.get("llm_call_budget")
        token_budget = context.settings.get("llm_token_budget")
        calls_used = int(state.values.get("llm_calls_used", 0))
        tokens_used = int(state.values.get("llm_tokens_used", 0))
        if isinstance(call_budget, int) and call_budget >= 0 and calls_used > call_budget:
            findings.append("LLM call usage exceeded the configured budget.")
            required_actions.append("Inspect llm_calls artifacts before any larger run.")
        if isinstance(token_budget, int) and token_budget >= 0 and tokens_used > token_budget:
            findings.append("LLM token usage exceeded the configured budget.")
            required_actions.append("Lower max papers or tighten chunk selection before rerunning.")

    def _check_experiment_plans(self, state: ResearchState, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        for plan in state.values.get("experiment_plans", []):
            if not plan.get("files_to_change"):
                findings.append("Experiment plan does not name concrete files to change.")
                required_actions.append("Regenerate the experiment plan with codebase context.")
            if not plan.get("rollback_plan"):
                findings.append("Experiment plan is missing a rollback plan.")
                required_actions.append("Add rollback instructions before code development.")
            training_config = plan.get("training_config", {})
            if isinstance(training_config, dict) and not any(
                "smoke" in str(value).lower() or "command" in str(key).lower()
                for key, value in training_config.items()
            ):
                residual_risk.append("Experiment plan lacks an explicit smoke-test command.")

    def _check_developer_mode(self, state: ResearchState, findings: list[str], required_actions: list[str]) -> None:
        if state.values.get("developer_mode") == "plan_only":
            findings.append("Developer agent produced a scoped plan only; no external code was edited.")
            required_actions.append("Confirm target repository and allowed paths before implementation.")
        elif state.values.get("developer_mode") == "explore_enabled":
            findings.append("Developer agent is allowed to explore the copied project, but this workflow run only created a task.")

    def _check_literature(self, state: ResearchState, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        if state.values.get("paper_count", 0) and all(
            paper.get("source") == "offline_seed" for paper in state.values.get("papers", [])
        ):
            residual_risk.append("Literature results are offline seeds, not real paper retrieval.")
            required_actions.append("Enable online arXiv or Semantic Scholar retrieval for real evidence.")

    # ---- new experiment-aware checks ----

    def _check_experiment_results(self, state: ResearchState, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        results = state.values.get("experiment_results") or []
        if not results:
            return

        errors = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
        failures = [r for r in results if isinstance(r, dict) and r.get("status") == "failed"]
        unparsed = [r for r in results if isinstance(r, dict) and r.get("status") == "unparsed"]

        if errors:
            findings.append(f"{len(errors)} experiment result(s) had execution errors.")
            required_actions.append("Check experiment error messages and fix environment before retry.")

        if failures:
            findings.append(f"{len(failures)} experiment result(s) detected failure signals.")
            required_actions.append("Review failed experiment log_tail and revert changes if needed.")

        if unparsed:
            residual_risk.append(f"{len(unparsed)} experiment result(s) could not be parsed; manual review needed.")

        expected_metrics = set(m.lower() for m in state.topic.experiment_metrics)
        if expected_metrics:
            for r in results:
                if not isinstance(r, dict):
                    continue
                metrics = r.get("metrics", {})
                if metrics and not expected_metrics.intersection(str(k).lower() for k in metrics):
                    residual_risk.append(
                        f"Result {r.get('result_id', '?')} metrics {list(metrics.keys())} "
                        f"do not overlap with expected {list(expected_metrics)}"
                    )

            for r in results:
                if not isinstance(r, dict):
                    continue
                if r.get("status") == "passed" and not r.get("metrics"):
                    residual_risk.append(
                        f"Result {r.get('result_id', '?')} status=passed but has no metrics."
                    )

        durations = [r.get("duration_seconds", 0) for r in results if isinstance(r, dict)]
        if durations:
            total = sum(d for d in durations if isinstance(d, (int, float)))
            if total > 600:
                residual_risk.append(f"Total experiment duration {total:.0f}s exceeded 10 minutes.")

    def _check_experiment_decision(self, state: ResearchState, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        decision = state.values.get("experiment_decision")
        if not decision:
            return

        action = decision.get("action", "unknown")
        if action == "rollback":
            plans = state.values.get("experiment_plans", [{}])
            rollback = plans[0].get("rollback_plan", "") if plans else ""
            if not rollback:
                findings.append("Experiment decision is rollback but plan has no rollback_plan.")
                required_actions.append("Define a rollback plan before re-running the experiment.")
            else:
                findings.append(f"Experiment decision: rollback. Rollback plan: {rollback[:200]}")

        if action == "continue":
            findings.append("Experiment decision: continue. Verify metrics against baseline before full training.")

        if action == "investigate":
            required_actions.append("Experiment decision requires investigation. Review error messages and log_tail.")

        if action == "hold":
            residual_risk.append("Experiment decision is hold; the loop may be incomplete.")

    # ---- experiment tree checks (P9d) ----

    def _check_experiment_tree(self, state: ResearchState, context: AgentContext, findings: list[str], required_actions: list[str], residual_risk: list[str]) -> None:
        tree = state.values.get("experiment_tree")
        if not isinstance(tree, dict) or not tree.get("nodes"):
            return

        nodes = tree.get("nodes", []) or []
        max_depth = tree.get("max_depth", 2)
        max_active = tree.get("max_active_nodes", 3)

        # Check: selected node without result
        for n in nodes:
            if n.get("status") == "selected" and not n.get("result"):
                findings.append(
                    f"Experiment tree node {n.get('node_id', '?')} is selected but has no result."
                )
                required_actions.append(
                    "Re-run with --enable-experiments or manually clear the selected status."
                )

        # Check: branch plan artifact must exist on disk when node is selected
        selected = state.values.get("selected_branch_node")
        if isinstance(selected, dict) and selected.get("node_id"):
            branch_artifacts = context.artifact_store.list_artifacts(
                state.run_id, "branch_experiment_plans"
            )
            if not branch_artifacts:
                findings.append(
                    f"Selected branch node {selected['node_id']} has no "
                    "branch_experiment_plans artifact on disk."
                )
                required_actions.append(
                    "Ensure BranchToPlanAgent runs after BranchSelectionAgent."
                )

        # Check: result on root but not on selected node
        root_id = tree.get("root_id", "")
        selected_id = selected.get("node_id", "") if isinstance(selected, dict) else ""
        if selected_id and selected_id != root_id:
            selected_node = next((n for n in nodes if n.get("node_id") == selected_id), None)
            root_node = next((n for n in nodes if n.get("node_id") == root_id), None)
            experiment_results = state.values.get("experiment_results", []) or []
            if experiment_results and root_node and root_node.get("result") and selected_node and not selected_node.get("result"):
                residual_risk.append(
                    f"Experiment results may have been written to root {root_id} "
                    f"instead of selected node {selected_id}."
                )

        # Check: pending branches exceed max_active_nodes
        pending = [n for n in nodes if n.get("status") == "pending" and n.get("depth", 0) < max_depth]
        if len(pending) > max_active:
            findings.append(
                f"Experiment tree has {len(pending)} pending branches, exceeding max {max_active}."
            )
            required_actions.append("Prune or promote pending branches before next run.")

        # Check: node depth exceeds max_depth
        over_depth = [n for n in nodes if n.get("depth", 0) > max_depth]
        if over_depth:
            findings.append(
                f"Experiment tree has {len(over_depth)} node(s) exceeding max depth {max_depth}."
            )
            required_actions.append("Prune or collapse nodes beyond max depth.")

    def _report_tree(
        self, state: ResearchState, context: AgentContext, findings: list[str],
    ) -> None:
        """Append ASCII tree visualization and borderline promotable list."""
        tree = state.values.get("experiment_tree")
        if not isinstance(tree, dict) or not tree.get("nodes"):
            return

        from tools.tree_visualizer import render_ascii_tree
        ascii_tree = render_ascii_tree(tree)
        findings.append(f"Experiment tree:\n{ascii_tree}")

        # List borderline promotable (smoke_passed, partial metrics improvement)
        root_id = tree.get("root_id", "")
        promotable: list[str] = []
        for n in tree.get("nodes", []) or []:
            if n.get("node_id") == root_id:
                continue
            if n.get("status") != "smoke_passed":
                continue
            result = n.get("result", {}) or {}
            metrics = result.get("metrics", {})
            if not metrics:
                continue
            root = next(
                (rn for rn in tree["nodes"] if rn.get("node_id") == root_id), None
            )
            root_metrics = (root.get("result", {}) or {}).get("metrics", {}) if root else {}
            if not root_metrics:
                continue
            ade = metrics.get("ade") or metrics.get("ADE")
            fde = metrics.get("fde") or metrics.get("FDE")
            r_ade = root_metrics.get("ade") or root_metrics.get("ADE")
            r_fde = root_metrics.get("fde") or root_metrics.get("FDE")
            if ade is None or fde is None or r_ade is None or r_fde is None:
                continue
            ade_better = ade < r_ade
            fde_better = fde < r_fde
            # Borderline = only one is better
            if ade_better != fde_better:
                promotable.append(
                    f"  {n['node_id']}: ADE={ade} FDE={fde} "
                    f"(root: ADE={r_ade} FDE={r_fde})"
                )
        if promotable:
            findings.append(
                "Borderline promotable branches (use --promote to promote):\n"
                + "\n".join(promotable)
            )
