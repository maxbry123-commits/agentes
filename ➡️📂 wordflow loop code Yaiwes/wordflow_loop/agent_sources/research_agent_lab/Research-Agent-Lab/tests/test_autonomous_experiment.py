from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.autonomous_experiment import AutonomousExperimentAgent, _normalize_command, _rewrite_python
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(repo_path: str, smoke_commands: list[str]) -> ResearchState:
    topic = TopicPack(
        topic_name="test",
        codebase={
            "repo_path": repo_path,
            "copy_can_modify": True,
            "allowed_auto_edit": [],
            "protected_files": [],
        },
    )
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = [{"experiment_id": "experiment_test1"}]
    state.values["code_tasks"] = [{"task_id": "codetask_test1"}]
    state.values["codebase_report"] = {"smoke_commands": smoke_commands}
    return state


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={"enable_experiments": True},
    )


_PY_PRINT_ADE = 'python -c "print(\'ADE: 0.30 FDE: 0.60\')"'
_PY_PRINT_ADE2 = 'python -c "print(\'ADE: 0.10\')"'
_PY_PRINT_FDE = 'python -c "print(\'FDE: 0.20\')"'
_PY_PRINT_ADE3 = 'python -c "print(\'ADE: 0.42\')"'
_PY_PRINT_HELLO = 'python -c "print(\'hello\')"'
_PY_EXIT_1 = 'python -c "import sys; sys.exit(1)"'


