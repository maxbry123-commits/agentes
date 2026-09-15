from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import re
import shlex
import time
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from agents.result_parser import parse_experiment_output
from schemas.experiment_result import ExperimentResult
from tools.code_executor import ScopedCodeExecutor


_PYTHON_EXE = os.environ.get(
    "RESEARCH_AGENT_PYTHON",
    "D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe",
)

_SMOKE_TIMEOUT = int(os.environ.get("RESEARCH_AGENT_SMOKE_TIMEOUT", "600"))


class AutonomousExperimentAgent(Agent):
    name = "autonomous_experiment"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plans = state.values.get("experiment_plans", []) or []
        if not plans:
            state.values["experiment_results"] = []
            return AgentResult(
                notes=["skipped: no experiment plans"],
                values={"experiment_results": []},
            )

        codebase = state.topic.codebase
        repo_path = codebase.get("repo_path", "")

        if not context.settings.get("enable_experiments"):
            state.values["experiment_results"] = []
            return AgentResult(
                notes=["skipped: --enable-experiments not set"],
                values={"experiment_results": []},
            )

        if not repo_path or not Path(repo_path).exists():
            state.values["experiment_results"] = []
            return AgentResult(
                notes=[f"skipped: repo_path not found: {repo_path}"],
                values={"experiment_results": []},
            )

        all_results: list[dict[str, Any]] = []
        for plan in plans:
            if isinstance(plan, dict):
                results = self.run_single_plan(state, context, plan)
                all_results.extend(results)

        state.values["experiment_results"] = all_results
        summary = self._summarize(all_results)
        return AgentResult(
            notes=summary,
            artifacts={"experiment_results": [r["result_id"] for r in all_results]},
            values={"experiment_results": all_results},
        )

    def run_single_plan(self, state: ResearchState, context: AgentContext, plan: dict, patch_dict: dict | None = None, attempt: int = 0) -> list[dict]:
        experiment_id = plan.get("experiment_id", "unknown")
        codebase = state.topic.codebase
        repo_path = codebase.get("repo_path", "")

        work_dir = repo_path
        if patch_dict and patch_dict.get("work_dir"):
            work_dir = patch_dict["work_dir"]
        elif isinstance(state.values.get("code_patches_by_experiment_id"), dict):
            by_id = state.values["code_patches_by_experiment_id"]
            if experiment_id in by_id and by_id[experiment_id].get("work_dir"):
                work_dir = by_id[experiment_id]["work_dir"]

        if not context.settings.get("enable_experiments"):
            return []

        success_criteria = plan.get("success_criteria")

        commands = self._resolve_commands(state, plan)
        commands = self._apply_budget(commands, context.settings)
        results: list[dict] = []
        for cmd in commands:
            result = self._execute_and_parse(experiment_id, cmd, work_dir, state, success_criteria, context.settings)
            result.attempt = attempt
            result.patch_id = patch_dict.get("patch_id", "") if patch_dict else ""
            result.work_dir = work_dir
            context.artifact_store.save_json(state.run_id, "experiment_results", result.result_id, result)
            results.append(asdict(result))
            if result.status == "error":
                break
        return results

    def _resolve_commands(self, state: ResearchState, plan: dict) -> list[str]:
        plan_commands = plan.get("commands", []) or []
        if plan_commands:
            return [_rewrite_python(cmd) for cmd in plan_commands]

        report = state.values.get("codebase_report", {})
        commands = report.get("smoke_commands", [])
        if not commands:
            commands = ["python -c \"print('no smoke commands configured; nothing to run')\""]
        return [_rewrite_python(cmd) for cmd in commands]

    def _apply_budget(self, commands: list[str], settings: dict) -> list[str]:
        epochs = settings.get("train_budget_epochs")
        if not epochs:
            return commands
        result = []
        for cmd in commands:
            if "--max_epochs" in cmd:
                cmd = re.sub(r"--max_epochs\s+\d+", f"--max_epochs {epochs}", cmd)
            else:
                cmd += f" --max_epochs {epochs}"
            result.append(cmd)
        return result

    def _execute_and_parse(
        self,
        experiment_id: str,
        command: str,
        work_dir: str,
        state: ResearchState,
        success_criteria: dict | None = None,
        settings: dict | None = None,
    ) -> ExperimentResult:
        cwd, clean_command = _normalize_command(command, work_dir)
        executor = ScopedCodeExecutor(work_dir)
        cmd_parts = shlex.split(clean_command)
        start = time.monotonic()
        try:
            timeout = _SMOKE_TIMEOUT
            if settings and settings.get("train_budget_minutes"):
                timeout = min(_SMOKE_TIMEOUT, int(settings["train_budget_minutes"]) * 60)
            completed = executor.run(cmd_parts, cwd=cwd, timeout=timeout)
            duration = round(time.monotonic() - start, 2)
            return parse_experiment_output(
                experiment_id=experiment_id,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                command=command,
                expected_metrics=state.topic.experiment_metrics,
                duration_seconds=duration,
                success_criteria=success_criteria,
            )
        except Exception as exc:
            duration = round(time.monotonic() - start, 2)
            return ExperimentResult(
                experiment_id=experiment_id,
                status="error",
                error_message=str(exc)[:500],
                run_command=command,
                duration_seconds=duration,
            )

    def _summarize(self, results: list[dict[str, Any]]) -> list[str]:
        notes: list[str] = []
        for r in results:
            status = r.get("status", "unknown")
            metrics = r.get("metrics", {})
            metric_str = ", ".join(
                f"{k}={v}" for k, v in sorted(metrics.items())
            ) if metrics else "no metrics"
            notes.append(f"experiment {status}: {metric_str}")
        return notes


_CD_PATTERN = re.compile(r"^cd\s+(?:/d\s+)?(\S+)\s*&&\s*(.+)$", re.IGNORECASE)


def _normalize_command(command: str, default_repo: str) -> tuple[str, str]:
    """Extract cd prefix into cwd, returning (cwd, clean_command)."""
    m = _CD_PATTERN.match(command.strip())
    if m:
        cwd = m.group(1)
        clean = m.group(2)
        return cwd, _rewrite_python(clean)
    return default_repo, _rewrite_python(command)


def _rewrite_python(command: str) -> str:
    parts = command.split()
    if parts and parts[0] == "python":
        parts[0] = _PYTHON_EXE
    return " ".join(parts)
