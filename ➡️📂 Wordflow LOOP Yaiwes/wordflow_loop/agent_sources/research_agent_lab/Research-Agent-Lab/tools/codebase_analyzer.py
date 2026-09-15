from __future__ import annotations

from pathlib import Path
import re

from schemas.codebase_report import CodebaseReport, CodeFileSummary
from schemas.topic_pack import TopicPack


class CodebaseAnalyzer:
    def analyze(self, topic: TopicPack) -> CodebaseReport:
        repo_path = Path(str(topic.codebase.get("repo_path", ""))).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"configured repo_path does not exist: {repo_path}")

        files = self._select_files(repo_path, topic)
        summaries = [self._summarize_file(repo_path, path) for path in files]
        return CodebaseReport(
            repository_path=str(repo_path),
            files=summaries,
            project_notes=self._read_notes(repo_path),
            integration_points=self._integration_points(summaries),
            suggested_first_patch_files=self._suggest_patch_files(summaries),
            smoke_commands=self._smoke_commands(topic),
            risks=self._risks(topic, summaries),
        )

    def to_markdown(self, report: CodebaseReport) -> str:
        lines = [
            f"# Codebase Report: {Path(report.repository_path).name}",
            "",
            f"Repository: `{report.repository_path}`",
            "",
            "## Integration Points",
        ]
        lines.extend(f"- {item}" for item in report.integration_points)
        lines.extend(["", "## Suggested First Patch Files"])
        lines.extend(f"- `{item}`" for item in report.suggested_first_patch_files)
        lines.extend(["", "## Smoke Commands"])
        lines.extend(f"- `{item}`" for item in report.smoke_commands)
        lines.extend(["", "## File Summaries"])
        for summary in report.files:
            lines.append(f"### `{summary.path}`")
            if summary.role:
                lines.append(f"- Role: {summary.role}")
            if summary.classes:
                lines.append(f"- Classes: {', '.join(summary.classes)}")
            if summary.functions:
                lines.append(f"- Functions: {', '.join(summary.functions)}")
            if summary.config_keys:
                lines.append(f"- Config keys: {', '.join(summary.config_keys[:16])}")
            if summary.important_patterns:
                lines.append(f"- Patterns: {', '.join(summary.important_patterns)}")
            lines.append("")
        if report.risks:
            lines.extend(["## Risks"])
            lines.extend(f"- {item}" for item in report.risks)
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _select_files(self, repo_path: Path, topic: TopicPack) -> list[Path]:
        priority = [
            "work.md",
            "README.md",
            "main_led_nba.py",
            "trainer/train_led_trajectory_augment_input.py",
            "models/model_led_initializer.py",
            "models/model_diffusion.py",
            "models/layers.py",
            "data/dataloader_virat.py",
            "cfg/virat/led_virat_debug.yml",
            "cfg/virat/led_virat.yml",
            "cfg/virat/led_virat_intent_debug.yml",
            "cfg/virat/led_virat_intent.yml",
            "utils/config.py",
            "utils/utils.py",
        ]
        selected: list[Path] = []
        for rel in priority:
            path = repo_path / rel
            if path.exists() and path.is_file():
                selected.append(path)
        if not selected:
            for pattern in topic.allowed_auto_edit():
                selected.extend(repo_path.glob(pattern))
        return sorted(set(selected))

    def _summarize_file(self, repo_path: Path, path: Path) -> CodeFileSummary:
        rel = path.relative_to(repo_path).as_posix()
        text = self._read_text(path)
        return CodeFileSummary(
            path=rel,
            role=self._role(rel),
            imports=self._matches(r"^\s*(?:from\s+\S+\s+import\s+.+|import\s+.+)$", text),
            classes=self._matches(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", text),
            functions=self._matches(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", text),
            config_keys=self._config_keys(text) if rel.endswith((".yml", ".yaml")) else [],
            important_patterns=self._important_patterns(text),
        )

    def _read_notes(self, repo_path: Path) -> str:
        notes = repo_path / "work.md"
        if not notes.exists():
            return ""
        return self._read_text(notes)[:4000]

    def _integration_points(self, summaries: list[CodeFileSummary]) -> list[str]:
        paths = {summary.path for summary in summaries}
        points: list[str] = []
        if "data/dataloader_virat.py" in paths:
            points.append("Add optional per-agent intention/language features in VIRATDataset output.")
        if "trainer/train_led_trajectory_augment_input.py" in paths:
            points.append("Fuse optional condition features in data_preprocess before initializer/denoiser calls.")
        if "models/model_led_initializer.py" in paths:
            points.append("Inject condition features into LEDInitializer mean/variance/scale branches.")
        if "models/model_diffusion.py" in paths:
            points.append("Extend TransformerDenoisingModel context conditioning after initializer smoke tests.")
        if any(path.startswith("cfg/virat/") for path in paths):
            points.append("Gate every experiment behind cfg/virat flags to keep baseline configs reproducible.")
        return points

    def _suggest_patch_files(self, summaries: list[CodeFileSummary]) -> list[str]:
        ordered = [
            "cfg/virat/led_virat_debug.yml",
            "cfg/virat/led_virat.yml",
            "data/dataloader_virat.py",
            "trainer/train_led_trajectory_augment_input.py",
            "models/model_led_initializer.py",
            "work.md",
        ]
        paths = {summary.path for summary in summaries}
        return [path for path in ordered if path in paths]

    def _smoke_commands(self, topic: TopicPack) -> list[str]:
        repo = topic.codebase.get("repo_path", "")
        info = topic.codebase.get("experiment_tag", "motion_condition")
        return [
            f"cd /d {repo} && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 1 --info {info}",
            f"cd /d {repo} && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 0 --info {info}",
        ]

    def _risks(self, topic: TopicPack, summaries: list[CodeFileSummary]) -> list[str]:
        risks = [
            "Project copy is not a git repository; use backups or copied files for rollback.",
            "VIRAT data is loaded from ../MID-main, so dataloader changes should not mutate source pkl files.",
        ]
        if any(summary.path == "models/model_diffusion.py" for summary in summaries):
            risks.append("Denoiser context dimensions are hard-coded around 256/512; condition fusion must preserve tensor shapes.")
        if topic.codebase.get("exploration_mode") == "high":
            risks.append("High exploration mode allows code edits after local report generation; keep smoke tests short.")
        return risks

    def _role(self, rel: str) -> str:
        if rel == "main_led_nba.py":
            return "CLI entry point for train/eval."
        if rel.startswith("trainer/"):
            return "Training, denoising, evaluation, and metric loop."
        if rel.startswith("models/model_led_initializer"):
            return "Leapfrog initializer for multi-sample future trajectory proposals."
        if rel.startswith("models/model_diffusion"):
            return "Transformer denoising model used by diffusion sampling."
        if rel.startswith("data/"):
            return "Dataset and batch collation."
        if rel.startswith("cfg/"):
            return "Experiment configuration."
        if rel == "work.md":
            return "Project log and current baseline record."
        return "Project file."

    def _important_patterns(self, text: str) -> list[str]:
        candidates = {
            "agent_mask": "agent masking",
            "pre_motion_3D": "history trajectory tensor",
            "fut_motion_3D": "future trajectory tensor",
            "LEDInitializer": "initializer",
            "TransformerDenoisingModel": "denoiser",
            "pretrained_initializer_model": "initializer checkpoint",
            "train_core_if_missing": "core fallback training",
            "debug": "debug-mode control",
        }
        return [label for needle, label in candidates.items() if needle in text]

    def _matches(self, pattern: str, text: str) -> list[str]:
        found = re.findall(pattern, text, flags=re.MULTILINE)
        return [item.strip() if isinstance(item, str) else item[0].strip() for item in found][:24]

    def _config_keys(self, text: str) -> list[str]:
        keys: list[str] = []
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.match(r"^\s*([A-Za-z0-9_/-]+)\s*:", line)
            if match:
                keys.append(match.group(1))
        return keys

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="gbk", errors="replace")
