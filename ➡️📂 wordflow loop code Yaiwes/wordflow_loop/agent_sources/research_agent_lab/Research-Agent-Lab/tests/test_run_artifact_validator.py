from __future__ import annotations

from dataclasses import asdict
from unittest import TestCase, main

from schemas.run_validation import RunValidationCheck, RunValidationReport

from core.agent_base import Agent, AgentContext, AgentResult
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from core.workflow import Workflow
from core.run_logger import RunLogger
from schemas.topic_pack import TopicPack
from agents.run_validation_agent import RunValidationAgent


class RunValidationSchemaTest(TestCase):
    def test_check_defaults_are_jsonable(self):
        check = RunValidationCheck(
            name="state_exists",
            status="pass",
            severity="info",
            message="state.json exists",
            evidence={"path": "state.json"},
        )
        payload = asdict(check)
        self.assertEqual(payload["name"], "state_exists")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["severity"], "info")
        self.assertEqual(payload["evidence"]["path"], "state.json")

    def test_report_defaults_are_jsonable(self):
        report = RunValidationReport(
            run_id="run_1",
            run_dir="data/runs/run_1",
            status="pass",
            score=100,
            checks=[],
            blocking_issues=[],
            warnings=[],
            summary=["status=pass"],
        )
        payload = asdict(report)
        self.assertTrue(payload["validation_id"].startswith("runval_"))
        self.assertEqual(payload["run_id"], "run_1")
        self.assertEqual(payload["score"], 100)


