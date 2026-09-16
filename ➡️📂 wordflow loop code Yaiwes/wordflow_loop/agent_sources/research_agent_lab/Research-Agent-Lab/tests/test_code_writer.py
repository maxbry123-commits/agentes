from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.code_writer import CodeWriterAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _state() -> ResearchState:
    topic = TopicPack(topic_name="test", codebase={"repo_path": "/fake/repo", "allowed_auto_edit": ["model/"], "protected_files": ["model/secrets.py"]})
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change decoder", "files_to_change": ["model/decoder.py"]}]
    state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": ["model/secrets.py"]}]
    return state


class ProjectSafetyPolicyTest(TestCase):
    def test_normalize_preserves_directory_prefix(self):
        from tools.project_safety import ProjectSafetyPolicy
        policy = ProjectSafetyPolicy(repo_path="/tmp",
            allowed_paths=["model/"], protected_paths=["model/secrets.py"])
        self.assertTrue(policy.is_allowed("model/decoder.py"))
        self.assertTrue(policy.is_allowed("model/sub/foo.py"))
        self.assertFalse(policy.is_allowed("other/file.py"))
        self.assertTrue(policy.is_protected("model/secrets.py"))

    def test_normalize_exact_filename_still_works(self):
        from tools.project_safety import ProjectSafetyPolicy
        policy = ProjectSafetyPolicy(repo_path="/tmp",
            allowed_paths=["model/decoder.py"], protected_paths=[])
        self.assertTrue(policy.is_allowed("model/decoder.py"))
        self.assertFalse(policy.is_allowed("model/other.py"))


