from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from schemas.topic_pack import TopicPack


@dataclass(slots=True)
class AgentLabConfig:
    path: Path
    command: list[str]
    research_topic: str


class AgentLaboratoryAdapter:
    """Generate Agent Laboratory configs without launching the long workflow."""

    def __init__(self, repo_path: Path | str = "external/AgentLaboratory"):
        self.repo_path = Path(repo_path)

    def is_available(self) -> bool:
        return (self.repo_path / "ai_lab_repo.py").exists()

    def write_config(
        self,
        topic: TopicPack,
        output_path: Path | str,
        llm_backend: str = "gpt-4o",
        api_key_placeholder: str = "OPENAI-API-KEY-HERE",
    ) -> AgentLabConfig:
        if not self.is_available():
            raise FileNotFoundError(f"Agent Laboratory is not available at {self.repo_path}")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        research_topic = self._research_topic(topic)
        task_notes = self._task_notes(topic)
        config = self._render_yaml(
            {
                "copilot-mode": True,
                "research-topic": research_topic,
                "api-key": api_key_placeholder,
                "llm-backend": llm_backend,
                "lit-review-backend": llm_backend,
                "language": "English",
                "num-papers-lit-review": 5,
                "num-papers-to-write": 1,
                "parallel-labs": False,
                "mlesolver-max-steps": 1,
                "papersolver-max-steps": 1,
                "lab-index": 1,
                "load-existing": False,
                "except-if-fail": False,
                "compile-latex": False,
                "task-notes": task_notes,
            }
        )
        output.write_text(config, encoding="utf-8")
        return AgentLabConfig(
            path=output,
            command=self.build_command(output),
            research_topic=research_topic,
        )

    def build_command(self, config_path: Path | str, python_executable: str = "python") -> list[str]:
        return [
            python_executable,
            str(self.repo_path / "ai_lab_repo.py"),
            "--yaml-location",
            str(config_path),
        ]

    def _research_topic(self, topic: TopicPack) -> str:
        goal = topic.research_goal.get("long") or topic.research_goal.get("short") or topic.topic_name
        baselines = topic.current_status.get("baseline_methods", [])
        priorities = topic.current_status.get("priority", [])
        repo_path = topic.codebase.get("repo_path", "")
        return (
            f"Research topic: {topic.topic_name}. Goal: {goal} "
            f"Baselines: {', '.join(str(item) for item in baselines)}. "
            f"Priorities: {'; '.join(str(item) for item in priorities)}. "
            f"Codebase copy: {repo_path}. Produce one concrete, reviewable experiment plan first."
        )

    def _task_notes(self, topic: TopicPack) -> dict[str, list[str]]:
        codebase = topic.codebase
        protected = ", ".join(topic.protected_files()) or "none configured"
        allowed = ", ".join(topic.allowed_auto_edit()) or "none configured"
        metrics = ", ".join(topic.experiment_metrics) or "topic-specific metrics"
        return {
            "plan-formulation": [
                "Propose only one experiment in this run.",
                "Prefer the smallest baseline-compatible modification before large architecture changes.",
                f"Primary metrics: {metrics}.",
                "Do not claim novelty without evidence from literature review.",
            ],
            "data-preparation": [
                f"Read the project notes first if present: {codebase.get('repo_path', '')}/work.md.",
                f"Allowed edit paths: {allowed}.",
                f"Protected paths: {protected}.",
                "Do not modify raw data, checkpoints, or baseline result archives.",
            ],
            "running-experiments": [
                "Use smoke/debug configs before full training.",
                "Do not launch long training unless the human explicitly approves.",
                "Write any new outputs into a clearly named experiment folder.",
            ],
            "results-interpretation": [
                "Compare against the same baseline split and config.",
                "Report failures and regressions directly.",
            ],
            "report-writing": [
                "Keep the report grounded in actual run logs and produced artifacts.",
                "Separate confirmed results from planned or inferred claims.",
            ],
        }

    def _render_yaml(self, value: object, indent: int = 0) -> str:
        spaces = " " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{spaces}{key}:")
                    lines.append(self._render_yaml(item, indent + 2))
                else:
                    lines.append(f"{spaces}{key}: {self._scalar(item)}")
            return "\n".join(lines) + "\n"
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{spaces}-")
                    lines.append(self._render_yaml(item, indent + 2))
                else:
                    lines.append(f"{spaces}- {self._scalar(item)}")
            return "\n".join(lines)
        return f"{spaces}{self._scalar(value)}"

    def _scalar(self, value: object) -> str:
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return "null"
        return json.dumps(str(value), ensure_ascii=False)