import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.run_artifact_validator import validate_run_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class RunArtifactValidatorTest(TestCase):
    def test_valid_minimal_run_passes(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"enable_experiments": False},
                "artifacts": {"reviews": ["review_1"], "run_evaluations": ["eval_1"]},
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})
            (run_dir / "artifact_index.jsonl").write_text(
                json.dumps({"kind": "reviews", "artifact_id": "review_1", "path": str(run_dir / "artifacts" / "reviews" / "review_1.json")}) + "\n",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "pass")
            self.assertEqual(report.blocking_issues, [])

    def test_missing_state_blocks(self):
        with TemporaryDirectory() as tmp:
            report = validate_run_dir(Path(tmp) / "missing_run", expect_completed=True)
            self.assertEqual(report.status, "block")
            self.assertTrue(any("state.json" in issue for issue in report.blocking_issues))

    def test_missing_indexed_file_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            missing = run_dir / "artifacts" / "reports" / "missing.md"
            (run_dir / "artifact_index.jsonl").parent.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact_index.jsonl").write_text(
                json.dumps({"kind": "reports", "artifact_id": "missing", "path": str(missing)}) + "\n",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("indexed artifact path is missing" in issue for issue in report.blocking_issues))

    def test_state_artifact_without_file_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {"reviews": ["review_missing"]},
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("state artifact file is missing" in issue for issue in report.blocking_issues))

    def test_llm_disabled_missing_llm_calls_is_info(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"workflow_settings": {"enable_llm": False}},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)
            check = next(c for c in report.checks if c.name == "llm_calls_presence")

            self.assertEqual(check.status, "pass")
            self.assertEqual(check.severity, "info")

    def test_llm_enabled_missing_llm_calls_warns(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"workflow_settings": {"enable_llm": True}},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)
            check = next(c for c in report.checks if c.name == "llm_calls_presence")

            self.assertEqual(check.status, "warn")
            self.assertEqual(check.severity, "warning")

    def test_auto_debug_llm_call_link_missing_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            _write_json(run_dir / "artifacts" / "auto_debug_records" / "debug_1.json", {
                "record_id": "debug_1",
                "llm_call_id": "llm_call_missing",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("llm_call_id" in issue for issue in report.blocking_issues))

    def test_experiment_result_patch_link_missing_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"experiment_results": [{"status": "passed"}]},
                "artifacts": {},
            })
            _write_json(run_dir / "artifacts" / "experiment_results" / "result_1.json", {
                "result_id": "result_1",
                "experiment_id": "exp_1",
                "patch_id": "patch_missing",
                "status": "passed",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("patch_id" in issue for issue in report.blocking_issues))

    def test_code_patch_experiment_id_uses_state_plan_fallback(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"experiment_plans": [{"experiment_id": "exp_state"}]},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                    "code_patches": ["patch_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})
            _write_json(run_dir / "artifacts" / "code_patches" / "patch_1.json", {
                "patch_id": "patch_1",
                "experiment_id": "exp_state",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertNotIn("code_patch experiment_id has no plan: exp_state", report.blocking_issues)

    def test_experiment_decision_uses_state_plan_fallback(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {
                    "experiment_plans": [{"experiment_id": "exp_state"}],
                    "experiment_decisions": {"exp_state": {"experiment_id": "exp_state", "decision": "continue"}},
                },
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertNotIn("experiment_decision experiment_id has no result or plan: exp_state", report.blocking_issues)

    def test_secret_like_token_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            (run_dir / "artifacts" / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "artifacts" / "reports" / "bad.md").write_text(
                "leaked key sk-abcdefghijklmnop",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("secret-like" in issue for issue in report.blocking_issues))

    def test_invalid_state_json_blocks_without_crash(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text("{bad json", encoding="utf-8")

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("state.json cannot be read" in issue for issue in report.blocking_issues))

    def test_artifact_index_invalid_json_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            (run_dir / "artifact_index.jsonl").write_text("{bad json\n", encoding="utf-8")

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("artifact_index" in issue for issue in report.blocking_issues))


class NoopAgent(Agent):
    name = "noop_agent"

    def run(self, state, context):
        return AgentResult()


class WorkflowSettingsPersistenceTest(TestCase):
    def test_workflow_persists_public_settings_in_state(self):
        with TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp) / "runs")
            workflow = Workflow(
                name="test_workflow",
                agents=[NoopAgent()],
                artifact_store=store,
                memory_store=None,
                tool_registry=None,
                logger=RunLogger(),
                settings={
                    "enable_experiments": True,
                    "enable_llm": False,
                    "llm_call_budget": 0,
                    "llm_token_budget": 12000,
                    "llm_tokens_used": 0,
                    "deepseek_api_key": "sk-should-not-persist",
                    "session_token": "credential-should-not-persist",
                },
            )

            state = workflow.run(TopicPack(topic_name="test"))

            self.assertEqual(state.values["workflow_settings"]["enable_experiments"], True)
            self.assertEqual(state.values["workflow_settings"]["enable_llm"], False)
            self.assertEqual(state.values["workflow_settings"]["llm_call_budget"], 0)
            self.assertEqual(state.values["workflow_settings"]["llm_token_budget"], 12000)
            self.assertEqual(state.values["workflow_settings"]["llm_tokens_used"], 0)
            self.assertNotIn("deepseek_api_key", state.values["workflow_settings"])
            self.assertNotIn("session_token", state.values["workflow_settings"])


class RunValidationAgentTest(TestCase):
    def test_agent_writes_validation_artifact(self):
        with TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp) / "runs")
            state = ResearchState(topic=TopicPack(topic_name="test"))
            run_dir = store.run_dir(state.run_id)
            state.artifacts["reviews"] = ["review_1"]
            state.artifacts["run_evaluations"] = ["eval_1"]
            store.save_state(state.run_id, state.to_dict())
            store.save_json(state.run_id, "reviews", "review_1", {"review_id": "review_1"})
            store.save_json(state.run_id, "run_evaluations", "eval_1", {"evaluation_id": "eval_1"})
            context = AgentContext(
                artifact_store=store,
                memory_store=None,
                tool_registry=None,
                settings={},
            )

            result = RunValidationAgent().run(state, context)

            self.assertIn("run_validations", result.artifacts)
            self.assertIn("run_validation", state.values)
            self.assertTrue(store.list_artifacts(state.run_id, "run_validations"))


class ValidateRunCliParserTest(TestCase):
    def test_validate_run_parser(self):
        from app.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "validate-run",
            "--run-dir",
            "data/runs/run_1",
            "--json",
            "--strict",
        ])

        self.assertEqual(args.command, "validate-run")
        self.assertEqual(args.run_dir, "data/runs/run_1")
        self.assertTrue(args.json)
        self.assertTrue(args.strict)


if __name__ == "__main__":
    main()