class AutonomousExperimentAgentTest(TestCase):
    def test_skips_when_experiments_not_enabled(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fake_repo"
            repo.mkdir()
            state = _make_state(str(repo), [_PY_PRINT_HELLO])
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,  # type: ignore
                tool_registry=None,  # type: ignore
                settings={},
            )
            agent = AutonomousExperimentAgent()
            result = agent.run(state, context)
            self.assertIn("--enable-experiments", result.notes[0])
            self.assertEqual(state.values.get("experiment_results"), [])

    def test_skips_when_repo_missing(self):
        state = _make_state("/nonexistent/repo", [_PY_PRINT_HELLO])
        with TemporaryDirectory() as tmp:
            context = _make_context(tmp)
            agent = AutonomousExperimentAgent()
            result = agent.run(state, context)
            self.assertIn("skipped", result.notes[0])
            self.assertEqual(state.values.get("experiment_results"), [])

    def test_executes_and_parses_smoke_commands(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fake_repo"
            repo.mkdir()
            state = _make_state(str(repo), [_PY_PRINT_ADE])
            context = _make_context(tmp)

            agent = AutonomousExperimentAgent()
            agent.run(state, context)

            results = state.values["experiment_results"]
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "passed")
            self.assertAlmostEqual(results[0]["metrics"]["ade"], 0.30)
            self.assertAlmostEqual(results[0]["metrics"]["fde"], 0.60)

    def test_executes_and_detects_error(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fake_repo"
            repo.mkdir()
            state = _make_state(str(repo), [_PY_EXIT_1])
            context = _make_context(tmp)

            agent = AutonomousExperimentAgent()
            agent.run(state, context)

            results = state.values["experiment_results"]
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "error")

    def test_multiple_smoke_commands(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fake_repo"
            repo.mkdir()
            state = _make_state(str(repo), [_PY_PRINT_ADE2, _PY_PRINT_FDE])
            context = _make_context(tmp)

            agent = AutonomousExperimentAgent()
            agent.run(state, context)

            results = state.values["experiment_results"]
            self.assertEqual(len(results), 2)

    def test_artifact_persisted(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fake_repo"
            repo.mkdir()
            state = _make_state(str(repo), [_PY_PRINT_ADE3])
            context = _make_context(tmp)

            agent = AutonomousExperimentAgent()
            agent.run(state, context)

            files = context.artifact_store.list_artifacts(
                state.run_id, "experiment_results"
            )
            self.assertEqual(len(files), 1)
            self.assertTrue(str(files[0]).endswith(".json"))


class RewritePythonTest(TestCase):
    def test_rewrites_python_to_env_interpreter(self):
        result = _rewrite_python("python main_led_nba.py --cfg led_virat_debug")
        self.assertIn("video_llava", result)
        self.assertIn("main_led_nba.py", result)
        self.assertFalse(result.startswith("python "))

    def test_preserves_non_python_commands(self):
        result = _rewrite_python("some_tool --flag value")
        self.assertEqual(result, "some_tool --flag value")


class NormalizeCommandTest(TestCase):
    def test_extracts_cd_and_rewrites_python(self):
        cwd, cmd = _normalize_command(
            "cd /d D:/Codes/VS/Intent-LED-mul-agent && python main_led_nba.py --cfg led_virat_debug",
            "/default",
        )
        self.assertEqual(cwd, "D:/Codes/VS/Intent-LED-mul-agent")
        self.assertIn("video_llava", cmd)
        self.assertIn("main_led_nba.py", cmd)

    def test_no_cd_uses_default_repo(self):
        cwd, cmd = _normalize_command("python train.py", "/default/repo")
        self.assertEqual(cwd, "/default/repo")
        self.assertIn("video_llava", cmd)

    def test_preserves_non_python_after_cd(self):
        cwd, cmd = _normalize_command(
            "cd /d D:/repo && some_tool --flag",
            "/default",
        )
        self.assertEqual(cwd, "D:/repo")
        self.assertEqual(cmd, "some_tool --flag")

    def test_handles_plain_command(self):
        cwd, cmd = _normalize_command("some_tool test", "/default")
        self.assertEqual(cwd, "/default")
        self.assertEqual(cmd, "some_tool test")

    def test_real_codebase_analyzer_format(self):
        cmd = "cd /d D:/Codes/VS/Intent-LED-mul-agent && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 1 --info motion_condition"
        cwd, clean = _normalize_command(cmd, "/fallback")
        self.assertEqual(cwd, "D:/Codes/VS/Intent-LED-mul-agent")
        self.assertIn("video_llava", clean)
        self.assertIn("main_led_nba.py", clean)
        self.assertNotIn("cd", clean)
        self.assertNotIn("&&", clean)

    def test_real_eval_command_format(self):
        cmd = "cd /d D:/Codes/VS/Intent-LED-mul-agent && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 0 --info motion_condition"
        cwd, clean = _normalize_command(cmd, "/fallback")
        self.assertEqual(cwd, "D:/Codes/VS/Intent-LED-mul-agent")
        self.assertIn("video_llava", clean)
        self.assertIn("--train 0", clean)


class ResolveCommandsTest(TestCase):
    def test_uses_plan_commands_when_present(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", [])
        plan = {"commands": ["python -c \"print('plan_cmd')\""]}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("plan_cmd", result[0])

    def test_falls_back_to_smoke_when_plan_commands_empty(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", ["python -c \"print('smoke_cmd')\""])
        plan = {"commands": []}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("smoke_cmd", result[0])

    def test_falls_back_to_smoke_when_plan_commands_missing(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", ["python -c \"print('smoke_cmd')\""])
        plan = {}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("smoke_cmd", result[0])

    def test_noop_fallback_when_both_empty(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", [])
        plan = {}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("no smoke commands configured", result[0])


class ApplyBudgetTest(TestCase):
    def test_appends_max_epochs_when_missing(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 5})
        self.assertIn("--max_epochs 5", result[0])

    def test_replaces_max_epochs_when_present(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --max_epochs 100 --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 5})
        self.assertIn("--max_epochs 5", result[0])
        self.assertNotIn("100", result[0])

    def test_noop_when_budget_none(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": None})
        self.assertEqual(result, cmds)

    def test_noop_when_budget_missing(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {})
        self.assertEqual(result, cmds)

    def test_handles_multiple_commands(self):
        agent = AutonomousExperimentAgent()
        cmds = [
            "python train.py --train 1",
            "python train.py --max_epochs 50 --train 0",
        ]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 3})
        self.assertIn("--max_epochs 3", result[0])
        self.assertIn("--max_epochs 3", result[1])


class ExecuteAndParseBudgetTest(TestCase):
    def test_respects_budget_timeout_when_set(self):
        with TemporaryDirectory() as tmp:
            work = Path(tmp) / "repo"
            work.mkdir()
            agent = AutonomousExperimentAgent()
            state = _make_state(str(work), [])
            result = agent._execute_and_parse(
                experiment_id="test",
                command="python -c \"print('ADE: 0.3')\"",
                work_dir=str(work),
                state=state,
                success_criteria=None,
                settings={"train_budget_minutes": 5},
            )
            self.assertEqual(result.status, "passed")


if __name__ == "__main__":
    main()