class CodeWriterAgentTest(TestCase):
    def test_skips_when_code_writes_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": False},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            self.assertIn("code_patches_by_experiment_id", state.values)
            patch = state.values["code_patches_by_experiment_id"].get("exp_1")
            self.assertEqual(patch["status"], "skipped")
            self.assertIn("code writes disabled", patch["reason"])

    def test_rejects_absolute_path(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(["/etc/passwd"], Path("/tmp/work"))
        self.assertFalse(ok)
        self.assertIn("absolute", reason.lower())

    def test_rejects_parent_traversal(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(["../outside.py"], Path("/tmp/work"))
        self.assertFalse(ok)
        self.assertIn("..", reason)

    def test_rejects_path_outside_work_dir(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(
            ["model/../../etc/hacked"], Path("/tmp/work/sub/proj"))
        self.assertFalse(ok)

    def test_rejects_protected_file_via_fnmatch(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(
            ["model/secrets.py"], Path("/tmp/work"),
            allowed_paths=["model/"], protected_paths=["model/secrets.py"],
        )
        self.assertFalse(ok)
        self.assertIn("protected", reason.lower())

    def test_accepts_valid_path_in_allowed_via_fnmatch(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(
            ["model/decoder.py"], Path("/tmp/work"),
            allowed_paths=["model/"], protected_paths=["model/secrets.py"],
        )
        self.assertTrue(ok)

    def test_accepts_valid_path_no_constraints(self):
        agent = CodeWriterAgent()
        ok, reason = agent._validate_paths(
            ["model/decoder.py"], Path("/tmp/work"))
        self.assertTrue(ok)

    def test_codetask_narrower_than_topic_blocks(self):
        """CodeTask allowed_paths can be narrower than topic-level — per-experiment restriction."""
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            (src_dir / "model" / "decoder.py").write_text("x = 1")
            (src_dir / "model" / "other.py").write_text("y = 2")
            topic = TopicPack(topic_name="test", codebase={
                "repo_path": str(src_dir), "copy_can_modify": True,
                "allowed_auto_edit": ["model/"],  # topic: broad
                "protected_files": [],
            })
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change", "files_to_change": ["model/other.py"],
            }]
            # CodeTask narrows to decoder.py only
            state.values["code_tasks"] = [{
                "task_id": "ct_1", "experiment_id": "exp_1",
                "allowed_paths": ["model/decoder.py"], "protected_paths": [],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "blocked",
                f"CodeTask narrowed to decoder.py, other.py should be blocked. Got: {patch.get('status')}")
            self.assertIn("not in allowed", patch.get("reason", ""))

    def test_glob_allowed_path_via_policy(self):
        """Glob patterns like models/* must work through ProjectSafetyPolicy."""
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "models").mkdir(parents=True)
            (src_dir / "models" / "a.py").write_text("x = 1")
            topic = TopicPack(topic_name="test", codebase={
                "repo_path": str(src_dir), "copy_can_modify": True,
                "allowed_auto_edit": ["models/*"],
                "protected_files": ["models/secrets.py"],
            })
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change", "files_to_change": ["models/a.py"],
            }]
            state.values["code_tasks"] = [{
                "task_id": "ct_1", "experiment_id": "exp_1",
                "allowed_paths": ["models/*"], "protected_paths": ["models/secrets.py"],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "applied",
                f"Glob should allow models/a.py, got: {patch.get('status')} reason={patch.get('reason')}")

    def test_copy_mode_creates_work_dir(self):
        import shutil
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir()
            (src_dir / "model" / "test.py").write_text("print('hello')")
            (src_dir / ".git").mkdir()

            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True, "enable_llm": False},
            )
            state.values["experiment_plans"] = [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change"}]
            state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/test.py"], "protected_paths": []}]

            agent = CodeWriterAgent()
            agent.run(state, context)

            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertIn("code_copies", patch["work_dir"])
            self.assertEqual(patch["mode"], "copy")
            self.assertTrue(Path(patch["work_dir"]).exists())
            self.assertTrue((Path(patch["work_dir"]) / "model" / "test.py").exists())
            self.assertFalse((Path(patch["work_dir"]) / ".git").exists(),
                             ".git should not be copied")

    def test_policy_blocks_protected_file(self):
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            (src_dir / "model" / "secrets.py").write_text("SECRET = 'xyz'")
            (src_dir / "model" / "decoder.py").write_text("x = 1")
            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            state.topic.codebase["copy_can_modify"] = True  # sandbox mode
            state.topic.codebase["protected_files"] = ["model/secrets.py"]
            state.topic.codebase["allowed_auto_edit"] = ["model/"]
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change secrets",
                "files_to_change": ["model/secrets.py"],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "blocked")
            self.assertIn("protected", patch["reason"])

    def test_policy_blocks_max_files(self):
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            for i in range(10):
                (src_dir / "model" / f"file_{i}.py").write_text(f"# file {i}")
            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            state.topic.codebase["copy_can_modify"] = True
            state.topic.codebase["max_files_per_patch"] = 3
            state.topic.codebase["allowed_auto_edit"] = ["model/"]
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change many files",
                "files_to_change": [f"model/file_{i}.py" for i in range(10)],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "blocked")
            self.assertIn("files", patch["reason"].lower())

    def test_code_task_match_by_experiment_id(self):
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            (src_dir / "model" / "decoder.py").write_text("x = 1")
            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            state.topic.codebase["copy_can_modify"] = True
            state.topic.codebase["allowed_auto_edit"] = ["model/"]
            # Two code_tasks, different experiment_ids
            state.values["code_tasks"] = [
                {"task_id": "ct_a", "experiment_id": "exp_other",
                 "allowed_paths": ["other/"], "protected_paths": []},
                {"task_id": "ct_b", "experiment_id": "exp_1",
                 "allowed_paths": ["model/"], "protected_paths": ["model/secrets.py"]},
            ]
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change decoder",
                "files_to_change": ["model/decoder.py"],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            # Should match ct_b, not ct_a
            self.assertEqual(patch["task_id"], "ct_b")

    def test_code_task_match_status_applied(self):
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            (src_dir / "model" / "decoder.py").write_text("x = 1")
            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            state.topic.codebase["copy_can_modify"] = True
            state.topic.codebase["allowed_auto_edit"] = ["model/"]
            state.topic.codebase["protected_files"] = ["model/secrets.py"]
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change decoder", "files_to_change": ["model/decoder.py"],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "applied",
                f"Expected status=applied, got status={patch.get('status')} reason={patch.get('reason')}")

    def test_code_task_missing_blocks(self):
        with TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            src_dir.mkdir()
            (src_dir / "model").mkdir(parents=True)
            (src_dir / "model" / "decoder.py").write_text("x = 1")
            state = _state()
            state.topic.codebase["repo_path"] = str(src_dir)
            state.topic.codebase["copy_can_modify"] = True
            state.topic.codebase["allowed_auto_edit"] = ["model/"]
            # No matching code_task for exp_1
            state.values["code_tasks"] = [
                {"task_id": "ct_other", "experiment_id": "exp_other",
                 "allowed_paths": ["other/"], "protected_paths": []},
            ]
            state.values["experiment_plans"] = [{
                "experiment_id": "exp_1", "hypothesis": "test",
                "modification": "change decoder",
                "files_to_change": ["model/decoder.py"],
            }]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": True},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            patch = state.values["code_patches_by_experiment_id"]["exp_1"]
            self.assertEqual(patch["status"], "blocked")
            self.assertIn("no CodeTask", patch["reason"])


if __name__ == "__main__":
    main()
