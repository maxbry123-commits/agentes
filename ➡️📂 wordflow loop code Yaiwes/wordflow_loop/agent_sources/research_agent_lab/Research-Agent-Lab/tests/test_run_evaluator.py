from __future__ import annotations

import json
from unittest import TestCase, main

from schemas.run_evaluation import RunEvaluationCheck, RunEvaluationReport


class RunEvaluationSchemaTest(TestCase):
    def test_report_defaults(self):
        check = RunEvaluationCheck(
            name="llm_budget",
            status="pass",
            severity="info",
            message="budget ok",
        )
        report = RunEvaluationReport(
            status="pass",
            score=100,
            checks=[check],
            recommended_next_action="expand_budget_carefully",
        )

        self.assertTrue(report.evaluation_id.startswith("runeval_"))
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.score, 100)
        self.assertEqual(report.checks[0].name, "llm_budget")
        self.assertEqual(report.blocking_issues, [])
        self.assertEqual(report.warnings, [])


from pathlib import Path
from tempfile import TemporaryDirectory

from agents.run_evaluator import RunEvaluationAgent, _llm_call_checks
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="eval_test",
        experiment_metrics=["ADE", "FDE"],
    )


def _context(tmp: str, settings: dict | None = None) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings=settings or {},
    )


class RunEvaluationAgentTest(TestCase):
    def test_passes_clean_offline_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 2,
                "method_card_count": 2,
                "unsupported_evidence_count": 0,
                "review_status": "pass",
                "llm_calls_used": 0,
                "llm_tokens_used": 0,
            })

            result = RunEvaluationAgent().run(state, _context(tmp))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "pass")
            self.assertGreaterEqual(report["score"], 85)
            self.assertEqual(state.values["run_evaluation_status"], "pass")
            self.assertIn("run_evaluations", result.artifacts)

    def test_blocks_budget_overrun(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "llm_calls_used": 5,
                "llm_tokens_used": 100,
            })
            ctx = _context(tmp, {"llm_call_budget": 3, "llm_token_budget": 20000})

            RunEvaluationAgent().run(state, ctx)

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("LLM call budget" in item for item in report["blocking_issues"]))

    def test_blocks_selected_tree_node_without_result(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["n1"], "result": {}},
                        {"node_id": "n1", "status": "selected", "depth": 1, "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_tree_search": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("selected" in item.lower() for item in report["blocking_issues"]))

    def test_experiment_results_absent_is_pass_when_experiments_disabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_results": [],
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_experiments": False}))

            checks = state.values["run_evaluation"]["checks"]
            exp_check = next(c for c in checks if c["name"] == "experiment_results")
            self.assertEqual(exp_check["status"], "pass")
            self.assertEqual(exp_check["severity"], "info")

    def test_experiment_results_absent_blocks_when_experiments_enabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_results": [],
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_experiments": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no experiment results" in item for item in report["blocking_issues"]))

    def test_warns_on_inconsistent_tree_links(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["child"], "result": {}},
                        {"node_id": "child", "status": "pending", "depth": 1, "parent_id": "other", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("parent/child" in w or "root->child" in w for w in report["warnings"]))

    def test_selected_node_with_valid_result_not_blocked(self):
        """Bug 2 fix: result={status: passed} should not trigger selected_without_result."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["n1"], "result": {}},
                        {"node_id": "n1", "status": "selected", "depth": 1, "parent_id": "root", "children_ids": [],
                         "result": {"status": "passed", "metrics": {"ade": 0.1}}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "pass")
            self.assertNotIn("selected nodes without result",
                             " ".join(report.get("blocking_issues", [])))

    def test_warns_when_llm_enabled_without_budget(self):
        """Bug 3 fix: LLM enabled but no budget config -> warning check produced."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "llm_calls_used": 3,
                "llm_tokens_used": 5000,
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_llm": True}))

            checks = state.values["run_evaluation"]["checks"]
            call_check = next(c for c in checks if c["name"] == "llm_call_budget")
            self.assertEqual(call_check["status"], "warn")
            self.assertIn("no call budget", call_check["message"])
            token_check = next(c for c in checks if c["name"] == "llm_token_budget")
            self.assertEqual(token_check["status"], "warn")
            self.assertIn("no token budget", token_check["message"])

    # ── P11.1 regression: LLM call quality checks ──

    def test_critical_agent_zero_success_blocks(self):
        """P11.1: experiment_planner with records but 0 success -> block."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_planner_llm_record_count": 1,
                "experiment_planner_llm_success_count": 0,
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_llm": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("experiment_planner" in item for item in report["blocking_issues"]))

    def test_non_critical_agent_zero_success_warns(self):
        """P11.1: paper_triage with records but 0 success -> warn (not block)."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "triage_llm_record_count": 1,
                "triage_llm_success_count": 0,
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_llm": True}))

            report = state.values["run_evaluation"]
            checks = report["checks"]
            triage_check = next(c for c in checks if c["name"] == "llm_triage_success")
            self.assertEqual(triage_check["status"], "warn")
            self.assertEqual(triage_check["severity"], "warning")

    def test_llm_invalid_json_artifact_detected(self):
        """P11.1: artifact with status=invalid_json -> warn check."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })
            ctx = _context(tmp)
            ctx.artifact_store.save_json(state.run_id, "llm_calls", "call_1", {
                "agent": "experiment_planner",
                "status": "invalid_json",
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "usage": {"total_tokens": 5000},
            })

            RunEvaluationAgent().run(state, ctx)

            checks = state.values["run_evaluation"]["checks"]
            invalid_check = next(c for c in checks if c["name"] == "llm_invalid_json")
            self.assertEqual(invalid_check["status"], "warn")
            self.assertIn("invalid_json", invalid_check["message"])

    def test_llm_call_quality_pass_when_no_records(self):
        """P11.1: no LLM records -> pass info check."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })

            RunEvaluationAgent().run(state, _context(tmp))

            checks = state.values["run_evaluation"]["checks"]
            quality_check = next(c for c in checks if c["name"] == "llm_call_quality")
            self.assertEqual(quality_check["status"], "pass")
            self.assertEqual(quality_check["severity"], "info")

    def test_llm_error_artifact_detected(self):
        """P11.1: artifact with status=error -> fail blocker."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })
            ctx = _context(tmp)
            ctx.artifact_store.save_json(state.run_id, "llm_calls", "call_err", {
                "agent": "method_card_extractor",
                "status": "error",
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "error": "HTTP 500",
                "usage": {},
            })

            RunEvaluationAgent().run(state, ctx)

            report = state.values["run_evaluation"]
            self.assertTrue(any("error" in item for item in report["blocking_issues"]))

    # ── P11.2 regression: reverse parent checks ──

    def test_tree_orphan_parent_id_detected(self):
        """P11.2: node with parent_id pointing to non-existent node -> fail."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": [], "result": {}},
                        {"node_id": "orphan", "status": "pending", "depth": 1, "parent_id": "missing", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            checks = state.values["run_evaluation"]["checks"]
            tree_check = next(c for c in checks if c["name"] == "tree_bidirectional_links")
            self.assertEqual(tree_check["status"], "fail")
            self.assertIn("parent not found", tree_check["message"])

    def test_tree_root_with_parent_id_flagged(self):
        """P11.2: root node has parent_id -> flagged as problem."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "parent_id": "ghost", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            checks = state.values["run_evaluation"]["checks"]
            tree_check = next(c for c in checks if c["name"] == "tree_bidirectional_links")
            self.assertEqual(tree_check["status"], "fail")
            self.assertIn("root", tree_check["message"])

    def test_tree_child_not_in_parent_children_ids(self):
        """P11.2: parent exists but doesn't list child in children_ids -> fail."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": ["other"], "result": {}},
                        {"node_id": "child", "status": "pending", "depth": 1, "parent_id": "root", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            checks = state.values["run_evaluation"]["checks"]
            tree_check = next(c for c in checks if c["name"] == "tree_bidirectional_links")
            self.assertEqual(tree_check["status"], "fail")
            self.assertIn("does not list", tree_check["message"])

    def test_tree_non_root_with_empty_parent_id_flagged(self):
        """P11.2 edge: non-root node with parent_id="" -> flagged as floating."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "experiment_tree": {
                    "root_id": "root",
                    "max_depth": 2,
                    "max_active_nodes": 3,
                    "nodes": [
                        {"node_id": "root", "status": "active", "depth": 0, "children_ids": [], "result": {}},
                        {"node_id": "floating", "status": "pending", "depth": 1, "parent_id": "", "children_ids": [], "result": {}},
                    ],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp))

            checks = state.values["run_evaluation"]["checks"]
            tree_check = next(c for c in checks if c["name"] == "tree_bidirectional_links")
            self.assertEqual(tree_check["status"], "fail")
            self.assertIn("no parent_id", tree_check["message"])

    def test_llm_skipped_budget_status_warns(self):
        """P11.1 edge: artifact with status=skipped_call_budget -> caught as non-ok."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })
            ctx = _context(tmp, {"enable_llm": True})
            ctx.artifact_store.save_json(state.run_id, "llm_calls", "call_skip", {
                "agent": "method_card_extractor",
                "status": "skipped_call_budget",
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "usage": {},
            })

            RunEvaluationAgent().run(state, ctx)

            checks = state.values["run_evaluation"]["checks"]
            skip_check = next(c for c in checks if c["name"] == "llm_skipped_call_budget")
            self.assertEqual(skip_check["status"], "warn")
            self.assertIn("skipped_call_budget", skip_check["message"])


class RunEvaluationRetrievalIntegrationTest(TestCase):
    def test_retrieval_block_status_blocks_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "block",
                    "score": 60,
                    "blocking_issues": ["no candidate papers found"],
                    "warnings": [],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("retrieval evaluation blocked" in item for item in report["blocking_issues"]))

    def test_retrieval_needs_review_warns_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "needs_review",
                    "score": 80,
                    "blocking_issues": [],
                    "warnings": ["low keyword coverage"],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            report = state.values["run_evaluation"]
            checks = report["checks"]
            retrieval_check = next(c for c in checks if c["name"] == "retrieval_evaluation")
            self.assertEqual(retrieval_check["status"], "warn")

    def test_missing_retrieval_report_warns_only_when_enabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            checks = state.values["run_evaluation"]["checks"]
            retrieval_check = next(c for c in checks if c["name"] == "retrieval_evaluation")
            self.assertEqual(retrieval_check["status"], "warn")

    def test_disabled_skips_even_when_report_exists(self):
        """Bug fix: when enable_retrieval_evaluation=False but report dict exists, silently skip."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "block",
                    "score": 50,
                    "blocking_issues": ["should not appear"],
                    "warnings": [],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": False}))

            checks = state.values["run_evaluation"]["checks"]
            retrieval_checks = [c for c in checks if c["name"] == "retrieval_evaluation"]
            self.assertEqual(len(retrieval_checks), 0,
                             f"Should produce no retrieval check when disabled, got {retrieval_checks}")

    def test_unknown_retrieval_status_not_treated_as_pass(self):
        """Bug fix: unknown retrieval status must not be silently treated as pass."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "error",
                    "score": 0,
                    "blocking_issues": [],
                    "warnings": [],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            checks = state.values["run_evaluation"]["checks"]
            retrieval_check = next(c for c in checks if c["name"] == "retrieval_evaluation")
            self.assertEqual(retrieval_check["status"], "warn",
                             f"unknown retrieval status 'error' should be warn, got {retrieval_check['status']}")
            self.assertIn("unknown status", retrieval_check["message"])

    def test_corrupted_retrieval_score_does_not_crash(self):
        """Bug fix: non-numeric retrieval score should not crash RunEvaluationAgent."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "pass",
                    "score": "bad",
                    "blocking_issues": [],
                    "warnings": [],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            report = state.values["run_evaluation"]
            self.assertIn("run_evaluation", state.values,
                          "agent should not crash on corrupted score")
            # Corrupted score defaults to 0
            retrieval_check = next(
                c for c in report["checks"] if c["name"] == "retrieval_evaluation"
            )
            self.assertEqual(retrieval_check["evidence"]["retrieval_score"], 0)


if __name__ == "__main__":
    main()
